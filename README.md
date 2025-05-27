# Hệ thống Quản lý Kho hàng

Đây là ứng dụng web quản lý kho hàng được xây dựng bằng Django, cho phép người dùng theo dõi hàng tồn kho, quản lý sản phẩm theo nhóm, và nhận thông báo khi số lượng tồn kho thấp.

## Yêu cầu hệ thống

- Python 3.10 hoặc cao hơn
- pip (công cụ quản lý gói Python)
- Virtualenv (khuyến nghị)

## Cài đặt

### Bước 1: Clone dự án

```bash
git clone https://github.com/duyavaliable/inventory_management.git
cd inventory_management

### Bước 2: Tạo môi trường ảo
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

### Bước 3:Cài đặt các gói phụ thuộc
pip install django==5.2.1
pip install django-crispy-forms
pip install crispy-bootstrap5

### Bước 4: Cấu hình cơ sở dữ liệu
python manage.py makemigrations
python manage.py migrate

### Bước 5: Tạo tài khoản quản trị viên
python manage.py createsuperuser


python manage.py runserver