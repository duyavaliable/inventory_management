from django.db import models
from django.contrib.auth.models import User

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
	category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True)
	product_group = models.ForeignKey(ProductGroup, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Nhóm hàng")
	date_created = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	date_stocked = models.DateField(verbose_name="Ngày nhập kho", null=True, blank=True)
	date_sold = models.DateField(verbose_name="Ngày xuất kho", null=True, blank=True)

	def __str__(self):
		return self.name
