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
from django.shortcuts import redirect 
from django.contrib import messages
from payos import PayOS, ItemData, PaymentData
import json
import time
from decimal import Decimal
from django.db.models import Q, Sum, F, DecimalField
from django.db import IntegrityError, transaction
from .forms import ( UserUpdateForm, UserProfileUpdateForm, 
                    SupplierForm, CustomerForm, 
)
from .models import UserProfile, Supplier, Order, Customer, InventoryItem , OrderItem, Order
from django.contrib.messages import get_messages as django_get_messages
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator 
from django.views.decorators.csrf import csrf_exempt 
from django.shortcuts import get_object_or_404
import calendar 



# Khởi tạo PayOS client
payos_client = PayOS(client_id=settings.PAYOS_CLIENT_ID,
                     api_key=settings.PAYOS_API_KEY,
                     checksum_key=settings.PAYOS_CHECKSUM_KEY)

@method_decorator(csrf_exempt, name='dispatch')
class CreatePaymentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        print("--- CreatePaymentView: Bắt đầu xử lý POST request ---") # DEBUG
        try:
            cart_data_json = request.POST.get('cart_items_json')
            print(f"cart_items_json từ POST: {cart_data_json}") # DEBUG
            if not cart_data_json:
                messages.error(request, "Dữ liệu giỏ hàng không hợp lệ.")
                print("Lỗi: cart_items_json rỗng hoặc None. Chuyển hướng về customer-shop.") # DEBUG
                return redirect('customer-shop')
            
            cart_items_data = json.loads(cart_data_json)
            print(f"cart_items_data sau khi parse JSON: {cart_items_data}") # DEBUG
            
            total_amount_for_payos_calc = 0 # Đây là int, tổng tiền cho PayOS
            list_of_item_data_objects = []
            processed_order_items_for_db = []
            order_code_int = int(time.time()) # Sử dụng tên biến rõ ràng cho order_code dạng int
            print(f"order_code_int được tạo: {order_code_int}") # DEBUG
            
            if not cart_items_data:
                messages.error(request, "Giỏ hàng trống.")
                print("Lỗi: cart_items_data rỗng. Chuyển hướng về customer-shop.") # DEBUG
                return redirect('customer-shop')

            with transaction.atomic(): 
                # ... (vòng lặp xử lý cart_items_data giữ nguyên) ...
                print("--- Bắt đầu vòng lặp xử lý các mục trong giỏ hàng ---") # DEBUG
                for product_id_str, item_detail in cart_items_data.items():
                    try:
                        product_id = int(product_id_str)
                        product = InventoryItem.objects.get(id=product_id)
                        item_price_for_payos = int(product.selling_price) # Giá cho PayOS là int
                        item_quantity = int(item_detail.get('quantity', 0))

                        if item_quantity <= 0:
                            continue
                        
                        if product.quantity < item_quantity:
                            messages.error(request, f'Sản phẩm "{product.name}" không đủ số lượng tồn kho (còn {product.quantity}).')
                            return redirect('customer-shop')

                        total_amount_for_payos_calc += item_price_for_payos * item_quantity
                        payos_item_obj = ItemData(name=product.name, quantity=item_quantity, price=item_price_for_payos)
                        list_of_item_data_objects.append(payos_item_obj)
                        processed_order_items_for_db.append({
                            "product_instance": product,
                            "quantity": item_quantity,
                            "price": product.selling_price # Lưu giá gốc (có thể là Decimal) cho DB
                        })
                    except InventoryItem.DoesNotExist:
                        messages.error(request, f'Sản phẩm với ID {product_id} không tồn tại.')
                        return redirect('customer-shop')
                    except ValueError:
                        messages.error(request, f'Dữ liệu không hợp lệ cho sản phẩm ID {product_id}.')
                        return redirect('customer-shop')

                if not list_of_item_data_objects:
                    messages.error(request, "Không có sản phẩm hợp lệ trong giỏ hàng.")
                    return redirect('customer-shop')
                
                # ... (logic lấy/tạo customer giữ nguyên) ...
                customer = None
                try:
                    user_profile = UserProfile.objects.get(user=request.user)
                    customer_phone = user_profile.phone_number
                    customer_name = user_profile.display_name or request.user.get_full_name() or request.user.username
                    if customer_phone:
                        customer, created = Customer.objects.get_or_create(
                            phone=customer_phone,
                            defaults={'name': customer_name, 'code': f"CUST{int(time.time())}", 'total_sales': Decimal('0.00')} # Khởi tạo Decimal
                        )
                        if not created and customer.name != customer_name: 
                            customer.name = customer_name
                            customer.save(update_fields=['name'])
                    else: 
                        customer, created = Customer.objects.get_or_create(
                            name=customer_name, 
                            defaults={'code': f"CUST{int(time.time())}{request.user.id}", 'total_sales': Decimal('0.00')} # Khởi tạo Decimal
                        )
                except UserProfile.DoesNotExist:
                    customer_name = request.user.get_full_name() or request.user.username
                    customer, created = Customer.objects.get_or_create(
                        name=customer_name,
                        defaults={'code': f"CUST{int(time.time())}{request.user.id}", 'total_sales': Decimal('0.00')} # Khởi tạo Decimal
                    )
                except Exception as e:
                    print(f"Lỗi khi lấy/tạo khách hàng: {e}")
                    messages.error(request, "Lỗi khi xử lý thông tin khách hàng.")
                    return redirect('customer-shop')
                
                if not customer:
                    messages.error(request, "Không thể xác định thông tin khách hàng.")
                    return redirect('customer-shop')

                new_order = Order.objects.create(
                    user=request.user,
                    customer=customer,
                    order_code=str(order_code_int), # Lưu order_code dưới dạng chuỗi
                    total_amount=Decimal(total_amount_for_payos_calc), # Chuyển sang Decimal nếu model field là DecimalField
                    status='pending_payment',
                    payment_method='payos', 
                    amount_paid=Decimal('0.00'), # Khởi tạo Decimal
                )

                for item_data_db in processed_order_items_for_db:
                    OrderItem.objects.create(
                        order=new_order,
                        product=item_data_db['product_instance'],
                        quantity=item_data_db['quantity'],
                        price=Decimal(item_data_db['price']) # Đảm bảo price là Decimal nếu model field là DecimalField
                    )

                payos_payment_data_object = PaymentData(
                    orderCode=order_code_int, # Gửi order_code dạng int cho PayOS
                    amount=total_amount_for_payos_calc,
                    description=f"Thanh toan SP {order_code_int}",
                    items=list_of_item_data_objects,
                    cancelUrl=request.build_absolute_uri(reverse('payment-cancel')),
                    returnUrl=request.build_absolute_uri(reverse('payment-return'))
                )
            
                print(f"Dữ liệu gửi đến PayOS: orderCode={order_code_int}, amount={total_amount_for_payos_calc}, items_count={len(list_of_item_data_objects)}") # DEBUG
                payos_response = None 
                try:
                    payos_response = payos_client.createPaymentLink(payos_payment_data_object)
                    print(f"Phản hồi thô từ PayOS SDK (createPaymentLink): {payos_response}") # DEBUG
                except Exception as e_payos_sdk:
                    print(f"LỖI khi gọi payos_client.createPaymentLink: {e_payos_sdk}") # DEBUG
                    messages.error(request, f"Lỗi kết nối hoặc tạo link với PayOS: {e_payos_sdk}")
                    if 'new_order' in locals() and new_order.pk:
                        new_order.status = 'payment_failed'
                        new_order.save(update_fields=['status'])
                    return redirect('customer-shop')

                # SỬA ĐỔI CÁCH KIỂM TRA VÀ TRUY CẬP THUỘC TÍNH
                if payos_response and hasattr(payos_response, 'checkoutUrl') and payos_response.checkoutUrl:
                    print(f"PayOS trả về checkoutUrl: {payos_response.checkoutUrl}") # DEBUG
                    if hasattr(payos_response, 'paymentLinkId'):
                        new_order.payos_payment_link_id = payos_response.paymentLinkId
                        new_order.save(update_fields=['payos_payment_link_id'])
                        print(f"Đã lưu paymentLinkId: {new_order.payos_payment_link_id}") # DEBUG
                    else:
                        print("Cảnh báo: Không tìm thấy paymentLinkId trong phản hồi từ PayOS.") # DEBUG
                    
                    print(f"Chuẩn bị chuyển hướng đến PayOS: {payos_response.checkoutUrl}") # DEBUG
                    return HttpResponseRedirect(payos_response.checkoutUrl)
                else:
                    error_desc = "Không thể tạo link thanh toán PayOS hoặc không có checkoutUrl."
                    if payos_response and hasattr(payos_response, 'message') and payos_response.message: # Giả sử lỗi được trả về trong thuộc tính 'message' hoặc 'desc'
                        error_desc = payos_response.message
                    elif payos_response and hasattr(payos_response, 'desc') and payos_response.desc:
                         error_desc = payos_response.desc
                    elif payos_response is None:
                        error_desc = "Không nhận được phản hồi từ PayOS SDK."
                    
                    print(f"Lỗi từ PayOS hoặc không có checkoutUrl. Phản hồi: {payos_response}, Mô tả lỗi: {error_desc}") # DEBUG
                    messages.error(request, f"Lỗi PayOS: {error_desc}")
                    # Chỉ cập nhật trạng thái đơn hàng nếu new_order đã được tạo
                    if 'new_order' in locals() and new_order.pk:
                        new_order.status = 'payment_failed' 
                        new_order.save(update_fields=['status'])
                    return redirect('customer-shop')

        except json.JSONDecodeError:
            messages.error(request, "Dữ liệu giỏ hàng không hợp lệ (JSON).")
            return redirect('customer-shop')
        except Exception as e:
            print(f"Error in CreatePaymentView: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Lỗi hệ thống khi tạo thanh toán. Vui lòng thử lại.')
            return redirect('customer-shop')

class PaymentReturnView(View): 
    def get(self, request, *args, **kwargs):
        order_code_str_from_payos = request.GET.get('orderCode') # Đây là chuỗi, ví dụ "1678886400"
        status_from_payos = request.GET.get('status')

        if not order_code_str_from_payos:
            messages.error(request, "Thiếu thông tin đơn hàng từ cổng thanh toán.")
            return redirect('customer-shop') 

        try:
            # Truy vấn Order bằng order_code (dạng chuỗi) đã lưu
            order = Order.objects.get(order_code=order_code_str_from_payos)
            
            if payos_client:
                try:
                    # Gọi API PayOS với order_code dạng int
                    payment_info = payos_client.getPaymentLinkInformation(int(order_code_str_from_payos))
                    if isinstance(payment_info, dict):
                        actual_payos_status = payment_info.get('status')
                        if actual_payos_status:
                            status_from_payos = actual_payos_status # Ưu tiên trạng thái từ API
                            order.payos_payment_status = actual_payos_status
                except Exception as e_payos_check:
                    print(f"Lỗi khi gọi getPaymentLinkInformation cho order {order_code_str_from_payos}: {e_payos_check}")
                    # Tiếp tục xử lý với status từ query param nếu API call lỗi, nhưng log lại
            
            if status_from_payos == 'PAID':
                if order.status not in ['paid', 'completed', 'processing']: # Thêm 'processing' để tránh ghi đè nếu webhook đã chạy
                    order.status = 'paid' 
                    order.amount_paid = order.total_amount # total_amount đã là Decimal
                    order.save(update_fields=['status', 'amount_paid','payos_payment_status'])

                    if order.customer:
                        order.customer.total_sales = (order.customer.total_sales or Decimal('0.00')) + order.total_amount
                        order.customer.save(update_fields=['total_sales'])
                        
                    with transaction.atomic():
                        for item in order.items.all():
                            product_to_update = InventoryItem.objects.select_for_update().get(id=item.product.id)
                            if product_to_update.quantity >= item.quantity:
                                product_to_update.quantity -= item.quantity
                                product_to_update.save(update_fields=['quantity'])
                            else:
                                messages.warning(request, f"Sản phẩm {item.product.name} không đủ tồn kho để hoàn tất đơn hàng.")
                                print(f"Cảnh báo tồn kho: SP ID {item.product.id} cho đơn {order.order_code}. Cần {item.quantity}, còn {product_to_update.quantity}")
                                # Cân nhắc: có nên đổi trạng thái đơn hàng ở đây nếu không đủ hàng?
                    
                    messages.success(request, f"Thanh toán cho đơn hàng {order_code_str_from_payos} thành công!")
                    if 'cartItems' in request.session: # Xóa cartItems khỏi session
                        del request.session['cartItems']
                        request.session.modified = True
                    # Chuyển hướng đến trang chi tiết đơn hàng hoặc trang thành công tùy chỉnh
                    # return redirect('order-detail', pk=order.pk) # Ví dụ
                else:
                    messages.info(request, f"Đơn hàng {order_code_str_from_payos} đã được xử lý thanh toán trước đó.")
                return redirect('order-list') # Hoặc trang chi tiết đơn hàng
            
            elif status_from_payos == 'CANCELLED':
                if order.status not in ['paid', 'completed', 'cancelled', 'processing']:
                    order.status = 'cancelled'
                    order.payos_payment_status = 'CANCELLED' # Đảm bảo cập nhật payos_payment_status
                    order.save(update_fields=['status','payos_payment_status']) 
                messages.warning(request, f"Thanh toán cho đơn hàng {order_code_str_from_payos} đã bị hủy.")
                return redirect('customer-shop') # Hoặc trang giỏ hàng
            
            else: # PENDING, EXPIRED, FAILED
                new_status_map = {
                    'PENDING': 'pending_payment', # Hoặc một trạng thái 'chờ xác nhận' khác
                    'EXPIRED': 'payment_failed',
                    'FAILED': 'payment_failed',
                }
                new_order_status = new_status_map.get(status_from_payos, 'payment_failed')

                if order.status not in ['paid', 'completed', 'cancelled', 'processing'] and order.status != new_order_status:
                    order.status = new_order_status
                    # order.payos_payment_status đã được cập nhật ở trên
                    order.save(update_fields=['status','payos_payment_status'])

                if new_order_status == 'payment_failed' and status_from_payos == 'FAILED':
                    messages.error(request, f"Thanh toán cho đơn hàng {order_code_str_from_payos} đã thất bại.")
                elif new_order_status == 'payment_failed' and status_from_payos == 'EXPIRED':
                    messages.warning(request, f"Phiên thanh toán cho đơn hàng {order_code_str_from_payos} đã hết hạn.")
                else: # PENDING
                    messages.info(request, f"Đơn hàng {order_code_str_from_payos} đang chờ xử lý thanh toán (Trạng thái PayOS: {status_from_payos}).")
                
                return redirect('customer-shop') # Hoặc trang chi tiết đơn hàng với thông báo

        except Order.DoesNotExist:
            messages.error(request, f"Không tìm thấy đơn hàng với mã {order_code_str_from_payos}.")
            return redirect('customer-shop')
        except Exception as e:
            print(f"Lỗi khi xử lý trả về từ PayOS: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, "Có lỗi xảy ra khi xử lý thanh toán. Vui lòng liên hệ hỗ trợ.")
            return redirect('customer-shop')
        
@method_decorator(csrf_exempt, name='dispatch')
class PaymentCancelView(View): 
    def get(self, request, *args, **kwargs):
        order_code_from_payos = request.GET.get('orderCode')
        
        if not order_code_from_payos:
            messages.warning(request, "Hủy thanh toán không rõ đơn hàng.")
            return redirect('customer-shop')
        try:
            order = Order.objects.get(order_code=order_code_from_payos)
            
            # Cập nhật trạng thái đơn hàng nếu đang chờ thanh toán
            if order.status == 'pending_payment':
                order.status = 'cancelled'
                order.payos_payment_status = 'CANCELLED'
                order.save(update_fields=['status', 'payos_payment_status'])
                messages.info(request, f"Bạn đã hủy thanh toán cho đơn hàng {order_code_from_payos}.")
            else:
                messages.info(request, f"Thanh toán cho đơn hàng {order_code_from_payos} đã được xử lý trước đó với trạng thái {order.get_status_display()}.")
                
            return redirect('customer-shop')
            
        except Order.DoesNotExist:
            messages.error(request, f"Không tìm thấy đơn hàng với mã {order_code_from_payos}.")
            return redirect('customer-shop')
            
        except Exception as e:
            print(f"Lỗi khi xử lý hủy từ PayOS: {e}")
            messages.error(request, "Có lỗi xảy ra khi xử lý hủy thanh toán. Vui lòng liên hệ hỗ trợ.")
            return redirect('customer-shop')


@method_decorator(csrf_exempt, name='dispatch')
class PayOSWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            webhook_data = json.loads(request.body)
            print(f"Nhận dữ liệu webhook từ PayOS: {webhook_data}")
            
            transaction_data = webhook_data.get('data', webhook_data)
            payos_order_code_int = transaction_data.get('orderCode') # Đây là int từ PayOS
            status = transaction_data.get('status')
            
            if not payos_order_code_int or not status:
                return JsonResponse({"code": "03", "desc": "Thiếu dữ liệu"}, status=200)
                
            with transaction.atomic():
                try:
                    # Truy vấn Order bằng order_code (dạng chuỗi) sau khi chuyển đổi từ int
                    order = Order.objects.select_for_update().get(order_code=str(payos_order_code_int))
                except Order.DoesNotExist:
                    print(f"Webhook: Không tìm thấy đơn hàng với order_code (str): {str(payos_order_code_int)}")
                    return JsonResponse({"code": "04", "desc": "Không tìm thấy đơn hàng"}, status=200)
                    
                if order.payos_payment_status == status:
                    if (status == 'PAID' and order.status in ['paid', 'completed', 'processing']) or \
                       (status in ['CANCELLED', 'EXPIRED', 'FAILED'] and order.status in ['cancelled', 'payment_failed', 'pending_payment']): # Thêm pending_payment cho trường hợp hủy/hết hạn
                        print(f"Webhook: Đơn hàng {order.order_code} đã xử lý trạng thái {status} trước đó.")
                        return JsonResponse({"code": "00", "desc": "Đã xử lý trước đó"}, status=200)
                        
                order.payos_payment_status = status
                
                if status == 'PAID':
                    # Chỉ cập nhật nếu đơn hàng đang chờ thanh toán hoặc xử lý ban đầu
                    if order.status in ['pending_payment', 'payment_failed']: # Cho phép thử lại nếu trước đó failed
                        order.status = 'processing' # Trạng thái chờ xử lý/giao hàng
                        order.amount_paid = order.total_amount # total_amount đã là Decimal
                        
                        all_items_sufficient = True
                        for item in order.items.all():
                            product = InventoryItem.objects.select_for_update().get(id=item.product.id)
                            if product.quantity >= item.quantity:
                                product.quantity -= item.quantity
                                product.save(update_fields=['quantity'])
                            else:
                                print(f"CẢNH BÁO WEBHOOK: Sản phẩm {product.id} không đủ số lượng cho đơn hàng {order.order_code}")
                                order.status = 'payment_failed' # Hoặc một trạng thái đặc biệt như 'paid_stock_issue'
                                order.payos_payment_status = 'PAID_STOCK_ISSUE' # Ghi nhận vấn đề
                                all_items_sufficient = False
                                break
                                
                        if all_items_sufficient and order.customer:
                            order.customer.total_sales = (order.customer.total_sales or Decimal('0.00')) + order.total_amount
                            order.customer.save(update_fields=['total_sales'])
                
                elif status == 'CANCELLED':
                    if order.status in ['pending_payment', 'processing']: # Nếu đang xử lý mà bị hủy (hiếm)
                        order.status = 'cancelled'
                
                elif status in ['EXPIRED', 'FAILED']:
                    if order.status in ['pending_payment', 'processing']:
                        order.status = 'payment_failed'
                
                order.save() # Lưu các thay đổi trạng thái
                
            return JsonResponse({"code": "00", "desc": "Xử lý webhook thành công"}, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({"code": "01", "desc": "Dữ liệu JSON không hợp lệ"}, status=400)
        
        except Exception as e:
            print(f"Lỗi xử lý webhook PayOS: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"code": "02", "desc": "Lỗi server"}, status=200)


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
            role = request.POST.get('role', 'manager')
            profile.role = role
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
    
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'inventory/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        # Nếu người dùng là superuser hoặc staff (quản lý), hiển thị tất cả đơn hàng
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Order.objects.all().order_by('-order_date')
        # Ngược lại, nếu là khách hàng thông thường, chỉ hiển thị đơn hàng của họ
        return Order.objects.filter(user=self.request.user).order_by('-order_date')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Danh sách đơn hàng'
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
    template_name = 'inventory/customer_confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object() 
        customer_name = self.object.name
        success_message = f'Khách hàng "{customer_name}" đã được xóa thành công!'
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, success_message)
        return response

#tong quan 
class DashboardOverviewView(LoginRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year

        # 1. Kết quả bán hàng hôm nay (giữ nguyên logic đã sửa với order_date)
        daily_orders_base_query = Order.objects.filter(
            user=request.user, 
            order_date__date=today,
            status__in=['paid', 'completed', 'processing']
        )
        
        daily_revenue_val = daily_orders_base_query.aggregate(
            total_revenue=Sum('total_amount', default=Decimal(0))
        )['total_revenue']
        
        daily_orders_count_val = daily_orders_base_query.count()

        daily_cogs_val = OrderItem.objects.filter(
            order__in=daily_orders_base_query,
            product__cost_price__isnull=False
        ).aggregate(
            total_cogs=Sum(F('quantity') * F('product__cost_price'), output_field=DecimalField(), default=Decimal(0))
        )['total_cogs']

        daily_net_revenue_val = daily_revenue_val - daily_cogs_val
        daily_net_revenue_margin_percent_val = (daily_net_revenue_val / daily_revenue_val * 100) if daily_revenue_val > 0 else Decimal(0)

        daily_sales = {
            'revenue': daily_revenue_val,
            'orders_count': daily_orders_count_val,
            'returns': 0,
            'net_revenue': daily_net_revenue_val,
            'net_revenue_percent': daily_net_revenue_margin_percent_val,
        }

        # 2. Doanh thu thuần theo tháng (biểu đồ) (giữ nguyên logic đã sửa với order_date)
        num_days_in_month = calendar.monthrange(current_year, current_month)[1]
        daily_net_revenue_chart_data = [0.0] * num_days_in_month

        orders_in_month = Order.objects.filter(
            user=request.user,
            order_date__year=current_year,
            order_date__month=current_month,
            status__in=['paid', 'completed', 'processing']
        )

        for day_num in range(1, num_days_in_month + 1):
            day_date = timezone.datetime(current_year, current_month, day_num).date()
            
            revenue_for_day = orders_in_month.filter(order_date__date=day_date).aggregate(
                total=Sum('total_amount', default=Decimal(0))
            )['total']
            
            cogs_for_day = OrderItem.objects.filter(
                order__in=orders_in_month.filter(order_date__date=day_date),
                product__cost_price__isnull=False
            ).aggregate(
                total_cogs=Sum(F('quantity') * F('product__cost_price'), output_field=DecimalField(), default=Decimal(0))
            )['total_cogs']
            
            net_revenue_for_day = revenue_for_day - cogs_for_day
            daily_net_revenue_chart_data[day_num - 1] = float(net_revenue_for_day / Decimal('1000000'))
        
        # 3. Top 10 hàng bán chạy (theo doanh thu) (giữ nguyên logic)
        top_products_data = OrderItem.objects.filter(
            order__user=request.user,
            order__status__in=['paid', 'completed', 'processing']
        ).values(
            'product__name'
        ).annotate(
            total_revenue_for_product=Sum(F('quantity') * F('price'))
        ).order_by(
            '-total_revenue_for_product'
        )[:10]
        
        top_products_chart_labels = [item['product__name'] for item in top_products_data]
        top_products_chart_values = [float(item['total_revenue_for_product'] / Decimal('1000000')) for item in top_products_data]

        # 4. Top 10 khách mua nhiều nhất (theo tổng chi tiêu) - SỬA ĐỔI Ở ĐÂY
        top_customers_data = Order.objects.filter(
            user=request.user, # Lọc đơn hàng theo user hiện tại (manager)
            status__in=['paid', 'completed', 'processing'],
            customer__isnull=False 
        ).values(
            'customer__name' # Chỉ lấy tên từ model Customer
        ).annotate(
            total_spent_by_customer=Sum('total_amount')
        ).order_by(
            '-total_spent_by_customer'
        )[:10]

        top_customers_chart_labels = []
        for item in top_customers_data:
            # Lấy tên khách hàng trực tiếp từ kết quả truy vấn
            name = item.get('customer__name') or "Khách vãng lai" 
            top_customers_chart_labels.append(name)
        
        # Lấy giá trị chi tiêu
        top_customers_chart_values = [float(item['total_spent_by_customer'] / Decimal('1000000')) for item in top_customers_data]

        context = {
            'current_url_name': 'dashboard',
            'daily_sales': daily_sales,
            'daily_data': json.dumps(daily_net_revenue_chart_data),
            'top_products_labels': json.dumps(top_products_chart_labels),
            'top_products_values': json.dumps(top_products_chart_values),
            'top_customers_labels': json.dumps(top_customers_chart_labels),
            'top_customers_values': json.dumps(top_customers_chart_values),
        }
        return render(request, 'inventory/dashboard_overview.html', context)
    
class CustomerShopView(LoginRequiredMixin, View):
    def get(self, request):
        # Lấy danh sách sản phẩm
        products = InventoryItem.objects.all()
        context = {
            'products': products
        }
        return render(request, 'inventory/customer-shop.html', context)