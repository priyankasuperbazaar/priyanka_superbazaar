"""
XML Sitemaps for Priyanka Super Bazaar.

Registered in config/urls.py at /sitemap.xml

Domain and protocol come from SITE_DOMAIN in settings, not django.contrib.sites
defaults (which ship as example.com).
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Product
from .seo import get_site_hostname, get_site_protocol


class ProductionSitemap(Sitemap):
    """Base sitemap that always uses the production domain from SITE_DOMAIN."""

    protocol = 'https'

    def get_protocol(self, protocol=None):
        return get_site_protocol()

    def get_domain(self, site=None):
        return get_site_hostname()


class StaticViewSitemap(ProductionSitemap):
    """Public static pages."""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'store:home',
            'store:product-list',
            'store:about',
            'store:contact',
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(ProductionSitemap):
    """All category listing pages."""
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.all().order_by('name')

    def lastmod(self, obj):
        return obj.modified

    def location(self, obj):
        return obj.get_absolute_url()


class ProductSitemap(ProductionSitemap):
    """All available product detail pages."""
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Product.objects.filter(available=True).select_related('category').order_by('-modified')

    def lastmod(self, obj):
        return obj.modified

    def location(self, obj):
        return obj.get_absolute_url()
