from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, InventoryItemForm, ProductGroupForm
from .models import InventoryItem, Category, ProductGroup
from inventory_management.settings import LOW_QUANTITY
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy

class Index(TemplateView):
	template_name = 'inventory/index.html'

class Dashboard(LoginRequiredMixin, View):
	def get(self, request):
		search_query = request.GET.get('q', None)
		selected_group_ids = request.GET.getlist('product_group_filter')
		stock_filter = request.GET.get('stock_filter', None)

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
		#chuan bi form de tao nhom hang moi trong modal
		product_group_form = ProductGroupForm()
		
		#Sap xep ket qua cuoi cung
		items = user_items.order_by('id')
  
		context = { 
			'items': items,
			'low_inventory_ids': low_inventory_ids, # Giữ nguyên từ code gốc
			'all_product_groups': all_product_groups,
			'selected_group_ids': selected_group_ids_int, # Truyền lại ID đã chọn (dạng số nguyên)
			'product_group_form': product_group_form,
			'search_query': search_query,  
			'stock_filter': stock_filter,  
		} 	

		return render(request, 'inventory/dashboard.html', context)

class SignUpView(View):
	def get(self, request):
		form = UserRegisterForm()
		return render(request, 'inventory/signup.html', {'form': form})

	def post(self, request):
		form = UserRegisterForm(request.POST)

		if form.is_valid():
			form.save()
			user = authenticate(
				username=form.cleaned_data['username'],
				password=form.cleaned_data['password1']
			)

			login(request, user)
			return redirect('index')

		return render(request, 'inventory/signup.html', {'form': form})

class AddItem(LoginRequiredMixin, CreateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('dashboard')

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
	success_url = reverse_lazy('dashboard')

class DeleteItem(LoginRequiredMixin, DeleteView):
	model = InventoryItem
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('dashboard')
	context_object_name = 'item'

class ProductGroupCreateView(LoginRequiredMixin, CreateView):
	model = ProductGroup
	form_class = ProductGroupForm
	template_name = 'inventory/partials/productgroup_form_modal.html'
	success_url = reverse_lazy('dashboard')

	def form_valid(self, form):
		response = super().form_valid(form)
		messages.success(self.request, f"Nhóm hàng '{form.instance.name}' đã được tạo thành công.")
		return response

#Xoa nhom hang
class ProductGroupDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductGroup
    success_url = reverse_lazy('dashboard')

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
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Nhóm hàng '{form.instance.name}' đã được cập nhật thành công.")
        return response