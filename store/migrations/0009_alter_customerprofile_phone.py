from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_customerprofile_passwordresetotp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerprofile',
            name='phone',
            field=models.CharField(max_length=20, verbose_name='phone number'),
        ),
    ]
