"""
SEO utilities for Priyanka Super Bazaar.

Provides meta tag builders, canonical URLs, Open Graph data, and JSON-LD schemas.
"""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse


SITE_NAME = getattr(settings, 'SITE_NAME', 'Priyanka Super Bazaar')
SITE_DOMAIN = getattr(settings, 'SITE_DOMAIN', 'https://priyankasuperbazaar.com').rstrip('/')
PRODUCTION_HOSTNAME = 'priyankasuperbazaar.com'


def get_site_hostname() -> str:
    """Return hostname from SITE_DOMAIN (no scheme, no path)."""
    raw = (getattr(settings, 'SITE_DOMAIN', '') or f'https://{PRODUCTION_HOSTNAME}').strip()
    if raw.startswith('http://') or raw.startswith('https://'):
        hostname = urlparse(raw).netloc
        return hostname or PRODUCTION_HOSTNAME
    return raw.rstrip('/').split('/')[0] or PRODUCTION_HOSTNAME


def get_site_protocol() -> str:
    """Return URL scheme from SITE_DOMAIN (defaults to https)."""
    raw = (getattr(settings, 'SITE_DOMAIN', '') or f'https://{PRODUCTION_HOSTNAME}').strip()
    if raw.startswith('http://'):
        return 'http'
    return 'https'
DEFAULT_DESCRIPTION = (
    'Priyanka Super Bazaar – your trusted online grocery store and supermarket. '
    'Shop fresh fruits, vegetables, dairy, staples, and household essentials '
    'with fast delivery across your neighbourhood.'
)
DEFAULT_KEYWORDS = (
    'grocery store, supermarket, online grocery, fresh vegetables, fruits, '
    'dairy, staples, Priyanka Super Bazaar, priyankasuperbazaar'
)


def truncate_text(text: str, max_length: int = 160) -> str:
    """Truncate text to a SEO-friendly length without breaking words."""
    text = re.sub(r'\s+', ' ', (text or '').strip())
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return f'{truncated}…' if truncated else text[:max_length]


def build_absolute_url(request, path: str = '/') -> str:
    """Build an absolute URL using SITE_DOMAIN (never example.com or request host)."""
    if path.startswith('http://') or path.startswith('https://'):
        return path
    if not path.startswith('/'):
        path = f'/{path}'
    return f'{SITE_DOMAIN}{path}'


def get_image_absolute_url(request, image_field=None, fallback_static: str = 'images/logo.jpg') -> str:
    """Return an absolute URL for an image field or static fallback."""
    if image_field:
        try:
            url = image_field.url
            if url.startswith('http://') or url.startswith('https://'):
                return url
            return build_absolute_url(request, url)
        except Exception:
            pass
    return build_absolute_url(request, static(fallback_static))


