from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Product, Category, Brand, ProductImage, ProductVariant, Review, Cart, CartItem, Order, OrderItem, ContactMessage
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import uuid
from decimal import Decimal
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
import random
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

import requests
import json
import hmac
import hashlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def product_list(request):
    """Display all products with filtering and pagination"""
    products = Product.objects.filter(is_active=True)
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Filter by brand
    brand_slug = request.GET.get('brand')
    if brand_slug:
        brand = get_object_or_404(Brand, slug=brand_slug)
        products = products.filter(brand=brand)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Sort
    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'bestseller':
        products = products.filter(is_bestseller=True)
    else:  # featured
        products = products.filter(is_featured=True)
    
    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    context = {
        'products': products_page,
        'categories': Category.objects.filter(is_active=True, parent=None),
        'brands': Brand.objects.all(),
        'total_products': products.count(),
    }
    
    return render(request, 'products/product_list.html', context)

    
def product_detail(request, slug):
    """Display single product details"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get product images
    product_images = product.images.all()
    if not product_images and product.main_image:
        product_images = [{'image': product.main_image, 'is_primary': True}]
    
    # Get product variants (size, color)
    variants = product.variants.all()
    
    # Get related products (same category)
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Get reviews
    reviews = product.reviews.filter(is_approved=True)[:5]
    
    context = {
        'product': product,
        'product_images': product_images,
        'variants': variants,
        'related_products': related_products,
        'reviews': reviews,
        'reviews_count': product.reviews.filter(is_approved=True).count(),
    }
    
    return render(request, 'products/product_detail.html', context)
# popup 
def product_quick_view(request, product_id):
    """AJAX view for quick product preview"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        data = {
            'id': product.id,
            'slug': product.slug, 
            'name': product.name,
            'price': f'${product.price}',
            'original_price': f'${product.compare_price}' if product.compare_price else None,
            'discount': f'{product.discount_percentage}%' if product.discount_percentage > 0 else None,
            'description': product.short_description or product.description[:200],
            'category': product.category.name,
            'stock': 'In Stock' if product.stock > 0 else 'Out of Stock',
            'image': product.main_image.url if product.main_image else '/static/images/placeholder.jpg',
            'slug': product.slug,
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)



def get_cart(request):
    session_key = request.session.get('cart_session_key')
    if not session_key:
        session_key = str(uuid.uuid4())
        request.session['cart_session_key'] = session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    else:
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def cart_detail(request):
    cart = get_cart(request)
    cart_items = cart.items.all().select_related('product')
    subtotal = cart.subtotal if cart.subtotal else Decimal('0')
    shipping = Decimal('0') if subtotal > 100 else Decimal('10')
    tax = subtotal * Decimal('0.1')
    total = subtotal + shipping + tax  
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': float(subtotal),
        'shipping': float(shipping),
        'tax': float(tax),
        'total': float(total)
    }
    
    return render(request, 'products/cart_detail.html', context)
