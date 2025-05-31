from django.shortcuts import redirect
from django.urls import reverse

class RoleBasedRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            # Nếu người dùng đã đăng nhập và đang truy cập trang chủ hoặc trang đăng nhập
            if request.path == '/' or request.path == reverse('login'):
                try:
                    # Kiểm tra vai trò và điều hướng
                    if hasattr(request.user, 'profile'):
                        if request.user.profile.role == 'customer':
                            return redirect('customer-shop')  # Trang shop cho khách hàng
                        else:
                            return redirect('dashboard')  # Trang dashboard cho quản lý
                except:
                    pass
        return None