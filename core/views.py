from django.shortcuts import render
from products.models import Category, Product
# Create your views here.



def landing_page(request):
    """Home page view"""
    # Get featured categories (limit to 4)
    categories = Category.objects.filter(is_active=True, parent=None)[:4]
    
    # Get featured products
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'core/home.html', context)