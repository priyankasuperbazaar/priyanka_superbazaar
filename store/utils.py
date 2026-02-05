from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from .models import SiteSettings, Order


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

