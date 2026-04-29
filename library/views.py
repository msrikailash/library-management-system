from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Sum, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Book, Category, IssuedBook, Reservation, Notification, ActivityLog
from .forms import BookForm, CategoryForm, IssueBookForm, ReturnBookForm, BookSearchForm, ReservationForm
from accounts.models import CustomUser
from accounts.forms import StudentRegistrationForm
from decimal import Decimal
from datetime import timedelta
import json


def admin_required(view_func):
    """Decorator to restrict views to admin users only."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin_user():
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def dashboard_view(request):
    user = request.user
    if user.is_admin_user():
        # Admin dashboard stats
        total_books = Book.objects.count()
        total_users = CustomUser.objects.filter(role='student').count()
        issued_books = IssuedBook.objects.filter(status='issued').count()
        overdue_books = IssuedBook.objects.filter(
            status='issued', due_date__lt=timezone.now()
        ).count()
        total_fines = IssuedBook.objects.filter(
            status='returned', fine__gt=0
        ).aggregate(total=Sum('fine'))['total'] or Decimal('0.00')

        recent_issues = IssuedBook.objects.select_related('user', 'book').order_by('-issue_date')[:5]
        overdue_list = IssuedBook.objects.filter(
            status='issued', due_date__lt=timezone.now()
        ).select_related('user', 'book')[:5]
        recent_books = Book.objects.order_by('-created_at')[:4]

        context = {
            'total_books': total_books,
            'total_users': total_users,
            'issued_books': issued_books,
            'overdue_books': overdue_books,
            'total_fines': total_fines,
            'recent_issues': recent_issues,
            'overdue_list': overdue_list,
            'recent_books': recent_books,
            'is_admin': True,
        }
    else:
        # Student dashboard
        my_issues = IssuedBook.objects.filter(
            user=user, status='issued'
        ).select_related('book').order_by('due_date')
        my_history = IssuedBook.objects.filter(
            user=user, status='returned'
        ).select_related('book').order_by('-return_date')[:5]
        total_fines = IssuedBook.objects.filter(
            user=user, fine__gt=0
        ).aggregate(total=Sum('fine'))['total'] or Decimal('0.00')

        overdue_issues = [issue for issue in my_issues if issue.is_overdue()]

        context = {
            'my_issues': my_issues,
            'my_history': my_history,
            'total_fines': total_fines,
            'overdue_issues': overdue_issues,
            'is_admin': False,
        }

    return render(request, 'library/dashboard.html', context)


# ===================== BOOK VIEWS =====================

@login_required
def book_list_view(request):
    form = BookSearchForm(request.GET)
    books = Book.objects.select_related('category').all()

    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        availability = form.cleaned_data.get('availability')

        if query:
            books = books.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(isbn__icontains=query)
            )
        if category:
            books = books.filter(category=category)
        if availability == 'available':
            books = books.filter(available_quantity__gt=0)
        elif availability == 'unavailable':
            books = books.filter(available_quantity=0)

    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    context = {
        'page_obj': page_obj,
        'form': form,
        'categories': categories,
        'total_books': books.count(),
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('library/partials/book_grid.html', context, request=request)
        return JsonResponse({'html': html})
        
    return render(request, 'library/book_list.html', context)


@login_required
def book_detail_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    user_has_book = False
    if not request.user.is_admin_user():
        user_has_book = IssuedBook.objects.filter(
            user=request.user, book=book, status='issued'
        ).exists()
    recent_issues = IssuedBook.objects.filter(book=book).order_by('-issue_date')[:5]
    return render(request, 'library/book_detail.html', {
        'book': book,
        'user_has_book': user_has_book,
        'recent_issues': recent_issues,
    })


@admin_required
def book_add_view(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('book_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form, 'action': 'Add'})


@admin_required
def book_edit_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            
            # Optional: Add to activity log (only if it's a new book add, but this is edit)
            ActivityLog.objects.create(
                user=request.user,
                action='Updated Book',
                details=f'Updated details for "{book.title}"'
            )
            
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_detail', pk=book.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {'form': form, 'action': 'Edit', 'book': book})


@admin_required
def book_delete_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'Book "{title}" deleted successfully.')
        return redirect('book_list')
    return render(request, 'library/book_confirm_delete.html', {'book': book})


# ===================== ISSUE / RETURN VIEWS =====================

@admin_required
def issue_book_view(request):
    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.issued_by = request.user
            # Check availability
            book = issue.book
            if book.available_quantity <= 0:
                messages.error(request, f'"{book.title}" is not available for issue.')
                return render(request, 'library/issue_book.html', {'form': form})
            # Check if user already has this book
            if IssuedBook.objects.filter(user=issue.user, book=book, status='issued').exists():
                messages.error(request, f'This user already has "{book.title}" issued.')
                return render(request, 'library/issue_book.html', {'form': form})
            issue.status = 'issued'
            issue.save()
            # Decrease available quantity
            book.available_quantity -= 1
            book.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='Issued Book',
                details=f'Issued "{book.title}" to {issue.user.username}'
            )
            
            messages.success(request, f'"{book.title}" issued to {issue.user.get_full_name() or issue.user.username}!')
            return redirect('issued_books')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IssueBookForm()
    return render(request, 'library/issue_book.html', {'form': form})


@admin_required
def return_book_view(request, pk):
    issue = get_object_or_404(IssuedBook, pk=pk)
    if issue.status == 'returned':
        messages.info(request, 'This book has already been returned.')
        return redirect('issued_books')

    fine = issue.calculate_fine()
    if request.method == 'POST':
        form = ReturnBookForm(request.POST, instance=issue)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.return_date = timezone.now()
            issue.fine = fine
            issue.status = 'returned'
            issue.save()
            # Increase available quantity
            issue.book.available_quantity += 1
            issue.book.save()
            
            log_details = f'Returned "{issue.book.title}" from {issue.user.username}'
            if fine > 0:
                log_details += f' with fine ₹{fine}'
            ActivityLog.objects.create(
                user=request.user,
                action='Returned Book',
                details=log_details
            )
            
            msg = f'"{issue.book.title}" returned successfully.'
            if fine > 0:
                msg += f' Fine charged: ₹{fine}'
            messages.success(request, msg)
            return redirect('issued_books')
    else:
        form = ReturnBookForm(instance=issue)

    return render(request, 'library/return_book.html', {
        'issue': issue,
        'form': form,
        'fine': fine,
    })


@admin_required
def issued_books_view(request):
    status = request.GET.get('status', 'issued')
    issues = IssuedBook.objects.select_related('user', 'book').all()

    if status == 'issued':
        issues = issues.filter(status='issued')
    elif status == 'returned':
        issues = issues.filter(status='returned')
    elif status == 'overdue':
        issues = issues.filter(status='issued', due_date__lt=timezone.now())

    paginator = Paginator(issues, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    overdue_count = IssuedBook.objects.filter(status='issued', due_date__lt=timezone.now()).count()
    return render(request, 'library/issued_books.html', {
        'page_obj': page_obj,
        'status': status,
        'overdue_count': overdue_count,
    })


# ===================== STUDENT VIEWS =====================

@login_required
def my_books_view(request):
    my_issues = IssuedBook.objects.filter(
        user=request.user
    ).select_related('book').order_by('-issue_date')
    paginator = Paginator(my_issues, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'library/my_books.html', {'page_obj': page_obj})


@login_required
def renew_book_view(request, pk):
    issue = get_object_or_404(IssuedBook, pk=pk, user=request.user, status='issued')
    
    if issue.days_until_due() is not None and issue.days_until_due() < 0:
        messages.error(request, 'Cannot renew an overdue book. Please return it and pay the fine.')
    elif issue.renewal_count >= issue.max_renewals:
        messages.error(request, 'Maximum renewals reached for this book.')
    else:
        issue.due_date = issue.due_date + timedelta(days=7)
        issue.renewal_count += 1
        issue.save()
        messages.success(request, f'Successfully renewed "{issue.book.title}" for 7 days.')
        
    return redirect('my_books')


# ===================== CATEGORY VIEWS =====================

@admin_required
def category_list_view(request):
    categories = Category.objects.annotate(book_count=Count('books')).all()
    return render(request, 'library/category_list.html', {'categories': categories})


@admin_required
def category_add_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" added!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'library/category_form.html', {'form': form, 'action': 'Add'})


@admin_required
def category_edit_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category updated!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'library/category_form.html', {'form': form, 'action': 'Edit'})


@admin_required
def category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('category_list')
    return render(request, 'library/category_confirm_delete.html', {'category': category})


# ===================== USER MANAGEMENT =====================

@admin_required
def user_list_view(request):
    users = CustomUser.objects.filter(role='student').annotate(
        total_issued=Count('issued_books')
    ).order_by('username')
    return render(request, 'library/user_list.html', {'users': users})


@admin_required
def user_add_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            ActivityLog.objects.create(
                user=request.user,
                action='Registered Student',
                details=f'Registered student account for {user.username}'
            )
            messages.success(request, f'Student "{user.username}" added successfully!')
            return redirect('user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentRegistrationForm()
    return render(request, 'library/user_form.html', {'form': form})


@admin_required
def user_detail_view(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    issues = IssuedBook.objects.filter(user=user).select_related('book').order_by('-issue_date')
    total_fines = issues.aggregate(total=Sum('fine'))['total'] or Decimal('0.00')
    active_count = issues.filter(status='issued').count()
    returned_count = issues.filter(status='returned').count()
    overdue_count = issues.filter(status='issued', due_date__lt=timezone.now()).count()
    return render(request, 'library/user_detail.html', {
        'profile_user': user,
        'issues': issues,
        'total_fines': total_fines,
        'active_count': active_count,
        'returned_count': returned_count,
        'overdue_count': overdue_count,
    })


@admin_required
def user_delete_view(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted.')
        return redirect('user_list')
    return render(request, 'library/user_confirm_delete.html', {'profile_user': user})


# ===================== REPORTS =====================

@admin_required
def reports_view(request):
    """Comprehensive library reports and analytics."""
    # Summary stats
    total_books = Book.objects.count()
    total_copies = Book.objects.aggregate(total=Sum('quantity'))['total'] or 0
    total_available = Book.objects.aggregate(total=Sum('available_quantity'))['total'] or 0
    total_students = CustomUser.objects.filter(role='student').count()
    total_issued = IssuedBook.objects.filter(status='issued').count()
    total_returned = IssuedBook.objects.filter(status='returned').count()
    total_overdue = IssuedBook.objects.filter(status='issued', due_date__lt=timezone.now()).count()
    total_fines_collected = IssuedBook.objects.filter(
        status='returned', fine__gt=0
    ).aggregate(total=Sum('fine'))['total'] or Decimal('0.00')
    total_categories = Category.objects.count()

    # Books by category (for chart)
    categories_data = Category.objects.annotate(
        book_count=Count('books')
    ).values('name', 'book_count').order_by('-book_count')
    category_labels = json.dumps([c['name'] for c in categories_data])
    category_values = json.dumps([c['book_count'] for c in categories_data])

    # Most borrowed books (top 10)
    popular_books = Book.objects.annotate(
        borrow_count=Count('issued_records')
    ).order_by('-borrow_count')[:10]

    # Top borrowers (students with most issues)
    top_borrowers = CustomUser.objects.filter(role='student').annotate(
        borrow_count=Count('issued_books'),
        total_fine=Sum('issued_books__fine')
    ).order_by('-borrow_count')[:10]

    # Monthly issue trends (last 6 months)
    months_data = []
    for i in range(5, -1, -1):
        month_start = (timezone.now() - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = (timezone.now() - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            month_end = timezone.now()
        issued_count = IssuedBook.objects.filter(
            issue_date__gte=month_start, issue_date__lt=month_end
        ).count()
        returned_count_month = IssuedBook.objects.filter(
            return_date__gte=month_start, return_date__lt=month_end
        ).count()
        months_data.append({
            'label': month_start.strftime('%b %Y'),
            'issued': issued_count,
            'returned': returned_count_month,
        })
    month_labels = json.dumps([m['label'] for m in months_data])
    month_issued = json.dumps([m['issued'] for m in months_data])
    month_returned = json.dumps([m['returned'] for m in months_data])

    # Students with overdue books
    overdue_students = IssuedBook.objects.filter(
        status='issued', due_date__lt=timezone.now()
    ).select_related('user', 'book').order_by('due_date')[:10]

    context = {
        'total_books': total_books,
        'total_copies': total_copies,
        'total_available': total_available,
        'total_students': total_students,
        'total_issued': total_issued,
        'total_returned': total_returned,
        'total_overdue': total_overdue,
        'total_fines_collected': total_fines_collected,
        'total_categories': total_categories,
        'category_labels': category_labels,
        'category_values': category_values,
        'popular_books': popular_books,
        'top_borrowers': top_borrowers,
        'month_labels': month_labels,
        'month_issued': month_issued,
        'month_returned': month_returned,
        'overdue_students': overdue_students,
    }
    return render(request, 'library/reports.html', context)


# ===================== RESERVATION VIEWS =====================

@login_required
def reserve_book_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
        
    # Check if already reserved
    if Reservation.objects.filter(user=request.user, book=book, status='pending').exists():
        messages.warning(request, 'You already have a pending reservation for this book.')
        return redirect('book_detail', pk=book.pk)
        
    if request.method == 'POST':
        Reservation.objects.create(user=request.user, book=book)
        
        # Notify admins
        admins = CustomUser.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"{request.user.username} reserved {book.title}",
                notification_type='reservation',
                link=f"/reservations/manage/"
            )
            
        messages.success(request, f'You have successfully reserved "{book.title}". We will notify you when it becomes available.')
        return redirect('my_reservations')
        
    return render(request, 'library/reserve_book.html', {'book': book})

@login_required
def my_reservations_view(request):
    reservations = Reservation.objects.filter(user=request.user).select_related('book').order_by('-reserved_date')
    paginator = Paginator(reservations, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'library/my_reservations.html', {'page_obj': page_obj})

@login_required
def cancel_reservation_view(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    if request.method == 'POST':
        reservation.status = 'cancelled'
        reservation.save()
        messages.success(request, 'Reservation cancelled successfully.')
    return redirect('my_reservations')

@admin_required
def manage_reservations_view(request):
    status_filter = request.GET.get('status', 'pending')
    reservations = Reservation.objects.select_related('user', 'book').order_by('reserved_date')
    
    if status_filter in ['pending', 'fulfilled', 'cancelled']:
        reservations = reservations.filter(status=status_filter)
        
    paginator = Paginator(reservations, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    if request.method == 'POST':
        res_id = request.POST.get('reservation_id')
        new_status = request.POST.get('status')
        reservation = get_object_or_404(Reservation, pk=res_id)
        
        if new_status in ['pending', 'fulfilled', 'cancelled']:
            # If fulfilling, check availability and issue the book
            if new_status == 'fulfilled':
                book = reservation.book
                
                # Check if the book is available
                if book.available_quantity <= 0:
                    messages.error(request, f'Cannot fulfill: "{book.title}" has no available copies.')
                    return redirect(f"{request.path}?status={status_filter}")
                
                # Check if user already has this book issued
                if IssuedBook.objects.filter(user=reservation.user, book=book, status='issued').exists():
                    messages.error(request, f'Cannot fulfill: {reservation.user.username} already has "{book.title}" issued.')
                    return redirect(f"{request.path}?status={status_filter}")
                
                # Create the issued book record
                issued = IssuedBook.objects.create(
                    user=reservation.user,
                    book=book,
                    issued_by=request.user,
                    status='issued',
                    due_date=timezone.now() + timedelta(days=14),
                    notes=f'Auto-issued from reservation #{reservation.pk}'
                )
                
                # Decrease available quantity
                book.available_quantity -= 1
                book.save()
                
                # Log the activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='Fulfilled Reservation',
                    details=f'Issued "{book.title}" to {reservation.user.username} (reservation #{reservation.pk})'
                )
                
                # Notify the student
                Notification.objects.create(
                    user=reservation.user,
                    message=f'Your reservation for "{book.title}" has been fulfilled! The book is now issued to you.',
                    notification_type='success',
                    link=f"/my-books/"
                )
            
            reservation.status = new_status
            reservation.save()
                
            messages.success(request, f'Reservation status updated to {new_status}.')
        return redirect(f"{request.path}?status={status_filter}")
        
    return render(request, 'library/manage_reservations.html', {
        'page_obj': page_obj,
        'status': status_filter
    })


# ===================== NOTIFICATION VIEWS =====================

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all viewed on this page as read
    unread = notifications.filter(is_read=False)
    if unread.exists():
        unread.update(is_read=True)
        
    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'library/notifications.html', {'page_obj': page_obj})

@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

# ===================== ACTIVITY LOG VIEW =====================

@admin_required
def activity_log_view(request):
    logs = ActivityLog.objects.select_related('user').order_by('-timestamp')
    paginator = Paginator(logs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'library/activity_log.html', {'page_obj': page_obj})

# ===================== CSV EXPORT VIEWS =====================
import csv
from django.http import HttpResponse

@admin_required
def export_books_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Author', 'ISBN', 'Category', 'Quantity', 'Available'])

    books = Book.objects.all().values_list('title', 'author', 'isbn', 'category__name', 'quantity', 'available_quantity')
    for book in books:
        writer.writerow(book)

    return response

@admin_required
def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'

    writer = csv.writer(response)
    writer.writerow(['Username', 'First Name', 'Last Name', 'Email', 'Total Issued'])

    users = CustomUser.objects.filter(role='student').annotate(
        total_issued=Count('issued_books')
    )
    for u in users:
        writer.writerow([u.username, u.first_name, u.last_name, u.email, u.total_issued])

    return response

@admin_required
def export_issued_books_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="issued_books.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Book', 'Issue Date', 'Due Date', 'Return Date', 'Status', 'Fine'])

    issues = IssuedBook.objects.select_related('user', 'book').all()
    for i in issues:
        writer.writerow([
            i.user.username,
            i.book.title,
            i.issue_date.strftime('%Y-%m-%d') if i.issue_date else '',
            i.due_date.strftime('%Y-%m-%d') if i.due_date else '',
            i.return_date.strftime('%Y-%m-%d') if i.return_date else '',
            i.status,
            i.fine
        ])

    return response


