import traceback
from django.shortcuts import redirect
from django.urls import reverse
# Giả sử bạn có UserProfile được liên kết với User
# from .models import UserProfile # Bỏ comment nếu cần và UserProfile ở models.py

class RoleBasedRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None # Chỉ áp dụng cho người dùng đã xác thực

        current_path = request.path_info
        
        # Các URL được phép truy cập mà không cần kiểm tra vai trò từ middleware này
        # (ví dụ: logout, trang chỉnh sửa tài khoản của chính họ, các URL của PayOS)
        # Bạn cần đảm bảo các URL này không gây ra vòng lặp chuyển hướng.
        allowed_paths_for_all_authenticated = [
            reverse('logout'),
            reverse('account-edit'), # Giả sử tên URL là 'account-edit'
            reverse('password_change'), # Giả sử tên URL là 'password_change'
            reverse('initiate-payment'), # <<< ĐÃ THÊM
            reverse('payment-return'),   # <<< ĐÃ THÊM (cho URL trả về từ PayOS)
            reverse('payment-cancel'),   # <<< ĐÃ THÊM (cho URL hủy từ PayOS)
            # Thêm các URL khác nếu cần
        ]

        if current_path in allowed_paths_for_all_authenticated:
            print(f"DEBUG Middleware: Path '{current_path}' is allowed for all authenticated users. Skipping role check.") # DEBUG
            return None # <<< Bỏ qua kiểm tra vai trò cho các path này

        # Phần còn lại của logic kiểm tra vai trò và chuyển hướng sẽ bắt đầu từ đây
        try:
            if hasattr(request.user, 'profile'):
                user_role = request.user.profile.role
                
                # In thông tin gỡ lỗi cho mọi request đã xác thực (trừ các path đã loại trừ ở trên)
                print(f"DEBUG Middleware (Global Check): User: {request.user.username}, Role: '{user_role}', Path: {current_path}")

                customer_shop_url = reverse('customer-shop')
                dashboard_url = reverse('dashboard')

                if user_role == 'customer':
                    # Nếu người dùng là 'customer' nhưng không ở trang 'customer-shop'
                    # (và không phải là một trong các allowed_paths_for_all_authenticated)
                    if current_path != customer_shop_url:
                        print(f"DEBUG Middleware: Customer '{request.user.username}' đang ở '{current_path}'. Chuyển hướng đến '{customer_shop_url}'.")
                        return redirect(customer_shop_url)
                else: # Giả sử các vai trò khác (ví dụ: 'manager') nên được chuyển đến dashboard
                    # Nếu người dùng không phải 'customer' (ví dụ: 'manager') nhưng đang ở trang 'customer-shop'
                    if current_path == customer_shop_url:
                        print(f"DEBUG Middleware: Manager '{request.user.username}' đang ở '{customer_shop_url}'. Chuyển hướng đến '{dashboard_url}'.")
                        return redirect(dashboard_url)
                    # Nếu người dùng không phải 'customer' và đang ở trang chủ ('/') hoặc trang login ('/login/')
                    # (logic này giữ lại từ phiên bản trước của bạn, hữu ích nếu LOGIN_REDIRECT_URL là '/')
                    elif current_path == '/' or current_path == reverse('login'): # Cẩn thận với reverse('login') nếu người dùng đã xác thực
                        print(f"DEBUG Middleware: Manager '{request.user.username}' đang ở '{current_path}'. Chuyển hướng đến '{dashboard_url}'.")
                        return redirect(dashboard_url)
            else:
                print(f"DEBUG Middleware: User {request.user.username} không có thuộc tính 'profile'.")
        
        except Exception as e: # Bắt lỗi cụ thể hơn nếu có thể
            print(f"DEBUG Middleware: Exception occurred: {e}")
            traceback.print_exc()
            # pass # Cẩn thận khi bỏ qua lỗi một cách âm thầm

        return None