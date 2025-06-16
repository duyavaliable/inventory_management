# Hệ thống Quản lý Kho hàng

Đây là ứng dụng web quản lý kho hàng được xây dựng bằng Django. Hệ thống cho phép người dùng theo dõi hàng tồn kho, quản lý sản phẩm, nhà cung cấp, đơn hàng, khách hàng, và tích hợp thanh toán trực tuyến qua PayOS.

## Tính năng nổi bật

*   **Quản lý Sản phẩm:** Thêm, sửa, xóa, xem danh sách sản phẩm. Phân loại sản phẩm theo danh mục và nhóm.
*   **Quản lý Tồn kho:** Theo dõi số lượng sản phẩm, cập nhật tồn kho tự động sau khi bán hàng. Cảnh báo khi sản phẩm dưới mức tồn kho tối thiểu.
*   **Quản lý Nhà cung cấp:** Lưu trữ thông tin nhà cung cấp.
*   **Quản lý Đơn hàng:** Tạo và theo dõi trạng thái đơn hàng.
*   **Quản lý Khách hàng:** Lưu trữ thông tin khách hàng và lịch sử mua hàng.
*   **Giao diện Bán hàng (POS):** Giao diện thân thiện cho nhân viên tạo đơn hàng và thanh toán tại cửa hàng.
*   **Tích hợp Thanh toán PayOS:** Cho phép khách hàng thanh toán đơn hàng trực tuyến một cách an toàn và tiện lợi.
*   **Trang Tổng quan (Dashboard):** Hiển thị các số liệu thống kê quan trọng về doanh thu, sản phẩm bán chạy, và hoạt động kinh doanh.
*   **Quản lý Người dùng:** Đăng ký, đăng nhập, quản lý thông tin tài khoản, phân quyền người dùng.

## Yêu cầu hệ thống

*   Python 3.10 hoặc cao hơn
*   pip (công cụ quản lý gói Python)
*   Virtualenv (khuyến nghị để tạo môi trường ảo)

## Cài đặt

### Bước 1: Clone dự án

```bash
git clone https://github.com/duyavaliable/inventory_management.git
cd inventory_management
```
### Bước 2: Tạo và kích hoạt môi trường ảo
# Tạo môi trường ảo (ví dụ: tên là 'venv')
```bash
python -m venv venv
```
# Kích hoạt môi trường ảo
# Trên Windows:
```bash
venv\Scripts\activate
```

### Bước 3: Cài đặt các gói phụ thuộc
Cài đặt các gói từ file requirements.txt:
```bash
pip install -r requirements.txt
```

### Bước 4: Thiết lập static files
Django sử dụng static files để phục vụ các tập tin CSS, JavaScript và hình ảnh. Sau khi cài đặt, chạy lệnh sau để thu thập tất cả các static files vào thư mục chỉ định:


```bash
python manage.py collectstatic
```
### Bước 5: Cấu hình cơ sở dữ liệu
Tạo tài khoản quản trị để truy cập vào trang admin của Django:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Bước 6: Tạo tài khoản quản trị viên (Superuser)
Tạo tài khoản quản trị để truy cập vào trang admin của Django:
```bash
python manage.py createsuperuser
```

Cấu hình PayOS
Để sử dụng tích hợp thanh toán PayOS, bạn cần thêm thông tin API của PayOS vào file settings.py:
```bash
PAYOS_CLIENT_ID = 'YOUR_CLIENT_ID'
PAYOS_API_KEY = 'YOUR_API_KEY'
PAYOS_CHECKSUM_KEY = 'YOUR_CHECKSUM_KEY'
```
Chạy ứng dụng
```bash
python manage.py runserver
```