from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_update_sitesettings_contact_info'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('phone', models.CharField(max_length=20, unique=True, verbose_name='phone number')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer_profile', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'customer profile',
                'verbose_name_plural': 'customer profiles',
            },
        ),
        migrations.CreateModel(
            name='PasswordResetOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('phone', models.CharField(db_index=True, max_length=20, verbose_name='phone number')),
                ('otp', models.CharField(max_length=10, verbose_name='otp')),
                ('expires_at', models.DateTimeField(verbose_name='expires at')),
                ('is_used', models.BooleanField(default=False, verbose_name='is used')),
            ],
            options={
                'verbose_name': 'password reset otp',
                'verbose_name_plural': 'password reset otps',
                'ordering': ('-created_at',),
            },
        ),
    ]
