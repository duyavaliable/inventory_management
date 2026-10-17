# Hệ thống Quản lý Kho hàng

Ứng dụng web quản lý kho được xây dựng bằng Django, dành cho cửa hàng cần theo dõi sản phẩm, tồn kho, nhà cung cấp, khách hàng và đơn hàng trên cùng một hệ thống. Ứng dụng có khu vực mua hàng trực tuyến và hỗ trợ thanh toán qua PayOS.

## Tính năng

- Quản lý sản phẩm, danh mục, nhóm hàng, giá bán và số lượng tồn kho.
- Quản lý nhà cung cấp, hồ sơ khách hàng và đơn hàng.
- Theo dõi trạng thái thanh toán; cập nhật tồn kho sau khi đơn hàng được thanh toán.
- Xem trang tổng quan về hoạt động kinh doanh.
- Đăng ký, đăng nhập và quản lý tài khoản người dùng.
- Tạo liên kết thanh toán PayOS cho đơn hàng.

## Công nghệ

- Python 3.10 trở lên và Django 5.2
- MySQL, kết nối thông qua PyMySQL
- Django Crispy Forms với Bootstrap 5
- PayOS cho thanh toán trực tuyến

## Cài đặt và chạy

### 1. Lấy mã nguồn và tạo môi trường ảo

```bash
git clone https://github.com/duyavaliable/inventory_management.git
cd inventory_management
python -m venv venv
```

Kích hoạt môi trường ảo:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source venv/bin/activate
```

### 2. Cài đặt thư viện

```bash
python -m pip install -r requirements.txt
```

### 3. Chuẩn bị MySQL

Cài đặt và khởi động MySQL, sau đó tạo cơ sở dữ liệu:

```sql
CREATE DATABASE inventory CHARACTER SET utf8mb4;
```

Mở `inventory_management/settings.py` và cập nhật `DATABASES` với tên cơ sở dữ liệu, tài khoản, mật khẩu, máy chủ và cổng MySQL của bạn. Cấu hình hiện tại mặc định dùng cơ sở dữ liệu `inventory` trên `localhost:3306`.

### 4. Cấu hình PayOS (tùy chọn)

Để bật thanh toán trực tuyến, thay các giá trị mẫu `PAYOS_CLIENT_ID`, `PAYOS_API_KEY` và `PAYOS_CHECKSUM_KEY` trong `inventory_management/settings.py` bằng thông tin từ PayOS. URL callback cần truy cập được từ PayOS. Không đưa khóa API hoặc thông tin nhạy cảm vào mã nguồn công khai.

### 5. Khởi tạo dữ liệu và chạy ứng dụng

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Mở ứng dụng tại <http://127.0.0.1:8000/>. Trang quản trị Django nằm tại <http://127.0.0.1:8000/admin/>.

## Ghi chú

- `createsuperuser` tạo tài khoản quản trị để đăng nhập trang `/admin/`.
- `makemigrations` chỉ cần chạy khi có thay đổi về model.
- Các khóa bí mật và thông tin kết nối cơ sở dữ liệu trong `settings.py` hiện là cấu hình dành cho phát triển. Trước khi triển khai thực tế, hãy chuyển chúng sang biến môi trường và tắt `DEBUG`.
