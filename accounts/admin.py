from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = UserAdmin.fieldsets + (
        ('Library Info', {'fields': ('role', 'phone', 'address', 'profile_pic')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Library Info', {'fields': ('role', 'phone', 'address')}),
    )