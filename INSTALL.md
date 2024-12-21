# Installation Guide

## Requirements

- **Python** 3.8.0 or higher
- **Django** 4.1

## Quick Start

### 1. Download and Install Python
- Download [Python 3.8.0](https://www.python.org/downloads/release/python-380/) or higher and follow the installation instructions for your operating system.

### 2. Install Django
Install Django 4.1 via `pip`:

```bash
pip install django==4.1
```

### 3. Clone the Respository
```bash
https://github.com/Software-Engineering-Project-PKHSAK/To-Done.git
cd To-Done
```

### 4. Install Additional Dependencies (if any)
```bash
pip install -r requirements.txt
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Start the Application
```bash
python manage.py runserver 8080
```

### 7. Open in Browser

Point your browser to http://127.0.0.1:8080 to explore the app.
