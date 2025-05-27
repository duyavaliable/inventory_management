from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
	name = models.CharField(max_length=200)

	class Meta:
		verbose_name_plural = 'categories'

	def __str__(self):
		return self.name

class ProductGroup(models.Model):
	name = models.CharField(max_length=200, unique=True, verbose_name="Tên nhóm hàng")
	parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.SET_NULL, verbose_name="Nhóm hàng")

	class Meta:
		verbose_name = 'Nhóm hàng'
		

	def __str__(self):
		return self.name

class InventoryItem(models.Model):
	name = models.CharField(max_length=200)
	sku = models.CharField(max_length=50, unique=True, verbose_name="Mã sản phẩm")
	quantity = models.IntegerField()
	selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá bán")
	cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Giá vốn")
	weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Trọng lượng (gram)")
	min_stock = models.IntegerField(default=0, verbose_name="Tồn kho tối thiểu")
	max_stock = models.IntegerField(default=10, verbose_name="Tồn kho tối đa")
	supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Nhà cung cấp")
	category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True)
	product_group = models.ForeignKey(ProductGroup, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Nhóm hàng")
	date_created = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	date_stocked = models.DateField(verbose_name="Ngày nhập kho", null=True, blank=True)
	date_sold = models.DateField(verbose_name="Ngày xuất kho", null=True, blank=True)

	def __str__(self):
		return self.name

class UserProfile(models.Model):
    # Sử dụng OneToOneField để liên kết với User với khóa chính (ID), không phải email
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Thông tin người dùng
    display_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='Tên hiển thị')
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='Số điện thoại')
    birth_date = models.DateField(blank=True, null=True, verbose_name='Ngày sinh')
    
    def __str__(self):
        return f"Hồ sơ của {self.user.username}"

# Tự động tạo UserProfile khi tạo mới User
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Đảm bảo profile luôn tồn tại
        instance.profile.save()

class Supplier(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên nhà cung cấp")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Nhà cung cấp"
        verbose_name_plural = "Nhà cung cấp"
    
    def __str__(self):
        return self.name