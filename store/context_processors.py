from .models import Category, Cart, SiteSettings


def catalog(request):
    """Provide categories list and cart item count to all templates."""
    categories = Category.objects.filter(is_active=True)
    site_settings = SiteSettings.load()

    cart_items_count = 0

    # Best-effort cart lookup; never raise errors here
    try:
        cart_qs = Cart.objects.all()
        if request.user.is_authenticated:
            cart_qs = cart_qs.filter(user=request.user)
        else:
            if not request.session.session_key:
                # No session yet → no cart
                return {
                    "categories": categories,
                    "cart_items_count": 0,
                    "site_settings": site_settings,
                }
            cart_qs = cart_qs.filter(session_key=request.session.session_key)

        cart = cart_qs.first()
        if cart:
            cart_items_count = cart.get_total_quantity()
    except Exception:
        cart_items_count = 0

    return {
        "categories": categories,
        "cart_items_count": cart_items_count,
        "site_settings": site_settings,
    }
