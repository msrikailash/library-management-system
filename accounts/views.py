from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import StudentRegistrationForm, CustomLoginForm, ProfileEditForm, CustomPasswordChangeForm
from .models import CustomUser


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def profile_view(request):
    context = {'user': request.user}
    
    if request.user.is_admin_user:
        from library.models import LibrarySetting
        setting = LibrarySetting.get_settings()
        
        if request.method == 'POST' and 'update_fine' in request.POST:
            new_fine = request.POST.get('fine_per_day')
            try:
                setting.fine_per_day = float(new_fine)
                setting.save()
                messages.success(request, 'Library fine settings updated successfully.')
                return redirect('profile')
            except ValueError:
                messages.error(request, 'Invalid fine amount.')
                
        context['library_setting'] = setting

    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})
