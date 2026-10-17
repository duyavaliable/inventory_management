# Inventory Management System

A Django web application for managing store operations in one place. Track products, inventory, suppliers, customers, and orders through the management interface, and let customers browse products and pay online with PayOS.

## Features

- Manage products, categories, product groups, prices, and stock quantities.
- Maintain supplier records, customer profiles, and orders.
- Track payment status and update inventory after an order is paid.
- Review business activity on the dashboard.
- Register, sign in, and manage user accounts.
- Create PayOS payment links for orders.

## Technology Stack

- Python 3.10 or later and Django 5.2
- MySQL, connected through PyMySQL
- Django Crispy Forms with Bootstrap 5
- PayOS for online payments

## Installation and Setup

### 1. Clone the repository and create a virtual environment

```bash
git clone https://github.com/duyavaliable/inventory_management.git
cd inventory_management
python -m venv venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Set up MySQL

Install and start MySQL, then create the database:

```sql
CREATE DATABASE inventory CHARACTER SET utf8mb4;
```

Open `inventory_management/settings.py` and update `DATABASES` with your MySQL database name, username, password, host, and port. The current configuration defaults to the `inventory` database on `localhost:3306`.

### 4. Configure PayOS (optional)

To enable online payments, replace the placeholder values for `PAYOS_CLIENT_ID`, `PAYOS_API_KEY`, and `PAYOS_CHECKSUM_KEY` in `inventory_management/settings.py` with your PayOS credentials. PayOS must be able to reach the callback URL. Do not commit API keys or other sensitive credentials to a public repository.

### 5. Apply migrations and run the application

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open the application at <http://127.0.0.1:8000/>. The Django administration site is available at <http://127.0.0.1:8000/admin/>.

## Notes

- `createsuperuser` creates an administrator account for the `/admin/` site.
- Run `makemigrations` only when you change the models.
- The secret key and database credentials in `settings.py` are for development. Before deploying to production, move sensitive values to environment variables and set `DEBUG` to `False`.
