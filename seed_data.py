"""
Seed Data Script for LibraryMS
Run: python manage.py shell < seed_data.py

Creates categories, books, users, and issued book records for demo purposes.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from accounts.models import CustomUser
from library.models import Category, Book, IssuedBook

print("=" * 60)
print("  LibraryMS — Seeding Database")
print("=" * 60)

# ============================================================
# 1. CREATE CATEGORIES
# ============================================================
categories_data = [
    {"name": "Fiction", "description": "Novels, short stories, and literary fiction"},
    {"name": "Science", "description": "Physics, chemistry, biology, and earth sciences"},
    {"name": "Technology", "description": "Computer science, programming, and engineering"},
    {"name": "Mathematics", "description": "Algebra, calculus, statistics, and discrete math"},
    {"name": "History", "description": "World history, civilizations, and historical events"},
    {"name": "Philosophy", "description": "Ethics, logic, metaphysics, and existentialism"},
    {"name": "Business", "description": "Management, economics, finance, and entrepreneurship"},
    {"name": "Self-Help", "description": "Personal development, motivation, and productivity"},
]

categories = {}
for cat_data in categories_data:
    cat, created = Category.objects.get_or_create(
        name=cat_data["name"],
        defaults={"description": cat_data["description"]}
    )
    categories[cat_data["name"]] = cat
    status = "✓ Created" if created else "○ Exists"
    print(f"  {status}: Category '{cat.name}'")

print()

# ============================================================
# 2. CREATE BOOKS
# ============================================================
books_data = [
    # Fiction
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "isbn": "9780061120084", "category": "Fiction", "quantity": 5, "publisher": "Harper Perennial", "published_year": 1960, "description": "A classic of modern American literature about racial injustice in the Deep South."},
    {"title": "1984", "author": "George Orwell", "isbn": "9780451524935", "category": "Fiction", "quantity": 4, "publisher": "Signet Classic", "published_year": 1949, "description": "A dystopian novel set in a totalitarian society ruled by Big Brother."},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "isbn": "9780743273565", "category": "Fiction", "quantity": 3, "publisher": "Scribner", "published_year": 1925, "description": "A portrait of the Jazz Age in all of its decadence and excess."},
    {"title": "Pride and Prejudice", "author": "Jane Austen", "isbn": "9780141439518", "category": "Fiction", "quantity": 3, "publisher": "Penguin Classics", "published_year": 1813, "description": "A romantic novel following the Bennet family in Georgian-era England."},
    # Science
    {"title": "A Brief History of Time", "author": "Stephen Hawking", "isbn": "9780553380163", "category": "Science", "quantity": 3, "publisher": "Bantam", "published_year": 1988, "description": "An exploration of cosmology for the general reader."},
    {"title": "The Selfish Gene", "author": "Richard Dawkins", "isbn": "9780198788607", "category": "Science", "quantity": 2, "publisher": "Oxford University Press", "published_year": 1976, "description": "A gene-centered view of evolution."},
    {"title": "Cosmos", "author": "Carl Sagan", "isbn": "9780345539434", "category": "Science", "quantity": 2, "publisher": "Ballantine Books", "published_year": 1980, "description": "An exploration of the universe and humanity's place within it."},
    # Technology
    {"title": "Clean Code", "author": "Robert C. Martin", "isbn": "9780132350884", "category": "Technology", "quantity": 4, "publisher": "Prentice Hall", "published_year": 2008, "description": "A handbook of agile software craftsmanship."},
    {"title": "Design Patterns", "author": "Gang of Four", "isbn": "9780201633610", "category": "Technology", "quantity": 2, "publisher": "Addison-Wesley", "published_year": 1994, "description": "Elements of reusable object-oriented software."},
    {"title": "The Pragmatic Programmer", "author": "David Thomas & Andrew Hunt", "isbn": "9780135957059", "category": "Technology", "quantity": 3, "publisher": "Addison-Wesley", "published_year": 2019, "description": "Your journey to mastery in software development."},
    {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "isbn": "9780262033848", "category": "Technology", "quantity": 3, "publisher": "MIT Press", "published_year": 2009, "description": "The essential algorithms textbook known as CLRS."},
    # Mathematics
    {"title": "Calculus", "author": "James Stewart", "isbn": "9781285740621", "category": "Mathematics", "quantity": 5, "publisher": "Cengage Learning", "published_year": 2015, "description": "The most widely used calculus textbook."},
    {"title": "Linear Algebra Done Right", "author": "Sheldon Axler", "isbn": "9783319110790", "category": "Mathematics", "quantity": 2, "publisher": "Springer", "published_year": 2014, "description": "A rigorous yet accessible approach to linear algebra."},
    # History
    {"title": "Sapiens", "author": "Yuval Noah Harari", "isbn": "9780062316097", "category": "History", "quantity": 4, "publisher": "Harper", "published_year": 2015, "description": "A brief history of humankind."},
    {"title": "Guns, Germs, and Steel", "author": "Jared Diamond", "isbn": "9780393354324", "category": "History", "quantity": 2, "publisher": "W. W. Norton", "published_year": 1997, "description": "The fates of human societies."},
    # Philosophy
    {"title": "Meditations", "author": "Marcus Aurelius", "isbn": "9780140449334", "category": "Philosophy", "quantity": 3, "publisher": "Penguin Classics", "published_year": 180, "description": "Personal writings of the Roman Emperor on Stoic philosophy."},
    {"title": "The Republic", "author": "Plato", "isbn": "9780140455113", "category": "Philosophy", "quantity": 2, "publisher": "Penguin Classics", "published_year": -380, "description": "One of the most influential works of philosophy in Western thought."},
    # Business
    {"title": "The Lean Startup", "author": "Eric Ries", "isbn": "9780307887894", "category": "Business", "quantity": 3, "publisher": "Crown Business", "published_year": 2011, "description": "How today's entrepreneurs use continuous innovation."},
    {"title": "Zero to One", "author": "Peter Thiel", "isbn": "9780804139298", "category": "Business", "quantity": 2, "publisher": "Crown Business", "published_year": 2014, "description": "Notes on startups, or how to build the future."},
    # Self-Help
    {"title": "Atomic Habits", "author": "James Clear", "isbn": "9780735211292", "category": "Self-Help", "quantity": 5, "publisher": "Avery", "published_year": 2018, "description": "An easy & proven way to build good habits & break bad ones."},
    {"title": "Deep Work", "author": "Cal Newport", "isbn": "9781455586691", "category": "Self-Help", "quantity": 3, "publisher": "Grand Central", "published_year": 2016, "description": "Rules for focused success in a distracted world."},
    {"title": "The Psychology of Money", "author": "Morgan Housel", "isbn": "9780857197689", "category": "Self-Help", "quantity": 3, "publisher": "Harriman House", "published_year": 2020, "description": "Timeless lessons on wealth, greed, and happiness."},
    {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "isbn": "9780374533557", "category": "Self-Help", "quantity": 2, "publisher": "Farrar, Straus and Giroux", "published_year": 2011, "description": "A groundbreaking tour of the mind exploring two systems of thought."},
]

books = {}
for book_data in books_data:
    category = categories.get(book_data.pop("category"))
    book, created = Book.objects.get_or_create(
        isbn=book_data["isbn"],
        defaults={**book_data, "category": category}
    )
    books[book.isbn] = book
    status = "✓ Created" if created else "○ Exists"
    print(f"  {status}: '{book.title}' by {book.author}")

print()

# ============================================================
# 3. CREATE USERS
# ============================================================
# Admin
admin_user, created = CustomUser.objects.get_or_create(
    username='admin',
    defaults={
        'first_name': 'Library',
        'last_name': 'Admin',
        'email': 'admin@libraryms.com',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
        'phone': '9876543210',
    }
)
if created:
    admin_user.set_password('Admin@123')
    admin_user.save()
    print(f"  ✓ Created: Admin user 'admin' (password: Admin@123)")
else:
    print(f"  ○ Exists: Admin user 'admin'")

# Students
students_data = [
    {"username": "student1", "first_name": "Rahul", "last_name": "Sharma", "email": "rahul@student.com", "phone": "9876500001"},
    {"username": "student2", "first_name": "Priya", "last_name": "Patel", "email": "priya@student.com", "phone": "9876500002"},
    {"username": "student3", "first_name": "Arjun", "last_name": "Reddy", "email": "arjun@student.com", "phone": "9876500003"},
    {"username": "student4", "first_name": "Neha", "last_name": "Gupta", "email": "neha@student.com", "phone": "9876500004"},
    {"username": "student5", "first_name": "Vikram", "last_name": "Singh", "email": "vikram@student.com", "phone": "9876500005"},
]

students = []
for s_data in students_data:
    student, created = CustomUser.objects.get_or_create(
        username=s_data["username"],
        defaults={**s_data, "role": "student"}
    )
    if created:
        student.set_password('Student@123')
        student.save()
        print(f"  ✓ Created: Student '{student.username}' — {student.get_full_name()} (password: Student@123)")
    else:
        print(f"  ○ Exists: Student '{student.username}'")
    students.append(student)

print()

# ============================================================
# 4. CREATE ISSUED BOOK RECORDS
# ============================================================
now = timezone.now()
book_list = list(books.values())

# Only create if no issues exist
if IssuedBook.objects.count() == 0:
    issues_data = [
        # Active issues (currently issued)
        {"user": students[0], "book": book_list[0], "days_ago": 5, "due_days": 14, "status": "issued"},
        {"user": students[0], "book": book_list[7], "days_ago": 3, "due_days": 14, "status": "issued"},
        {"user": students[1], "book": book_list[1], "days_ago": 10, "due_days": 14, "status": "issued"},
        {"user": students[2], "book": book_list[4], "days_ago": 2, "due_days": 14, "status": "issued"},
        {"user": students[2], "book": book_list[19], "days_ago": 7, "due_days": 14, "status": "issued"},
        {"user": students[3], "book": book_list[13], "days_ago": 4, "due_days": 14, "status": "issued"},

        # Overdue issues
        {"user": students[1], "book": book_list[9], "days_ago": 20, "due_days": 14, "status": "issued"},
        {"user": students[4], "book": book_list[3], "days_ago": 25, "due_days": 14, "status": "issued"},

        # Returned (on time)
        {"user": students[0], "book": book_list[13], "days_ago": 30, "due_days": 14, "returned_days_ago": 20, "status": "returned", "fine": 0},
        {"user": students[1], "book": book_list[17], "days_ago": 40, "due_days": 14, "returned_days_ago": 30, "status": "returned", "fine": 0},
        {"user": students[2], "book": book_list[10], "days_ago": 35, "due_days": 14, "returned_days_ago": 24, "status": "returned", "fine": 0},
        {"user": students[3], "book": book_list[20], "days_ago": 45, "due_days": 14, "returned_days_ago": 35, "status": "returned", "fine": 0},
        {"user": students[4], "book": book_list[6], "days_ago": 50, "due_days": 14, "returned_days_ago": 40, "status": "returned", "fine": 0},

        # Returned (late, with fines)
        {"user": students[0], "book": book_list[5], "days_ago": 35, "due_days": 14, "returned_days_ago": 18, "status": "returned", "fine": 15},
        {"user": students[3], "book": book_list[2], "days_ago": 30, "due_days": 14, "returned_days_ago": 12, "status": "returned", "fine": 20},
        {"user": students[4], "book": book_list[14], "days_ago": 40, "due_days": 14, "returned_days_ago": 20, "status": "returned", "fine": 30},
    ]

    for issue_data in issues_data:
        issue_date = now - timedelta(days=issue_data["days_ago"])
        due_date = issue_date + timedelta(days=issue_data["due_days"])
        return_date = None
        fine = Decimal('0.00')

        if issue_data["status"] == "returned":
            return_date = now - timedelta(days=issue_data.get("returned_days_ago", 0))
            fine = Decimal(str(issue_data.get("fine", 0)))

        issue = IssuedBook.objects.create(
            user=issue_data["user"],
            book=issue_data["book"],
            issue_date=issue_date,
            due_date=due_date,
            return_date=return_date,
            fine=fine,
            status=issue_data["status"],
            issued_by=admin_user,
        )

        # Update available quantity for issued books
        if issue_data["status"] == "issued":
            book = issue_data["book"]
            book.available_quantity = max(0, book.available_quantity - 1)
            book.save()

        print(f"  ✓ Issue: '{issue.book.title}' → {issue.user.get_full_name()} [{issue.status}]")

    print()
else:
    print("  ○ Issue records already exist, skipping.")
    print()

# ============================================================
# SUMMARY
# ============================================================
print("=" * 60)
print("  SEED COMPLETE!")
print("=" * 60)
print(f"  Categories:  {Category.objects.count()}")
print(f"  Books:       {Book.objects.count()}")
print(f"  Users:       {CustomUser.objects.count()}")
print(f"  Issues:      {IssuedBook.objects.count()}")
print()
print("  LOGIN CREDENTIALS:")
print("  ─────────────────────────────────────")
print("  Admin:    admin / Admin@123")
print("  Students: student1-5 / Student@123")
print("=" * 60)
