from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView, ListView
from django.views.generic.edit import CreateView 
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from .forms import UserRegisterForm, InventoryItemForm, ProductGroupForm
from .models import InventoryItem, Category, ProductGroup
from inventory_management.settings import LOW_QUANTITY
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from .forms import ( UserUpdateForm, UserProfileUpdateForm, 
                    SupplierForm, OrderForm, CustomerForm
)
from .models import UserProfile, Supplier, Order, Customer
from django.contrib.messages import get_messages as django_get_messages
from django.utils import timezone



class Index(TemplateView):
	template_name = 'inventory/index.html'

class ProductsView(LoginRequiredMixin, View):
	def get(self, request):
		search_query = request.GET.get('q', None)
		selected_group_ids = request.GET.getlist('product_group_filter')
		stock_filter = request.GET.get('stock_filter', None)
		supplier_filter = request.GET.get('supplier_filter', None)

		user_items = InventoryItem.objects.filter(user=self.request.user.id)
		
		#Loc theo tu khoa tim kiem (ten hoac SKU san pham)
		if search_query:
			user_items = user_items.filter(
				Q(name__icontains=search_query) | Q(sku__icontains=search_query)
			)
		#Loc theo nhom hang
		selected_group_ids_int = []
		if selected_group_ids:
			# Chuyển đổi danh sách ID nhóm hàng từ chuỗi sang danh sách số nguyên
			for gid_str in selected_group_ids:
				if gid_str.isdigit():
					selected_group_ids_int.append(int(gid_str))
	 
		if selected_group_ids_int: # Chỉ lọc nếu có ID hợp lệ
			user_items = user_items.filter(product_group__id__in=selected_group_ids_int)

		#Loc theo ton kho
		if stock_filter:
			print(f"Stock filter applied: {stock_filter}")
			# LOW_QUANTITY được định nghĩa trong settings.py là 10	
			if stock_filter == 'low':
				user_items = user_items.filter(quantity__lte=LOW_QUANTITY) #định mức LOW_QUANTITY được định nghĩa trong setting.py là 10
			elif stock_filter == 'in_stock':
				user_items = user_items.exclude(quantity__isnull=True).filter(quantity__gt=0)
			elif stock_filter == 'out_stock':
				user_items = user_items.filter(quantity=0)
		
		low_inventory_ids = list(InventoryItem.objects.filter(user=self.request.user.id, quantity__lte=LOW_QUANTITY).values_list('id', flat=True))

		#lay tat ca nhom hang de hien thi trong sidebar
		all_product_groups = ProductGroup.objects.all().order_by('name')
		#Lọc theo nhà cung cấp
		all_suppliers = Supplier.objects.all().order_by('name')
		#chuan bi form de tao nhom hang moi trong modal
		product_group_form = ProductGroupForm()
		
		#Sap xep ket qua cuoi cung
		items = user_items.order_by('id')
  
		context = { 
			'items': items,
			'low_inventory_ids': low_inventory_ids, # Giữ nguyên từ code gốc
			'all_product_groups': all_product_groups,
			'all_suppliers': all_suppliers, # Danh sách tất cả nhà cung cấp
			'selected_group_ids': selected_group_ids_int, # Truyền lại ID đã chọn (dạng số nguyên)
			'selected_supplier': supplier_filter, #them nha cung cap da chon
   			'product_group_form': product_group_form,
			'search_query': search_query,  
			'stock_filter': stock_filter,  
		} 	

		return render(request, 'inventory/Product_overview.html', context)

class SignUpView(View):
	def get(self, request):
		form = UserRegisterForm()
		return render(request, 'inventory/signup.html', {'form': form})

	def post(self, request):
		form = UserRegisterForm(request.POST)
		if form.is_valid():
			# Lưu thông tin User
			user = form.save()
			
			# Lưu thông tin profile từ form
			profile, created = UserProfile.objects.get_or_create(user=user)
			profile.display_name = form.cleaned_data.get('display_name')
			profile.phone_number = form.cleaned_data.get('phone_number')
			profile.save()
			
			username = form.cleaned_data.get('username')
			messages.success(request, f'Tài khoản {username} đã được tạo thành công! Bạn có thể đăng nhập ngay bây giờ.')
			return redirect('login')
		return render(request, 'inventory/signup.html', {'form': form})