@require_POST
def add_to_cart(request):
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        size = request.POST.get('size', '')
        color = request.POST.get('color', '')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart = get_cart(request)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            color=color,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        cart_data = {
            'total_items': cart.total_items,
            'item_count': cart_item.quantity,
            'item_total': float(cart_item.total_price),
            'cart_total': float(cart.subtotal),
            'message': f'{product.name} added to cart!'
        }
        
        return JsonResponse(cart_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_POST
def update_cart_item(request):
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=item_id)
        
        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        cart = cart_item.cart
        
        return JsonResponse({
            'item_total': float(cart_item.total_price) if cart_item.id else 0,
            'cart_total': float(cart.subtotal),
            'total_items': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_POST
def remove_from_cart(request):
    try:
        item_id = request.POST.get('item_id')
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart = cart_item.cart
        cart_item.delete()
        
        return JsonResponse({
            'cart_total': float(cart.subtotal),
            'total_items': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# checkout view 
def checkout(request):
    cart = get_cart(request)
    cart_items = cart.items.all().select_related('product')
    
    if not cart_items:
        messages.warning(request, 'Your cart is empty!')
        return redirect('products:product_list')
    
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        country = request.POST.get('country')
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes', '')
        
        # Calculate totals
        subtotal = float(cart.subtotal)
        shipping = 0 if subtotal > 100 else 10
        tax = subtotal * 0.1
        total = subtotal + shipping + tax
        
        # Create order
        order = Order.objects.create(
            session_key=request.session.get('cart_session_key'),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            country=country,
            subtotal=subtotal,
            shipping_cost=shipping,
            tax=tax,
            total=total,
            payment_method=payment_method,
            notes=notes,
            payment_status='pending',
        )
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=float(item.product.price),
                size=item.size,
                color=item.color,
            )

            
        # Cash on delivery - clear cart now
        cart.items.all().delete()
        messages.success(request, f'Order placed successfully! Order number: {order.order_number}')
        return redirect('products:order_confirmation', order_id=order.id)
        
    # GET request - show checkout form
    subtotal = float(cart.subtotal)
    shipping = 0 if subtotal > 100 else 10
    tax = subtotal * 0.1
    total = subtotal + shipping + tax
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }
    
    return render(request, 'products/checkout.html', context)

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
        'domain': request.get_host(),
    }
    
    return render(request, 'products/order_confirmation.html', context)
# email functions 
def send_order_confirmation_email(order, order_items):
    """Send order confirmation email to customer"""
    subject = f'Order Confirmation - {order.order_number}'
    
    # HTML email template
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'order_items': order_items,
        'total': order.total,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_admin_notification_email(order, order_items):
    """Send notification email to store admin"""
    subject = f'New Order Received - {order.order_number}'
    
    html_message = render_to_string('emails/admin_notification.html', {
        'order': order,
        'order_items': order_items,
        'total': order.total,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        html_message=html_message,
        fail_silently=False,
    )

# order views 

def my_orders(request):
    """Display all orders for the current session"""
    session_key = request.session.get('cart_session_key')
    
    if session_key:
        orders = Order.objects.filter(session_key=session_key).order_by('-created_at')
    else:
        orders = []
    
    context = {
        'orders': orders,
    }
    return render(request, 'products/my_orders.html', context)

def order_track(request, order_id):
    """Track specific order status"""
    session_key = request.session.get('cart_session_key')
    order = get_object_or_404(Order, id=order_id, session_key=session_key)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'products/order_track.html', context)

# admin views 

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with statistics"""
    products = Product.objects.all().order_by('-created_at')[:10]
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_categories = Category.objects.count()
    low_stock = Product.objects.filter(stock__lt=10).count()
    unread_messages = ContactMessage.objects.filter(is_read=False).count() 
    recent_messages = ContactMessage.objects.all()[:5]  
    
    context = {
        'products': products,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_categories': total_categories,
        'low_stock': low_stock,
        'unread_messages': unread_messages,  
        'recent_messages': recent_messages,
    }
    return render(request, 'products/admin/dashboard.html', context)

@staff_member_required
def admin_products(request):
    """List all products with management options"""
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'products/admin/products_list.html', {'products': products})

@staff_member_required
def admin_product_add(request):
    """Add new product"""
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        compare_price = request.POST.get('compare_price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        short_description = request.POST.get('short_description')
        is_featured = request.POST.get('is_featured') == 'on'
        is_new = request.POST.get('is_new') == 'on'
        is_bestseller = request.POST.get('is_bestseller') == 'on'
        
        category = get_object_or_404(Category, id=category_id)
        
        product = Product.objects.create(
            name=name,
            slug=slugify(name),
            category=category,
            price=price,
            compare_price=compare_price if compare_price else None,
            stock=stock,
            description=description,
            short_description=short_description,
            is_featured=is_featured,
            is_new=is_new,
            is_bestseller=is_bestseller,
            is_active=True,
        )
        
        # Handle image upload
        if request.FILES.get('main_image'):
            product.main_image = request.FILES['main_image']
            product.save()
        
        messages.success(request, f'Product "{name}" added successfully!')
        return redirect('products:admin_products')
    
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.all()
    return render(request, 'products/admin/product_form.html', {
        'categories': categories,
        'brands': brands,
        'title': 'Add Product'
    })

@staff_member_required
def admin_product_edit(request, product_id):
    """Edit existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.slug = slugify(request.POST.get('name'))
        product.category_id = request.POST.get('category')
        product.price = request.POST.get('price')
        product.compare_price = request.POST.get('compare_price') or None
        product.stock = request.POST.get('stock')
        product.description = request.POST.get('description')
        product.short_description = request.POST.get('short_description')
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.is_new = request.POST.get('is_new') == 'on'
        product.is_bestseller = request.POST.get('is_bestseller') == 'on'
        
        if request.FILES.get('main_image'):
            product.main_image = request.FILES['main_image']
        
        product.save()
        
        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('products:admin_products')
    
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.all()
    return render(request, 'products/admin/product_form.html', {
        'product': product,
        'categories': categories,
        'brands': brands,
        'title': 'Edit Product'
    })

@staff_member_required
def admin_product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('products:admin_products')
    
    return render(request, 'products/admin/product_confirm_delete.html', {'product': product})


# contact views
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Save to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        

        messages.success(request, 'Your message has been sent successfully! We will contact you soon.')

        return redirect('products:contact')
    
    return render(request, 'products/contact.html')


# paymob views 

def initiate_paymob_payment(request, order_id):
    """Start Paymob payment for an order"""
    order = get_object_or_404(Order, id=order_id)
    
    try:
        # Step 1: Get Authentication Token
        auth_response = requests.post(
            'https://accept.paymob.com/api/auth/tokens',
            json={'api_key': settings.PAYMOB_API_KEY}
        )
        token = auth_response.json().get('token')
        
        if not token:
            return JsonResponse({'error': 'Failed to get auth token'}, status=400)
        
        # Step 2: Create Order
        order_response = requests.post(
            'https://accept.paymob.com/api/ecommerce/orders',
            json={
                'auth_token': token,
                'delivery_needed': 'false',
                'amount_cents': int(order.total * 100),
                'currency': 'EGP',
                'merchant_id': settings.PAYMOB_MERCHANT_ID,
                'items': []
            }
        )
        
        paymob_order_id = order_response.json().get('id')
        
        if not paymob_order_id:
            return JsonResponse({'error': 'Failed to create order'}, status=400)
        
        # Step 3: Get Payment Key
        billing_data = {
            'apartment': 'NA',
            'email': order.email,
            'floor': 'NA',
            'first_name': order.first_name,
            'street': order.address[:50],
            'building': 'NA',
            'phone_number': order.phone,
            'shipping_method': 'NA',
            'postal_code': order.zip_code or 'NA',
            'city': order.city or 'NA',
            'country': order.country or 'EG',
            'last_name': order.last_name,
            'state': order.state or 'NA'
        }
        
        payment_key_response = requests.post(
            'https://accept.paymob.com/api/acceptance/payment_keys',
            json={
                'auth_token': token,
                'amount_cents': int(order.total * 100),
                'expiration': 3600,
                'order_id': paymob_order_id,
                'billing_data': billing_data,
                'currency': 'EGP',
                'integration_id': settings.PAYMOB_INTEGRATION_ID,
                'lock_order_when_paid': 'false'
            }
        )
        
        payment_token = payment_key_response.json().get('token')
        
        if not payment_token:
            return JsonResponse({'error': 'Failed to get payment token'}, status=400)
        
        # Save payment info to order
        order.payment_intent_id = str(paymob_order_id)
        order.save()
        
        # Redirect to Paymob checkout page
        paymob_url = f'https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_token}'
        return redirect(paymob_url)
        
    except Exception as e:
        print(f"Paymob error: {e}")
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def paymob_webhook(request):
    """Handle Paymob's callback after payment"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Check if payment was successful
            if data.get('success') == 'true' or data.get('txn_response_code') == '000':
                order_id = data.get('merchant_order_id')
                paymob_order_id = data.get('order_id')
                
                if order_id:
                    try:
                        order = Order.objects.get(id=order_id)
                        order.payment_status = 'paid'
                        order.status = 'processing'
                        order.save()
                        
                        # Clear cart
                        session_key = order.session_key
                        if session_key:
                            try:
                                from .models import Cart
                                cart = Cart.objects.get(session_key=session_key)
                                cart.items.all().delete()
                            except Cart.DoesNotExist:
                                pass
                        
                        # Send confirmation emails
                        try:
                            send_order_confirmation_email(order, order.items.all())
                            send_admin_notification_email(order, order.items.all())
                        except:
                            pass
                        
                        print(f"Order {order.order_number} paid successfully")
                        
                    except Order.DoesNotExist:
                        print(f"Order {order_id} not found")
            
            return JsonResponse({'status': 'ok'})
            
        except Exception as e:
            print(f"Webhook error: {e}")
            return JsonResponse({'status': 'error'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)