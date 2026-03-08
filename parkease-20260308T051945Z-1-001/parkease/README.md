# 🅿️ ParkEase — Integrated Parking & Vehicle Services Management System

ParkEase is a Django-based web application for managing a public parking facility with tyre clinic and battery hire services.

## Features

### Core Module — Parking Management
- ✅ Vehicle registration (Truck, Personal Car, Taxi, Coaster, Boda-boda)
- ✅ Automatic parking fee calculation (day/night/short-stay rates)
- ✅ Unique receipt generation per transaction
- ✅ Vehicle sign-out with receiver details
- ✅ Active vehicle dashboard with live duration timer
- ✅ Receipt printing

### Extra Credit Modules
- ✅ Tyre Clinic — pressure, puncture, valve, new tyre sales
- ✅ Battery Section — hire & sales with date tracking

### Administration
- ✅ Daily revenue report by section
- ✅ Signed-out vehicles per day
- ✅ User management (create/delete)

### Authentication
- ✅ Role-based login (Admin, Attendant, Tyre Manager, Battery Manager)
- ✅ Route protection per role

### Validation
- ✅ Names must start with capital letter, no digits
- ✅ Number plates must start with 'U', alphanumeric, <6 chars
- ✅ Ugandan phone number validation
- ✅ NIN format validation
- ✅ NIN required for Boda-boda vehicles
- ✅ Both frontend (JS) and backend (Django forms) validation

---

## Setup Instructions

### Requirements
- Python 3.8+
- pip

### 1. Install Django
```bash
pip install django
```

### 2. Navigate to project folder
```bash
cd parkease
```

### 3. Run database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Set up initial data (users + sample prices)
```bash
python manage.py setup_parkease
```

### 5. Start the development server
```bash
python manage.py runserver
```

### 6. Open in browser
Visit: http://127.0.0.1:8000/

---

## Default Login Credentials

| Role              | Username       | Password      |
|-------------------|----------------|---------------|
| System Admin      | `admin`        | `parkease123` |
| Parking Attendant | `attendant1`   | `attend123`   |
| Tyre Manager      | `tyre_mgr`     | `tyre123`     |
| Battery Manager   | `battery_mgr`  | `battery123`  |

---

## Parking Rates

| Vehicle Type | Day (6AM–7PM) | Night (7PM–6AM) | < 3 Hours |
|--------------|---------------|-----------------|-----------|
| Truck        | UGX 5,000     | UGX 10,000      | UGX 2,000 |
| Personal Car | UGX 3,000     | UGX 2,000       | UGX 2,000 |
| Taxi         | UGX 3,000     | UGX 2,000       | UGX 2,000 |
| Coaster      | UGX 4,000     | UGX 2,000       | UGX 3,000 |
| Boda-boda    | UGX 2,000     | UGX 2,000       | UGX 1,000 |

---

## Technology Stack
- **Backend:** Python 3 + Django
- **Database:** SQLite (via Django ORM)
- **Frontend:** HTML5, CSS3, JavaScript
- **Fonts:** Syne (headings), DM Sans (body)

## Project Structure
```
parkease/
├── manage.py
├── parkease/           # Django config
│   ├── settings.py
│   └── urls.py
├── core/               # Main app
│   ├── models.py       # Database models
│   ├── views.py        # View logic
│   ├── forms.py        # Forms & validation
│   ├── admin.py
│   ├── management/commands/setup_parkease.py
│   └── templates/core/ # HTML templates
├── static/css/style.css
└── db.sqlite3          # Created on first run
```

## Assumptions
1. A vehicle can only have one active parking session at a time.
2. Parking fee is calculated based on arrival time (day/night) and duration.
3. The system uses Africa/Kampala timezone.
4. Boda-boda operators require NIN as per Ugandan regulations.
5. Number plates follow Uganda format: start with U, alphanumeric, max 5 characters.
