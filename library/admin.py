from django.contrib import admin
from .models import Category, Book, IssuedBook

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'category', 'quantity', 'available_quantity', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'author', 'isbn']
    readonly_fields = ['available_quantity', 'created_at', 'updated_at']

@admin.register(IssuedBook)
class IssuedBookAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'issue_date', 'due_date', 'return_date', 'fine', 'status']
    list_filter = ['status', 'issue_date']
    search_fields = ['book__title', 'user__username']
    readonly_fields = ['created_at']
