from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Category, InventoryItem, ProductGroup

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        help_texts = {
            'username': 'Bắt buộc. Tối đa 150 ký tự. Chỉ chấp nhận chữ cái, số và @/./+/-/_.',
        }
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        # Việt hóa thông báo cho password
        self.fields['password1'].help_text = '''
            <ul>
                <li>Mật khẩu của bạn không được giống thông tin cá nhân.</li>
                <li>Mật khẩu phải chứa ít nhất 8 ký tự.</li>
                <li>Mật khẩu không được phổ biến, dễ đoán.</li>
                <li>Mật khẩu không được chứa toàn số.</li>
            </ul>
        '''
        self.fields['password2'].help_text = 'Nhập lại mật khẩu để xác nhận.'

class InventoryItemForm(forms.ModelForm):
	category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, label='Danh mục', empty_label="Chọn danh mục")
	product_group = forms.ModelChoiceField(queryset=ProductGroup.objects.all(), required=False, label='Nhóm hàng', empty_label="Chọn nhóm hàng")
 
	class Meta:
		model = InventoryItem
		fields = ['name','sku', 'quantity', 'selling_price', 'category', 'product_group']
		labels = {
            'name': 'Tên',
            'sku': 'Mã sản phẩm',
            'quantity': 'Số lượng',
            'selling_price': 'Giá bán',
        }

class ProductGroupForm(forms.ModelForm):
	class Meta:
		model = ProductGroup
		fields = ['name']
		labels = {
			'name': 'Tên nhóm hàng',
		}
		widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Nhập tên nhóm hàng'}),
        }