class AddItem(LoginRequiredMixin, CreateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('products')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['categories'] = Category.objects.all()
		return context

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

class EditItem(LoginRequiredMixin, UpdateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('products')

class DeleteItem(LoginRequiredMixin, DeleteView):
	model = InventoryItem
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('products')
	context_object_name = 'item'

class ProductGroupCreateView(LoginRequiredMixin, CreateView):
	model = ProductGroup
	form_class = ProductGroupForm
	template_name = 'inventory/partials/productgroup_form_modal.html'
	success_url = reverse_lazy('products')

	def form_valid(self, form):
		response = super().form_valid(form)
		messages.success(self.request, f"Nhóm hàng '{form.instance.name}' đã được tạo thành công.")
		return response

#Xoa nhom hang
class ProductGroupDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductGroup
    success_url = reverse_lazy('products')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        group_name = self.object.name
        self.object.delete()
        messages.success(self.request, f"Nhóm hàng '{group_name}' đã được xóa thành công.")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return HttpResponseRedirect(self.success_url)
    
class ProductGroupUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductGroup
    fields = ['name']
    success_url = reverse_lazy('products')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Nhóm hàng '{form.instance.name}' đã được cập nhật thành công.")
        return response

#chỉnh lại khi đã hoàn thiện code 
class AccountUpdateView(LoginRequiredMixin, UpdateView): 
    model = User  # Thay đổi model từ UserProfile sang User
    form_class = UserUpdateForm
    template_name = 'inventory/account_edit.html'
    success_url = reverse_lazy('dashboard')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Kiểm tra và tạo profile nếu chưa tồn tại
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        
        if self.request.POST:
            context['user_form'] = UserUpdateForm(self.request.POST, instance=self.request.user)
            context['profile_form'] = UserProfileUpdateForm(self.request.POST, instance=profile)
        else:
            context['user_form'] = UserUpdateForm(instance=self.request.user)
            context['profile_form'] = UserProfileUpdateForm(instance=profile)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        profile_form = context['profile_form']
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(self.request, 'Thông tin tài khoản đã được cập nhật thành công!')
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        return self.form_valid(form)

#hien thi danh sach nha cung cap
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'
    
    #kiem tra xem co thong bao nao trong request hay khong
    def get(self, request, *args, **kwargs):
        # Debug: Print messages available in this request
        storage = django_get_messages(request)
        if storage:
            print("Messages in SupplierListView:")	
            for message in storage:
                print(f"- {message} (tags: {message.tags})")
        else:
            print("No messages found in SupplierListView.")
        # storage.used = False # Uncomment if messages disappear after this debug
        return super().get(request, *args, **kwargs)
    
#tao va cap nhat nha cung cap
class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Nhà cung cấp '{form.instance.name}' đã được tạo thành công.")
        return response 
class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Nhà cung cấp '{form.instance.name}' đã được cập nhật thành công.")
        return response
class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    success_url = reverse_lazy('supplier-list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        supplier_name = self.object.name
        self.object.delete()
        messages.success(self.request, f"Nhà cung cấp '{supplier_name}' đã được xóa thành công.")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return HttpResponseRedirect(self.success_url)
    
# Xem danh sách đơn hàng
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'inventory/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10 # Tùy chọn: nếu bạn muốn phân trang

    def get_queryset(self):
        # Tùy chọn lọc đơn hàng, ví dụ: cho người dùng hiện tại hoặc theo trạng thái
        # return Order.objects.all().order_by('-order_date') # Lấy tất cả đơn hàng
        return Order.objects.filter(user=self.request.user).order_by('-order_date')
class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'inventory/order_form.html' # Template bạn sẽ tạo ở bước 4
    success_url = reverse_lazy('order-list') # Chuyển hướng đến danh sách đơn hàng sau khi tạo thành công

    def form_valid(self, form):
        # Gán người dùng hiện tại cho đơn hàng trước khi lưu
        form.instance.user = self.request.user
        # Bạn có thể thực hiện các xử lý khác ở đây trước khi lưu form
        # Ví dụ: tính toán total_amount dựa trên các OrderItem (nếu có)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tạo đơn hàng mới'
        return context    
    
#Phan chuc nang khac hang
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'inventory/customer_list.html'
    context_object_name = 'customers'

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'inventory/customer_form.html'
    success_url = reverse_lazy('customer-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Thêm khách hàng mới'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Khách hàng đã được thêm thành công!')
        return super().form_valid(form)

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'inventory/customer_form.html'
    success_url = reverse_lazy('customer-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Cập nhật thông tin khách hàng'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Thông tin khách hàng đã được cập nhật!')
        return super().form_valid(form)

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('customer-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Khách hàng đã được xóa thành công!')
        return super().delete(request, *args, **kwargs)

#tong quan 
class DashboardOverviewView(LoginRequiredMixin, View):
    def get(self, request):
        # Lấy dữ liệu bán hàng hôm nay
        today = timezone.now().date()
        
        # Dữ liệu cho kết quả bán hàng hôm nay
        daily_sales = {
            'revenue': 0,  # Doanh thu
            'returns': 0,  # Trả hàng
            'net_revenue_percent': 22.30,  # Doanh thu thuần (%)
        }
        
        # Doanh thu theo tháng
        monthly_revenue = 719646000
        
        # Dữ liệu cho biểu đồ theo ngày (số liệu mẫu)
        daily_data = [
            23, 24, 34, 32, 8, 26, 26, 33, 18, 48, 40, 19, 18, 27, 22, 35, 22, 32, 20, 14, 28, 38, 28, 35, 42
        ]
        
        # Top 10 sản phẩm bán chạy
        top_products = [
            {'name': 'Quần kaki nam màu xanh', 'revenue': 416979000},
            {'name': 'Quần kaki nam màu kem', 'revenue': 302700000},
        ]
        
        # Top khách hàng
        top_customers = [
            {'name': 'Anh Hoàng - Sài Gòn', 'value': 245500000},
            {'name': 'Phạm Thu Hương', 'value': 223400000},
            {'name': 'Anh Giang - Kim Mã', 'value': 139000000},
            {'name': 'Nguyễn Văn Hải', 'value': 111700000},
        ]
        
        context = {
            'daily_sales': daily_sales,
            'monthly_revenue': monthly_revenue,
            'daily_data': daily_data,
            'top_products': top_products,
            'top_customers': top_customers,
        }
        
        return render(request, 'inventory/dashboard_overview.html', context)