from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (   Category, InventoryItem, ProductGroup, 
                        UserProfile, Supplier, Order,
                        Customer
)
from django.contrib.auth.forms import PasswordChangeForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    display_name = forms.CharField(
        max_length=150,
        required=False,
        label='Tên hiển thị',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        label='Số điện thoại',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email','display_name','phone_number','password1', 'password2']
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
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), required=False, label='Nhà cung cấp', empty_label="Chọn nhà cung cấp")
        
    class Meta:
        model = InventoryItem
        fields = ['name', 'sku', 'quantity', 'cost_price', 'selling_price', 'weight', 
                 'min_stock', 'max_stock', 'category', 'product_group', 'supplier', 
                 'date_stocked', 'date_sold']
        labels = {
            'name': 'Tên',
            'sku': 'Mã sản phẩm',
            'quantity': 'Số lượng',
            'cost_price': 'Giá vốn',
            'selling_price': 'Giá bán',
            'weight': 'Trọng lượng (gram)',
            'min_stock': 'Tồn kho tối thiểu',
            'max_stock': 'Tồn kho tối đa',
            'date_stocked': 'Ngày nhập kho',
            'date_sold': 'Ngày xuất kho',
        }
        widgets = {
            'date_stocked': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_sold': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['email']  

#Cập nhật thông tin cá nhân người dùng         
class UserProfileUpdateForm(forms.ModelForm):
    display_name = forms.CharField(
        max_length=150, 
        required=False, 
        label='Tên người dùng',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=15, 
        required=False, 
        label='Điện thoại',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    birth_date = forms.DateField(
        required=False, 
        label='Ngày sinh',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = UserProfile
        fields = ['display_name', 'phone_number', 'birth_date']
        
#Chỉnh sửa mật khẩu tài khoản
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu hiện tại'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu mới'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nhập lại mật khẩu mới'
        })
        # Việt hoá thông báo trợ giúp
        self.fields['new_password1'].help_text = '''
        <ul>
            <li>Mật khẩu của bạn không được giống thông tin cá nhân.</li>
            <li>Mật khẩu phải chứa ít nhất 8 ký tự.</li>
            <li>Mật khẩu không được phổ biến, dễ đoán.</li>
            <li>Mật khẩu không được chứa toàn số.</li>
        </ul>
        '''

#them nha cung cap
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'address']
        labels = {
            'name': 'Tên nhà cung cấp',
            'phone': 'Số điện thoại',
            'address': 'Địa chỉ',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên nhà cung cấp'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số điện thoại'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Nhập địa chỉ'}),
        }

#danh sach don hang
class OrderForm(forms.ModelForm):
    # Nếu bạn muốn cho phép người dùng chọn sản phẩm và số lượng,
    # bạn có thể cần xử lý phức tạp hơn, ví dụ dùng formsets cho OrderItem.
    # Ví dụ đơn giản này chỉ tập trung vào việc tạo Order.
    # Bạn có thể thêm các trường tùy chỉnh hoặc widget tại đây nếu cần.
    class Meta:
        model = Order
        fields = ['total_amount'] # Chỉ ví dụ, bạn sẽ cần các trường phù hợp
                                  # Ví dụ: 'customer_name', 'shipping_address', etc.
                                  # Trường 'user' và 'order_date' thường được xử lý tự động trong view.
        # widgets = {
        #     'some_field': forms.TextInput(attrs={'class': 'form-control'}),
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tùy chỉnh các trường form nếu cần
        # Ví dụ: self.fields['total_amount'].widget.attrs.update({'class': 'form-control'})

#danh sach khach hang 
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['code', 'name', 'phone']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập mã khách hàng'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên khách hàng'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số điện thoại'}),
        }