from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from .models import SiteSettings, Order
import json
import urllib.request
import urllib.error

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """Custom authentication backend that allows login with email or username"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        # Check if username is an email
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
        else:
            # Try username
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                user = None

            # Try phone via CustomerProfile
            try:
                from .models import CustomerProfile

                profile = CustomerProfile.objects.select_related('user').filter(phone=username).first()
                if profile and profile.user and profile.user.check_password(password):
                    return profile.user
            except Exception:
                return None

            # Try phone via default shipping address (if any)
            try:
                from .models import Address

                address = Address.objects.select_related('user').filter(
                    phone=username,
                    address_type='shipping',
                    is_default=True,
                ).first()
                if address and address.user and address.user.check_password(password):
                    return address.user
            except Exception:
                return None
        
        return None


def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    site_settings = SiteSettings.load()
    
    subject = f'Order Confirmation - {order.order_number}'
    context = {
        'order': order,
        'site_settings': site_settings,
    }
    
    try:
        message = render_to_string('store/emails/order_confirmation.html', context)
        plain_message = render_to_string('store/emails/order_confirmation.txt', context)
    except:
        # If templates don't exist, use simple text
        plain_message = f"""Order Confirmation

Dear {order.user.get_full_name() if order.user else order.shipping_address.full_name},

Thank you for your order! Your order has been confirmed.

Order Details:
Order Number: {order.order_number}
Order Date: {order.created_at.strftime('%B %d, %Y')}
Total Amount: ₹{order.total}

We will notify you once your order is shipped.

Thank you for shopping with {site_settings.site_name}!"""
        message = plain_message
    
    recipient = order.user.email if order.user and order.user.email else None
    
    if recipient:
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                html_message=message if message != plain_message else None,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")


def send_order_status_update_email(order, status_message):
    """Send order status update email"""
    site_settings = SiteSettings.load()
    
    subject = f'Order {order.order_number} - Status Update'
    context = {
        'order': order,
        'status_message': status_message,
        'site_settings': site_settings,
    }
    
    try:
        message = render_to_string('store/emails/order_status_update.html', context)
        plain_message = render_to_string('store/emails/order_status_update.txt', context)
    except:
        plain_message = f"""Order Status Update

Dear {order.user.get_full_name() if order.user else order.shipping_address.full_name},

{status_message}

Order Number: {order.order_number}
Current Status: {order.get_status_display()}

Thank you for shopping with {site_settings.site_name}!"""
        message = plain_message
    
    if order.user and order.user.email:
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                html_message=message if message != plain_message else None,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")


def send_contact_form_email(name, email, subject, message):
    """Send contact form submission email to admin"""
    site_settings = SiteSettings.load()
    
    admin_subject = f'Contact Form: {subject}'
    context = {
        'name': name,
        'email': email,
        'subject': subject,
        'message': message,
        'site_settings': site_settings,
    }
    
    try:
        message_body = render_to_string('store/emails/contact_form.html', context)
        plain_message = f"From: {name} ({email})\n\nSubject: {subject}\n\nMessage:\n{message}"
    except:
        plain_message = f"From: {name} ({email})\n\nSubject: {subject}\n\nMessage:\n{message}"
        message_body = plain_message
    
    try:
        send_mail(
            subject=admin_subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[site_settings.contact_email],
            html_message=message_body if message_body != plain_message else None,
            fail_silently=False,
        )
        # Send acknowledgment to user
        send_mail(
            subject=f'Thank you for contacting {site_settings.site_name}',
            message=f'Thank you for contacting us. We will get back to you soon.\n\nYour message: {message}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending contact email: {e}")


def calculate_tax(amount, tax_rate=0.18):
    """Calculate tax (18% GST by default)"""
    return Decimal(str(round(float(amount) * tax_rate, 2)))


def calculate_shipping_cost(order_total, shipping_method=None):
    """Calculate shipping cost"""
    from .models import ShippingMethod, SiteSettings
    
    if shipping_method:
        if order_total >= shipping_method.min_order_amount:
            return Decimal('0.00')
        return shipping_method.price
    
    # Default shipping cost logic
    site_settings = SiteSettings.load()
    if hasattr(site_settings, 'min_order_amount') and order_total >= site_settings.min_order_amount:
        return Decimal('0.00')
    
    return Decimal('50.00')  # Default shipping cost


def send_login_alert_email(user, identifier=None):
    if not user or not getattr(user, 'email', None):
        return

    site_settings = SiteSettings.load()
    subject = f"Login Alert - {site_settings.site_name}"
    name = user.get_full_name() or user.username
    ident_text = f" using {identifier}" if identifier else ""
    plain_message = (
        f"Hi {name},\n\n"
        f"You have successfully logged in to {site_settings.site_name}{ident_text}.\n\n"
        f"If this wasn't you, please change your password immediately."
    )

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending login alert email: {e}")


def _send_sms_via_http(phone, message):
    api_url = getattr(settings, 'SMS_API_URL', '')
    api_key = getattr(settings, 'SMS_API_KEY', '')

    if not api_url or not api_key:
        return False

    payload = {
        'to': phone,
        'message': message,
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"Error sending SMS: {e}")
        return False


def send_sms(phone, message):
    if not phone or not message:
        return False
    try:
        return _send_sms_via_http(phone, message)
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False


def send_login_alert_sms(phone, site_name=None):
    site_settings = SiteSettings.load()
    name = site_name or site_settings.site_name
    message = f"You have successfully logged in to {name}. If this wasn't you, secure your account."
    return send_sms(phone, message)


def send_order_confirmation_sms(order, phone=None):
    if not order:
        return False

    site_settings = SiteSettings.load()
    target_phone = phone
    if not target_phone:
        try:
            if getattr(order, 'shipping_address', None) and order.shipping_address.phone:
                target_phone = order.shipping_address.phone
        except Exception:
            target_phone = None

    if not target_phone:
        return False

    message = (
        f"Order placed successfully! Order: {order.order_number}. "
        f"Total: ₹{order.total}. Thanks for shopping with {site_settings.site_name}."
    )
    return send_sms(target_phone, message)

