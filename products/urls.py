from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    # Cart URLs
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-track/<int:order_id>/', views.order_track, name='order_track'),
    # Admin Management URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/product/add/', views.admin_product_add, name='admin_product_add'),
    path('admin/product/edit/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/product/delete/<int:product_id>/', views.admin_product_delete, name='admin_product_delete'),
    # contact URLs
    path('contact/', views.contact, name='contact'),
    # Paymob URLs
    path('paymob/pay/<int:order_id>/', views.initiate_paymob_payment, name='initiate_paymob_payment'),
    path('paymob/webhook/', views.paymob_webhook, name='paymob_webhook'),
    path('quick-view/<int:product_id>/', views.product_quick_view, name='product_quick_view'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),

]