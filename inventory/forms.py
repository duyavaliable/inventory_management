from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Category, InventoryItem

class UserRegisterForm(UserCreationForm):
	email = forms.EmailField()

	class Meta:
		model = User
		fields = ['username', 'email', 'password1', 'password2']

class InventoryItemForm(forms.ModelForm):
	category = forms.ModelChoiceField(queryset=Category.objects.all(), initial=0, label='Danh mục')
	class Meta:
		model = InventoryItem
		fields = ['name','sku', 'quantity', 'selling_price', 'category']
		labels = {
            'name': 'Tên',
            'sku': 'Mã sản phẩm',
            'quantity': 'Số lượng',
            'selling_price': 'Giá bán',
        }