def build_seo_context(
    request,
    *,
    title: str | None = None,
    description: str | None = None,
    keywords: str | None = None,
    canonical_path: str | None = None,
    og_image=None,
    og_type: str = 'website',
    robots: str = 'index, follow',
    schema_json: list[dict[str, Any]] | dict[str, Any] | None = None,
    breadcrumbs: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a complete SEO context dict for templates."""
    page_title = title or SITE_NAME
    if title and SITE_NAME.lower() not in title.lower():
        page_title = f'{title} | {SITE_NAME}'

    page_description = truncate_text(description or DEFAULT_DESCRIPTION)
    page_keywords = keywords or DEFAULT_KEYWORDS
    canonical_url = build_absolute_url(request, canonical_path or request.path)

    schemas: list[dict[str, Any]] = []
    if schema_json:
        if isinstance(schema_json, list):
            schemas.extend(schema_json)
        else:
            schemas.append(schema_json)

    if breadcrumbs:
        schemas.append(build_breadcrumb_schema(request, breadcrumbs))

    return {
        'seo': {
            'title': page_title,
            'description': page_description,
            'keywords': page_keywords,
            'canonical_url': canonical_url,
            'og_title': title or SITE_NAME,
            'og_description': page_description,
            'og_image': get_image_absolute_url(request, og_image),
            'og_type': og_type,
            'og_url': canonical_url,
            'robots': robots,
            'schema_json': schemas,
            'breadcrumbs': breadcrumbs or [],
        }
    }


def seo_for_home(request, site_settings=None) -> dict[str, Any]:
    """SEO context for the homepage."""
    title = (site_settings.meta_title if site_settings and site_settings.meta_title else
             f'{SITE_NAME} – Online Grocery Store & Supermarket')
    description = (site_settings.meta_description if site_settings and site_settings.meta_description else
                   DEFAULT_DESCRIPTION)
    keywords = (site_settings.meta_keywords if site_settings and site_settings.meta_keywords else
                DEFAULT_KEYWORDS)
    schemas = [build_local_business_schema(site_settings)]
    return build_seo_context(
        request,
        title=title,
        description=description,
        keywords=keywords,
        canonical_path=reverse('store:home'),
        og_image=site_settings.site_logo if site_settings else None,
        schema_json=schemas,
    )


def seo_for_product_list(request, category=None, query: str = '') -> dict[str, Any]:
    """SEO context for shop and category listing pages."""
    if category:
        title = f'{category.name} – Buy Online'
        description = category.description or (
            f'Shop {category.name} at {SITE_NAME}. Fresh quality groceries '
            f'delivered to your doorstep. Browse our {category.name} collection today.'
        )
        keywords = f'{category.name}, {category.name} online, grocery, {SITE_NAME}'
        canonical_path = category.get_absolute_url()
        breadcrumbs = [
            {'name': 'Home', 'url': reverse('store:home')},
            {'name': 'Shop', 'url': reverse('store:product-list')},
            {'name': category.name, 'url': canonical_path},
        ]
        og_image = category.image
    elif query:
        title = f'Search: {query}'
        description = f'Search results for "{query}" at {SITE_NAME}. Find fresh groceries and daily essentials.'
        keywords = f'{query}, grocery search, {SITE_NAME}'
        canonical_path = f"{reverse('store:product-list')}?q={query}"
        breadcrumbs = [
            {'name': 'Home', 'url': reverse('store:home')},
            {'name': 'Shop', 'url': reverse('store:product-list')},
            {'name': f'Search: {query}', 'url': canonical_path},
        ]
        og_image = None
    else:
        title = 'Shop All Products'
        description = (
            f'Browse all groceries and supermarket products at {SITE_NAME}. '
            'Fresh produce, dairy, staples, snacks, and household essentials.'
        )
        keywords = f'shop groceries, all products, supermarket, {SITE_NAME}'
        canonical_path = reverse('store:product-list')
        breadcrumbs = [
            {'name': 'Home', 'url': reverse('store:home')},
            {'name': 'Shop', 'url': canonical_path},
        ]
        og_image = None

    return build_seo_context(
        request,
        title=title,
        description=description,
        keywords=keywords,
        canonical_path=canonical_path,
        og_image=og_image,
        breadcrumbs=breadcrumbs,
    )


def seo_for_product(request, product) -> dict[str, Any]:
    """SEO context for a product detail page."""
    price = product.discount_price or product.price
    description = product.description or (
        f'Buy {product.name} online at {SITE_NAME}. '
        f'Price: ₹{price}. Category: {product.category.name}. '
        f'Order fresh groceries with fast delivery.'
    )
    keywords = f'{product.name}, {product.category.name}, buy {product.name} online, grocery, {SITE_NAME}'
    breadcrumbs = [
        {'name': 'Home', 'url': reverse('store:home')},
        {'name': 'Shop', 'url': reverse('store:product-list')},
        {'name': product.category.name, 'url': product.category.get_absolute_url()},
        {'name': product.name, 'url': product.get_absolute_url()},
    ]
    schemas = [build_product_schema(request, product)]
    return build_seo_context(
        request,
        title=product.name,
        description=description,
        keywords=keywords,
        canonical_path=product.get_absolute_url(),
        og_image=product.image,
        og_type='product',
        schema_json=schemas,
        breadcrumbs=breadcrumbs,
    )


def seo_for_static_page(request, *, page_title: str, description: str, path_name: str,
                        keywords: str | None = None) -> dict[str, Any]:
    """SEO context for static pages like About and Contact."""
    breadcrumbs = [
        {'name': 'Home', 'url': reverse('store:home')},
        {'name': page_title, 'url': reverse(path_name)},
    ]
    return build_seo_context(
        request,
        title=page_title,
        description=description,
        keywords=keywords or f'{page_title}, {SITE_NAME}, grocery store',
        canonical_path=reverse(path_name),
        breadcrumbs=breadcrumbs,
    )


def seo_noindex(request, title: str, description: str = '') -> dict[str, Any]:
    """SEO context for private pages that should not be indexed."""
    return build_seo_context(
        request,
        title=title,
        description=description or f'{title} – {SITE_NAME}',
        robots='noindex, nofollow',
    )


def build_local_business_schema(site_settings=None) -> dict[str, Any]:
    """JSON-LD LocalBusiness / GroceryStore schema."""
    phone = '+91-XXXXXXXXXX'
    address_line1 = 'Your Store Address Line 1'
    address_line2 = 'City, State'
    country = 'India'
    hours = 'Mo-Su 08:00-22:00'
    email = 'info@priyankasuperbazaar.com'

    if site_settings:
        phone = site_settings.store_phone or site_settings.contact_phone or phone
        address_line1 = site_settings.store_address_line1 or address_line1
        address_line2 = site_settings.store_address_line2 or address_line2
        country = site_settings.store_country or country
        email = site_settings.store_email or site_settings.contact_email or email
        if site_settings.store_hours:
            hours = site_settings.store_hours

    return {
        '@context': 'https://schema.org',
        '@type': 'GroceryStore',
        'name': SITE_NAME,
        'description': DEFAULT_DESCRIPTION,
        'url': SITE_DOMAIN,
        'telephone': phone,
        'email': email,
        'image': f'{SITE_DOMAIN}/static/images/logo.jpg',
        'address': {
            '@type': 'PostalAddress',
            'streetAddress': address_line1,
            'addressLocality': address_line2,
            'addressCountry': country,
        },
        'openingHours': hours,
        'priceRange': '₹₹',
        'sameAs': [
            url for url in [
                getattr(site_settings, 'facebook_url', '') if site_settings else '',
                getattr(site_settings, 'instagram_url', '') if site_settings else '',
                getattr(site_settings, 'twitter_url', '') if site_settings else '',
                getattr(site_settings, 'linkedin_url', '') if site_settings else '',
                'https://www.instagram.com/priyanka_super_bazaar',
            ] if url
        ],
    }


def build_product_schema(request, product) -> dict[str, Any]:
    """JSON-LD Product schema for product detail pages."""
    price = product.discount_price or product.price
    availability = 'https://schema.org/InStock' if product.is_in_stock() and product.available else 'https://schema.org/OutOfStock'
    image_url = get_image_absolute_url(request, product.image)

    schema: dict[str, Any] = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': product.name,
        'description': truncate_text(product.description or f'{product.name} available at {SITE_NAME}', 500),
        'image': image_url,
        'sku': str(product.id),
        'brand': {
            '@type': 'Brand',
            'name': product.category.name,
        },
        'offers': {
            '@type': 'Offer',
            'url': build_absolute_url(request, product.get_absolute_url()),
            'priceCurrency': 'INR',
            'price': str(price),
            'availability': availability,
            'seller': {
                '@type': 'Organization',
                'name': SITE_NAME,
            },
        },
    }
    return schema


def build_breadcrumb_schema(request, breadcrumbs: list[dict[str, str]]) -> dict[str, Any]:
    """JSON-LD BreadcrumbList schema."""
    items = []
    for i, crumb in enumerate(breadcrumbs, start=1):
        items.append({
            '@type': 'ListItem',
            'position': i,
            'name': crumb['name'],
            'item': build_absolute_url(request, crumb['url']),
        })
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': items,
    }


def schema_to_json(schema: list[dict] | dict) -> str:
    """Serialize schema dict(s) to JSON for template output."""
    return json.dumps(schema, ensure_ascii=False)
