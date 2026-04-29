# Library Management System

A full-featured, premium **Library Management System** built with Django 6. Designed with a beautiful dark/light responsive UI for both administrators and students.

## ✨ Features

### Admin
- 📚 Full Book CRUD (add, edit, delete with cover images)
- 👥 Student management with registration
- 📋 Issue & Return books with automatic fine calculation (₹5/day)
- 🔔 Real-time notification system
- 📅 Book reservation management
- 📊 Activity logs for auditing
- 📈 Reports & analytics dashboard
- 📤 CSV export for books, users & issued books
- 🔍 AJAX-powered live book search

### Student
- 🔑 Login & registration
- 📖 Browse book catalog
- 📚 View personal issued books
- 🔄 Renew books online
- 🔔 Receive notifications

### UI/UX
- 🌗 **Dark / Light mode toggle** (persists via localStorage)
- 📱 Fully responsive layout
- ✨ Glassmorphism, smooth animations, premium aesthetics

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/msrikailash/library-management-system-.git
cd library-management-system-

# Create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# (Optional) Seed sample data
python seed_data.py

# Run the development server
python manage.py runserver
```

Then open **http://127.0.0.1:8000** in your browser.

### Default Admin Login
After running `seed_data.py`:
- **Username:** `admin`
- **Password:** `admin123`

## 🏗️ Project Structure

```
├── accounts/          # Custom user model & auth
├── core/              # Django settings, URLs, WSGI
├── library/           # Main app (models, views, URLs, forms)
├── templates/         # All HTML templates
├── static/            # CSS, JS, images
├── media/             # Uploaded book covers
├── requirements.txt
├── Procfile           # For Heroku / Render deployment
└── manage.py
```

## 🌐 Deployment

The project is configured for deployment on platforms like **Render** or **Railway**:

1. Set `DEBUG=False` in environment variables.
2. Set a strong `SECRET_KEY`.
3. Run `python manage.py collectstatic` before deploying.
4. The `Procfile` is already configured to use `gunicorn`.

## 🛠️ Tech Stack

- **Backend:** Django 6
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Frontend:** HTML5, Vanilla CSS (custom design system), JavaScript
- **UI Components:** Bootstrap 5 (layout only), Bootstrap Icons
- **Fonts:** Inter, Outfit (Google Fonts)
