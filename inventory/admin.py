from django.contrib import admin
from .models import InventoryItem, Category, ProductGroup

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

admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductGroup, ProductGroupAdmin)
