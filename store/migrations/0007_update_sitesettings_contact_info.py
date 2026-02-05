from django.db import migrations


def update_site_settings(apps, schema_editor):
    SiteSettings = apps.get_model('store', 'SiteSettings')

    site_settings, _ = SiteSettings.objects.get_or_create(pk=1)

    phone = '9584984284'
    email = 'priyankasuperbazaar2025@gmail.com'
    addr = 'khujner road, near shivdham colony main gate,RAJGARH'

    site_settings.contact_phone = phone
    site_settings.contact_email = email
    site_settings.address = addr

    site_settings.store_phone = phone
    site_settings.store_email = email
    site_settings.store_address_line1 = addr
    site_settings.store_address_line2 = ''
    if not site_settings.store_country:
        site_settings.store_country = 'RAJGARH,INDIA'

    site_settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_order_delivery_boy'),
    ]

    operations = [
        migrations.RunPython(update_site_settings, reverse_code=migrations.RunPython.noop),
    ]
