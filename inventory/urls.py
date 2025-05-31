from django.contrib import admin
from django.urls import path
from .views import (Index, SignUpView, 
                    AddItem, EditItem, DeleteItem, 
                    ProductGroupCreateView, ProductGroupDeleteView, 
                    ProductGroupUpdateView, AccountUpdateView,
                    SupplierListView, SupplierCreateView, SupplierUpdateView,
                    SupplierDeleteView, OrderListView,
                    CustomerListView, CustomerCreateView, CustomerUpdateView, 
                    CustomerDeleteView, DashboardOverviewView, ProductsView,
                    CustomerShopView, CreatePaymentView, PaymentReturnView, 
                    PaymentCancelView, PayOSWebhookView
)
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordChangeView 
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CustomPasswordChangeForm

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'inventory/password_change.html'
    success_url = reverse_lazy('account-edit')

    def form_valid(self, form):
        messages.success(self.request, "Mật khẩu đã được thay đổi thành công!")
        return super().form_valid(form)

urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('products/', ProductsView.as_view(), name='products'),
    path('add-item/', AddItem.as_view(), name='add-item'),
    path('edit-item/<int:pk>', EditItem.as_view(), name='edit-item'),
    path('delete-item/<int:pk>', DeleteItem.as_view(), name='delete-item'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='inventory/logout.html'), name='logout'),
    path('productgroup/new/', ProductGroupCreateView.as_view(), name='productgroup-create'),
    path('productgroup/<int:pk>/delete/', ProductGroupDeleteView.as_view(), name='productgroup-delete'),
    path('productgroup/<int:pk>/update/', ProductGroupUpdateView.as_view(), name='productgroup-update'),
    path('account/edit/', AccountUpdateView.as_view(), name='account-edit'),
    path('account/password/', CustomPasswordChangeView.as_view(
        form_class=CustomPasswordChangeForm
    ), name='password_change'),
    path('supplier/', SupplierListView.as_view(), name='supplier-list'),
    path('supplier/new/', SupplierCreateView.as_view(), name='supplier-create'),
    path('supplier/<int:pk>/update/', SupplierUpdateView.as_view(), name='supplier-update'),
    path('supplier/<int:pk>/delete/', SupplierDeleteView.as_view(), name='supplier-delete'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer-create'),
    path('customers/<int:pk>/update/', CustomerUpdateView.as_view(), name='customer-update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer-delete'),
    path('dashboard/', DashboardOverviewView.as_view(), name='dashboard'),
    path('shop/', CustomerShopView.as_view(), name='customer-shop'),
    path('checkout/initiate-payment/', CreatePaymentView.as_view(), name='initiate-payment'),
    path('checkout/payment/return/', PaymentReturnView.as_view(), name='payment-return'),
    path('checkout/payment/cancel/', PaymentCancelView.as_view(), name='payment-cancel'),
    path('checkout/payment/webhook/', PayOSWebhookView.as_view(), name='payos-webhook'),
]
