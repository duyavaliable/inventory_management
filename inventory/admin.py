from django.contrib import admin
from .models import (   InventoryItem, Category, 
                        ProductGroup, UserProfile, 
                        Supplier, Order, Customer
)

class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'quantity', 'selling_price', 'category', 'product_group', 'user', 'date_stocked', 'date_sold', 'date_created')
    search_fields = ('name', 'sku')
    list_filter = ('category', 'product_group', 'date_stocked', 'date_sold')

#quan ly nha cung cap
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address')
    search_fields = ('name', 'phone')

#danh sach don hang
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_code', 'customer', 'order_date', 'total_amount', 'amount_paid', 'amount_due', 'status', 'user')
    list_filter = ('status', 'order_date')
    search_fields = ('order_code', 'customer__name', 'user__username')
    
#Danh sach khach hang
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'phone', 'total_sales')
    search_fields = ('code', 'name', 'phone')
    list_filter = ('code', 'name')

admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductGroup, ProductGroupAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(UserProfile)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Customer, CustomerAdmin)
