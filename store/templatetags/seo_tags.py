"""Template tags for SEO helpers."""
import json

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def schema_json(value):
    """Serialize schema data to JSON for JSON-LD script tags."""
    if not value:
        return ''
    return json.dumps(value, ensure_ascii=False)


@register.simple_tag
def absolute_url(request, path='/'):
    """Build absolute URL from request and path."""
    from store.seo import build_absolute_url
    return build_absolute_url(request, path)


@register.simple_tag
def ga4_id():
    """Return GA4 measurement ID from settings (empty if not configured)."""
    return getattr(settings, 'GOOGLE_ANALYTICS_ID', '')


@register.simple_tag
def gsc_verification():
    """Return Google Search Console verification code from settings."""
    return getattr(settings, 'GOOGLE_SITE_VERIFICATION', '')
