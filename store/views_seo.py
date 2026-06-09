"""SEO-related views: robots.txt"""
from django.conf import settings
from django.http import HttpResponse


def robots_txt(request):
    """
    Serve robots.txt for search engine crawlers.

    Allows all public pages; blocks admin, API, account, and checkout URLs.
    """
    site_domain = getattr(settings, 'SITE_DOMAIN', 'https://priyankasuperbazaar.com').rstrip('/')
    sitemap_url = f'{site_domain}/sitemap.xml'

    lines = [
        'User-agent: *',
        'Allow: /',
        '',
        '# Block admin and private areas',
        'Disallow: /admin/',
        'Disallow: /accounts/',
        'Disallow: /api/',
        'Disallow: /customer/',
        'Disallow: /account/',
        'Disallow: /cart/',
        'Disallow: /checkout/',
        'Disallow: /wishlist/',
        'Disallow: /delivery/',
        'Disallow: /order/',
        'Disallow: /create-render-admin/',
        '',
        f'Sitemap: {sitemap_url}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
