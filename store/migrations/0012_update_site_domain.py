"""Set django.contrib.sites Site record to the production domain."""
from django.db import migrations


def set_production_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        pk=1,
        defaults={
            'domain': 'priyankasuperbazaar.com',
            'name': 'Priyanka Super Bazaar',
        },
    )


def revert_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(pk=1).update(domain='example.com', name='example.com')


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('store', '0011_product_unit_type_productvariant_and_more'),
    ]

    operations = [
        migrations.RunPython(set_production_site_domain, revert_site_domain),
    ]
