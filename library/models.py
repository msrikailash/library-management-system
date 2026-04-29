from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    published_year = models.PositiveIntegerField(blank=True, null=True)
    image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author}"

    def is_available(self):
        return self.available_quantity > 0

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.available_quantity = self.quantity
        super().save(*args, **kwargs)


class LibrarySetting(models.Model):
    fine_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)

    class Meta:
        verbose_name = "Library Setting"
        verbose_name_plural = "Library Settings"

    @classmethod
    def get_settings(cls):
        setting, created = cls.objects.get_or_create(pk=1)
        return setting

    def __str__(self):
        return f"Library Settings (Fine: ${self.fine_per_day}/day)"


class IssuedBook(models.Model):
    STATUS_CHOICES = (
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='issued_books'
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issued_records')
    issue_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(blank=True, null=True)
    fine = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='issued')
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='books_issued_by_admin'
    )
    notes = models.TextField(blank=True, null=True)
    renewal_count = models.PositiveIntegerField(default=0)
    max_renewals = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.book.title} — {self.user.username}"

    def save(self, *args, **kwargs):
        if self._state.adding and not self.due_date:
            self.due_date = timezone.now() + timedelta(days=14)
        super().save(*args, **kwargs)

    def calculate_fine(self):
        setting = LibrarySetting.get_settings()
        fine_rate = setting.fine_per_day
        
        if self.return_date:
            if self.return_date > self.due_date:
                overdue_days = (self.return_date - self.due_date).days
                return fine_rate * overdue_days
        elif timezone.now() > self.due_date:
            overdue_days = (timezone.now() - self.due_date).days
            return fine_rate * overdue_days
        return Decimal('0.00')

    def is_overdue(self):
        if self.status == 'issued':
            return timezone.now() > self.due_date
        return False

    def days_until_due(self):
        if self.status == 'issued':
            delta = self.due_date - timezone.now()
            return delta.days
        return None

    def abs_days_until_due(self):
        days = self.days_until_due()
        return abs(days) if days is not None else None


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=50, default='info')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.message}"


class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.user.username if self.user else 'System'}"

