from django import forms
from .models import Book, Category, IssuedBook
from django.utils import timezone
from datetime import timedelta


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'category', 'quantity', 'description',
                  'publisher', 'published_year', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Book Title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author Name'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN (13 digits)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'published_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class IssueBookForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=lambda: (timezone.now() + timedelta(days=14)).date()
    )

    class Meta:
        model = IssuedBook
        fields = ['user', 'book', 'due_date', 'notes']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'book': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        from accounts.models import CustomUser
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = CustomUser.objects.filter(role='student', is_active=True)
        self.fields['book'].queryset = Book.objects.filter(available_quantity__gt=0)
        self.fields['due_date'].initial = (timezone.now() + timedelta(days=14)).date()

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        from django.utils.timezone import make_aware
        from datetime import datetime
        if due_date:
            return make_aware(datetime.combine(due_date, datetime.min.time()))
        return due_date


class ReturnBookForm(forms.ModelForm):
    class Meta:
        model = IssuedBook
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Return notes (optional)'}),
        }


class BookSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '🔍 Search books by title, author, or ISBN...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    availability = forms.ChoiceField(
        choices=[('', 'All'), ('available', 'Available'), ('unavailable', 'Unavailable')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

