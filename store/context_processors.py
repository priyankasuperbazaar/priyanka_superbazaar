from .models import Category, Cart, SiteSettings, Wishlist


def catalog(request):
    """Provide categories list and cart item count to all templates."""
    categories = Category.objects.all().order_by('name')
    site_settings = SiteSettings.load()

    cart_items_count = 0
    wishlist_items_count = 0

    try:
        if request.user.is_authenticated:
            wishlist_items_count = Wishlist.objects.filter(user=request.user).count()
    except Exception:
        wishlist_items_count = 0

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
        "wishlist_items_count": wishlist_items_count,
        "site_settings": site_settings,
    }
