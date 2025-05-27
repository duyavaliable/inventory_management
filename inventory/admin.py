from django.contrib import admin
from .models import InventoryItem, Category

class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'quantity', 'selling_price', 'category', 'user', 'date_stocked', 'date_sold', 'date_created')
    search_fields = ('name', 'sku')
    list_filter = ('category', 'date_stocked', 'date_sold')
    
admin.site.register(InventoryItem)
admin.site.register(Category)
