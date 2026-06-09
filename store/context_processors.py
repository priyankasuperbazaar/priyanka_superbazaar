from .models import Category, Cart, SiteSettings, Wishlist
from .seo import build_seo_context, DEFAULT_DESCRIPTION, DEFAULT_KEYWORDS, SITE_NAME


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


_PRIVATE_PATH_PREFIXES = (
    '/admin/', '/accounts/', '/api/', '/customer/', '/account/',
    '/cart/', '/checkout/', '/wishlist/', '/delivery/', '/order/',
    '/create-render-admin/',
)


def seo_defaults(request):
    """Provide fallback SEO context for every template."""
    site_settings = SiteSettings.load()
    title = site_settings.meta_title or SITE_NAME
    description = site_settings.meta_description or DEFAULT_DESCRIPTION
    keywords = site_settings.meta_keywords or DEFAULT_KEYWORDS

    if any(request.path.startswith(prefix) for prefix in _PRIVATE_PATH_PREFIXES):
        from .seo import seo_noindex
        return seo_noindex(request, title, description)

    ctx = build_seo_context(
        request,
        title=title,
        description=description,
        keywords=keywords,
    )
    return ctx
