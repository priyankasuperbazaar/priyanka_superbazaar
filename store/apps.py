from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        from . import signals  # noqa: F401
        self._sync_site_domain()

    def _sync_site_domain(self):
        """Keep django.contrib.sites in sync with SITE_DOMAIN (avoids example.com)."""
        try:
            from django.conf import settings
            from django.contrib.sites.models import Site
            from .seo import SITE_NAME, get_site_hostname

            Site.objects.update_or_create(
                pk=getattr(settings, 'SITE_ID', 1),
                defaults={
                    'domain': get_site_hostname(),
                    'name': SITE_NAME,
                },
            )
        except Exception:
            # Database may be unavailable during migrations or initial setup.
            pass
