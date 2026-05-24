from .models import Cart

def cart_count(request):
    session_key = request.session.get('cart_session_key')
    if session_key:
        try:
            cart = Cart.objects.get(session_key=session_key)
            return {'cart_total_items': cart.total_items}
        except Cart.DoesNotExist:
            pass
    return {'cart_total_items': 0}
# Context Processor لعداد السلة