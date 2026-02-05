from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib import messages
from django.views.decorators.http import require_POST
from decimal import Decimal

from django.http import JsonResponse, HttpResponse
from .models import (
    Product,
    Category,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Address,
    Offer,
    SiteSettings,
    Wishlist,
    DeliveryBoy,
    ProductReview,
    PromoCode,
    ShippingMethod,
    Payment,
)
from .forms import (
    ProductReviewForm, AddressForm, UserProfileForm,
    ContactForm, CheckoutForm
)
from .utils import (
    send_order_confirmation_email, send_order_status_update_email,
    send_contact_form_email, calculate_tax, calculate_shipping_cost
)


def home(request):
    """Homepage showing featured products and categories."""
    featured_products = Product.objects.filter(available=True, featured=True)[:8]
    latest_products = Product.objects.filter(available=True).order_by("-created_at")[:8]
    offers = Offer.objects.filter(is_active=True)[:3]
    context = {
        "featured_products": featured_products,
        "latest_products": latest_products,
        "offers": offers,
    }
    return render(request, "store/home.html", context)


def product_list(request, category_slug=None):
    """List products, optionally filtered by category."""
    category = None
    products = Product.objects.filter(available=True)
    categories = Category.objects.filter(is_active=True)
    
    # Get wishlist items for the current user
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(request.user.wishlist.values_list('product_id', flat=True))

    query = request.GET.get("q", "").strip()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    context = {
        "category": category,
        "categories": categories,
        "products": products,
        "query": query,
        "wishlist_ids": wishlist_ids,
    }
    return render(request, "store/product_list.html", context)


def product_detail(request, id, slug):
    """Show a single product detail page."""
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    images = product.images.all()
    reviews = product.reviews.filter(is_approved=True)

    context = {
        "product": product,
        "images": images,
        "reviews": reviews,
    }
    return render(request, "store/product_detail.html", context)


def about(request):
    site_settings = SiteSettings.load()
    return render(request, "store/about.html", {"site_settings": site_settings})


def contact(request):
    """Contact form view"""
    site_settings = SiteSettings.load()
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            send_contact_form_email(name, email, subject, message)
            messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            return redirect('store:contact')
    else:
        form = ContactForm()
    
    return render(request, 'store/contact.html', {'form': form, 'site_settings': site_settings})


def delivery_login(request):
    """Custom login view for delivery personnel"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Check if user is a delivery boy
            if hasattr(user, 'delivery_profile'):
                auth_login(request, user)
                return redirect('store:delivery_dashboard')
            else:
                form.add_error(None, 'This account is not authorized for delivery access.')
    else:
        form = AuthenticationForm(request)
    return render(request, 'store/delivery/login.html', {'form': form})


def delivery_logout(request):
    """Logout view for delivery personnel"""
    auth_logout(request)
    return redirect('store:delivery_login')


def delivery_dashboard(request):
    """Dashboard for delivery personnel"""
    if not request.user.is_authenticated or not hasattr(request.user, 'delivery_profile'):
        return redirect('store:delivery_login')
        
    delivery_boy = request.user.delivery_profile
    active_orders = delivery_boy.get_active_orders()
    recent_deliveries = delivery_boy.delivery_orders.filter(status=Order.STATUS_DELIVERED).order_by('-updated_at')[:10]
    
    return render(request, 'store/delivery/dashboard.html', {
        'delivery_boy': delivery_boy,
        'active_orders': active_orders,
        'recent_deliveries': recent_deliveries,
    })


def delivery_order_detail(request, order_number):
    """Detail page for a delivery boy to view an assigned order, contact, and map."""
    if not request.user.is_authenticated or not hasattr(request.user, 'delivery_profile'):
        return redirect('store:delivery_login')

    delivery_boy = request.user.delivery_profile
    order = get_object_or_404(Order, order_number=order_number, delivery_boy=delivery_boy)

    shipping_address = order.shipping_address
    map_query = ""
    if shipping_address:
        parts = [
            shipping_address.address_line_1,
            shipping_address.address_line_2,
            shipping_address.city,
            shipping_address.state,
            shipping_address.postal_code,
            shipping_address.country,
        ]
        map_query = ", ".join([p for p in parts if p])

    return render(request, 'store/delivery/order_detail.html', {
        'order': order,
        'shipping_address': shipping_address,
        'map_query': map_query,
        'delivery_boy': delivery_boy,
    })


@require_POST
def delivery_order_update(request, order_number):
    """Allow an assigned delivery boy to update order/payment status."""
    if not request.user.is_authenticated or not hasattr(request.user, 'delivery_profile'):
        return redirect('store:delivery_login')

    delivery_boy = request.user.delivery_profile
    order = get_object_or_404(Order, order_number=order_number, delivery_boy=delivery_boy)

    action = request.POST.get('action', '').strip()

    if action == 'mark_paid_cod':
        order.payment_method = Order.PAYMENT_METHOD_COD
        order.mark_as_paid()
        messages.success(request, 'Payment marked as Paid (COD).')
    elif action == 'mark_paid_online':
        order.payment_method = Order.PAYMENT_METHOD_STRIPE
        order.mark_as_paid()
        messages.success(request, 'Payment marked as Paid (Online).')
    elif action == 'mark_processing':
        order.status = Order.STATUS_PROCESSING
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Order marked as Processing.')
    elif action == 'mark_shipped':
        order.status = Order.STATUS_SHIPPED
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Order marked as Shipped.')
    elif action == 'mark_delivered':
        order.status = Order.STATUS_DELIVERED
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Order marked as Delivered.')
    else:
        messages.error(request, 'Invalid action.')
    next_url = request.POST.get('next', '').strip()
    if next_url:
        return redirect(next_url)
    return redirect('store:delivery_order_detail', order_number=order.order_number)


@require_POST
def delivery_update_location(request):
    """Update current GPS location for the logged-in delivery boy."""
    if not request.user.is_authenticated or not hasattr(request.user, 'delivery_profile'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    lat = request.POST.get('lat', '').strip()
    lng = request.POST.get('lng', '').strip()
    if not lat or not lng:
        return JsonResponse({'status': 'error', 'message': 'Missing coordinates'}, status=400)

    delivery_boy = request.user.delivery_profile
    delivery_boy.current_location = f"{lat},{lng}"
    delivery_boy.save(update_fields=['current_location', 'updated_at'])

    return JsonResponse({'status': 'ok', 'location': delivery_boy.current_location})


def cart(request):
    return cart_detail(request)


def _get_cart(request):
    """Return existing cart or create one for current user/session."""
    cart_qs = Cart.objects.all()
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    # Anonymous user: use session key
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
    return cart


def cart_add(request, product_id):
    """Add a product to the cart or update its quantity."""
    product = get_object_or_404(Product, id=product_id, available=True)
    cart = _get_cart(request)

    quantity = 1
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if created:
        item.quantity = max(quantity, 1)
    else:
        item.quantity += max(quantity, 1)
    item.save()

    return redirect("store:cart_detail")


def cart_remove(request, product_id):
    """Remove a product from the cart."""
    cart = _get_cart(request)
    try:
        item = CartItem.objects.get(cart=cart, product_id=product_id)
        item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect("store:cart_detail")


def cart_detail(request):
    """Display cart contents."""
    cart = _get_cart(request)
    items = cart.items.select_related("product")
    total_price = cart.get_total_price()

    context = {
        "cart": cart,
        "items": items,
        "total_price": total_price,
    }
    return render(request, "store/cart.html", context)


def cart_update(request, product_id):
    """Update quantity of a product in the cart."""
    if request.method != "POST":
        return redirect("store:cart_detail")

    cart = _get_cart(request)
    try:
        item = CartItem.objects.get(cart=cart, product_id=product_id)
    except CartItem.DoesNotExist:
        return redirect("store:cart_detail")

    try:
        quantity = int(request.POST.get("quantity", item.quantity))
    except (TypeError, ValueError):
        quantity = item.quantity

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()

    return redirect("store:cart_detail")


@transaction.atomic
def checkout(request):
    """Enhanced checkout with promo code, shipping, tax calculation"""
    cart = _get_cart(request)
    items = cart.items.select_related("product")
    
    if not items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect("store:cart_detail")
    
    site_settings = SiteSettings.load()
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    
    # Check minimum order amount
    cart_total = cart.get_total_price()
    if site_settings.min_order_amount > 0 and cart_total < site_settings.min_order_amount:
        messages.warning(
            request,
            f'Minimum order amount is ₹{site_settings.min_order_amount}. Please add more items to your cart.'
        )
        return redirect("store:cart_detail")
    
    promo_code_obj = None
    discount_amount = Decimal('0.00')
    applied_promo_code = request.session.get('applied_promo_code')
    
    if applied_promo_code:
        try:
            promo_code_obj = PromoCode.objects.get(code__iexact=applied_promo_code, is_active=True)
            is_valid, _ = promo_code_obj.is_valid(cart_total)
            if is_valid:
                discount_amount = promo_code_obj.calculate_discount(cart_total)
        except PromoCode.DoesNotExist:
            request.session.pop('applied_promo_code', None)
    
    if request.method == "POST":
        form = CheckoutForm(user=request.user if request.user.is_authenticated else None, data=request.POST)
        
        if form.is_valid():
            user = request.user if request.user.is_authenticated else None
            
            # Handle saved address selection
            use_saved_address = form.cleaned_data.get('use_saved_address')
            if use_saved_address and user:
                shipping_address = use_saved_address
                billing_address = use_saved_address
            else:
                # Create new address
                shipping_address = Address.objects.create(
                    user=user,
                    address_type="shipping",
                    full_name=form.cleaned_data['full_name'],
                    phone=form.cleaned_data['phone'],
                    address_line_1=form.cleaned_data['address_line_1'],
                    address_line_2=form.cleaned_data.get('address_line_2', ''),
                    city=form.cleaned_data['city'],
                    state=form.cleaned_data['state'],
                    postal_code=form.cleaned_data['postal_code'],
                    country=form.cleaned_data.get('country', 'India'),
                    is_default=form.cleaned_data.get('save_address', False) if user else False,
                )
                billing_address = shipping_address
            
            # Calculate totals
            subtotal = cart_total
            tax_amount = calculate_tax(subtotal - discount_amount)
            
            shipping_method = form.cleaned_data.get('shipping_method')
            if shipping_method:
                shipping_cost = calculate_shipping_cost(subtotal, shipping_method)
            else:
                shipping_cost = calculate_shipping_cost(subtotal)
            
            total = subtotal + tax_amount + shipping_cost - discount_amount
            
            # Create order
            order = Order.objects.create(
                user=user,
                status=Order.STATUS_PENDING,
                payment_status=Order.PAYMENT_STATUS_PENDING,
                payment_method=Order.PAYMENT_METHOD_COD,
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_cost=shipping_cost,
                discount_amount=discount_amount,
                promo_code=promo_code_obj,
                billing_address=billing_address,
                shipping_address=shipping_address,
                customer_note=form.cleaned_data.get('customer_note', ''),
                ip_address=request.META.get("REMOTE_ADDR"),
            )
            
            # Create Payment record
            Payment.objects.create(
                order=order,
                payment_method=Payment.PAYMENT_METHOD_COD,
                amount=total,
                payment_status=Payment.PAYMENT_STATUS_PENDING,
            )
            
            # Auto-assign delivery boy
            try:
                candidate = (
                    DeliveryBoy.objects.filter(is_active=True)
                    .annotate(
                        active_count=Count(
                            'delivery_orders',
                            filter=Q(delivery_orders__status__in=[
                                Order.STATUS_PENDING,
                                Order.STATUS_PROCESSING,
                                Order.STATUS_SHIPPED,
                            ])
                        )
                    )
                    .order_by('active_count', 'id')
                    .first()
                )
                if candidate:
                    order.delivery_boy = candidate
                    order.save(update_fields=['delivery_boy', 'updated_at'])
            except Exception:
                pass
            
            # Create order items and update stock
            for item in items:
                price = item.product.discount_price or item.product.price
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_sku="",
                    price=price,
                    quantity=item.quantity,
                )
                # Update product stock
                if item.product.stock >= item.quantity:
                    item.product.stock -= item.quantity
                    item.product.save()
            
            # Update promo code usage
            if promo_code_obj:
                promo_code_obj.use()
                request.session.pop('applied_promo_code', None)
            
            # Clear cart
            cart.clear()
            
            # Send confirmation email
            try:
                send_order_confirmation_email(order)
            except Exception as e:
                print(f"Error sending email: {e}")
            
            return redirect("store:order_success", order_number=order.order_number)
    else:
        initial_data = {}
        if request.user.is_authenticated:
            default_address = Address.objects.filter(user=request.user, is_default=True, address_type='shipping').first()
            if default_address:
                initial_data = {
                    'full_name': default_address.full_name,
                    'phone': default_address.phone,
                    'address_line_1': default_address.address_line_1,
                    'address_line_2': default_address.address_line_2,
                    'city': default_address.city,
                    'state': default_address.state,
                    'postal_code': default_address.postal_code,
                    'country': default_address.country,
                }
        
        form = CheckoutForm(user=request.user if request.user.is_authenticated else None, initial=initial_data)
    
    # Calculate totals for display
    subtotal = cart_total
    calculated_tax = calculate_tax(subtotal - discount_amount)
    calculated_shipping = calculate_shipping_cost(subtotal)
    calculated_total = subtotal + calculated_tax + calculated_shipping - discount_amount
    
    context = {
        "cart": cart,
        "items": items,
        "form": form,
        "total_price": calculated_total,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "tax_amount": calculated_tax,
        "shipping_cost": calculated_shipping,
        "shipping_methods": shipping_methods,
        "applied_promo_code": applied_promo_code,
        "site_settings": site_settings,
    }
    return render(request, "store/checkout.html", context)


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "store/order_success.html", {"order": order})


@login_required
def account_profile(request):
    """Simple My Account page showing basic user info."""
    return render(request, "store/account_profile.html", {"user_obj": request.user})


@login_required
def account_orders(request):
    """List of orders for the logged-in user."""
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/account_orders.html", {"orders": orders})


def track_order(request):
    """Public order tracking page by order number."""
    order = None
    query = ""
    if request.method == "POST":
        query = request.POST.get("order_number", "").strip()
        if query:
            try:
                order = Order.objects.get(order_number=query)
            except Order.DoesNotExist:
                order = None

    return render(request, "store/order_track.html", {"order": order, "query": query})


def account_signup(request):
    """User registration page."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('store:home')
    else:
        form = UserCreationForm()
    return render(request, 'store/account_signup.html', {'form': form})


@login_required
def wishlist_view(request):
    """Display user's wishlist."""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def wishlist_add(request, product_id):
    """Add a product to the wishlist."""
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    if not created:
        # Item already in wishlist
        pass
    
    if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Product added to wishlist'})
    return redirect('store:wishlist')


@login_required
def wishlist_remove(request, product_id):
    """Remove a product from the wishlist."""
    wishlist_item = get_object_or_404(
        Wishlist,
        user=request.user,
        product_id=product_id
    )
    wishlist_item.delete()
    
    if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Product removed from wishlist'})
    return redirect('store:wishlist')


def is_in_wishlist(user, product_id):
    """Check if product is in user's wishlist."""
    if not user.is_authenticated:
        return False
    return Wishlist.objects.filter(user=user, product_id=product_id).exists()


# ==================== NEW VIEWS ====================

@login_required
def product_review_create(request, product_id):
    """Create a product review"""
    product = get_object_or_404(Product, id=product_id, available=True)
    
    # Check if user already reviewed this product
    existing_review = ProductReview.objects.filter(user=request.user, product=product).first()
    
    if request.method == 'POST':
        if existing_review:
            form = ProductReviewForm(request.POST, instance=existing_review)
        else:
            form = ProductReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.is_approved = False  # Admin approval required
            review.save()
            messages.success(request, 'Thank you for your review! It will be published after admin approval.')
            return redirect('store:product_detail', id=product.id, slug=product.slug)
    else:
        form = ProductReviewForm(instance=existing_review)
    
    return render(request, 'store/product_review_form.html', {
        'form': form,
        'product': product,
        'existing_review': existing_review
    })


@login_required
def account_profile_edit(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('store:account_profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'store/account_profile_edit.html', {'form': form})


@login_required
def account_change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('store:account_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'store/account_change_password.html', {'form': form})


@login_required
def address_list(request):
    """List user addresses"""
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'store/address_list.html', {'addresses': addresses})


@login_required
def address_create(request):
    """Create new address"""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.address_type = 'shipping'
            address.save()
            messages.success(request, 'Address added successfully.')
            return redirect('store:address_list')
    else:
        form = AddressForm()
    
    return render(request, 'store/address_form.html', {'form': form, 'title': 'Add Address'})


@login_required
def address_edit(request, address_id):
    """Edit address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('store:address_list')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'store/address_form.html', {'form': form, 'address': address, 'title': 'Edit Address'})


@login_required
@require_POST
def address_delete(request, address_id):
    """Delete address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully.')
    return redirect('store:address_list')


@require_POST
def apply_promo_code(request):
    """Apply promo code to cart via AJAX"""
    promo_code = request.POST.get('promo_code', '').strip()
    
    if not promo_code:
        return JsonResponse({'success': False, 'message': 'Please enter a promo code.'})
    
    try:
        code = PromoCode.objects.get(code__iexact=promo_code, is_active=True)
    except PromoCode.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid promo code.'})
    
    cart = _get_cart(request)
    cart_total = cart.get_total_price()
    
    is_valid, message = code.is_valid(cart_total)
    if not is_valid:
        return JsonResponse({'success': False, 'message': str(message)})
    
    discount_amount = code.calculate_discount(cart_total)
    request.session['applied_promo_code'] = code.code
    
    return JsonResponse({
        'success': True,
        'message': f'Promo code applied! You saved ₹{discount_amount:.2f}',
        'discount_amount': float(discount_amount),
        'code': code.code
    })


@require_POST
def set_promo_code(request):
    """Set promo code in session"""
    promo_code = request.POST.get('promo_code', '').strip()
    request.session['applied_promo_code'] = promo_code
    return JsonResponse({'success': True})


@login_required
def order_cancel(request, order_number):
    """Cancel order by user"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if not order.can_cancel():
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('store:account_orders')
    
    if request.method == 'POST':
        order.cancel()
        messages.success(request, 'Order has been cancelled successfully.')
        
        # Send email notification
        try:
            send_order_status_update_email(order, 'Your order has been cancelled.')
        except Exception as e:
            print(f"Error sending email: {e}")
        
        return redirect('store:account_orders')
    
    return render(request, 'store/order_cancel_confirm.html', {'order': order})


@login_required
def order_invoice(request, order_number):
    """Generate PDF invoice for order"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_number}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
        )
        title = Paragraph(f"Invoice #{order.order_number}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Order details
        data = [
            ['Order Number:', order.order_number],
            ['Order Date:', order.created_at.strftime('%B %d, %Y')],
            ['Status:', order.get_status_display()],
            ['Payment Status:', order.get_payment_status_display()],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Shipping address
        elements.append(Paragraph("<b>Shipping Address:</b>", styles['Normal']))
        if order.shipping_address:
            address_text = order.shipping_address.get_full_address().replace('\n', '<br/>')
            elements.append(Paragraph(address_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Order items
        elements.append(Paragraph("<b>Order Items:</b>", styles['Heading2']))
        items_data = [['Product', 'Quantity', 'Price', 'Subtotal']]
        
        for item in order.items.all():
            items_data.append([
                item.product_name,
                str(item.quantity),
                f"₹{item.price:.2f}",
                f"₹{item.subtotal:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Totals
        totals_data = [
            ['Subtotal:', f"₹{order.subtotal:.2f}"],
            ['Tax:', f"₹{order.tax_amount:.2f}"],
            ['Shipping:', f"₹{order.shipping_cost:.2f}"],
        ]
        
        if order.discount_amount > 0:
            totals_data.append(['Discount:', f"-₹{order.discount_amount:.2f}"])
        
        totals_data.append(['<b>Total:</b>', f"<b>₹{order.total:.2f}</b>"])
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (-1, -1), (-1, -1), 14),
            ('GRID', (0, -2), (-1, -1), 1, colors.black),
            ('BACKGROUND', (-1, -1), (-1, -1), colors.lightgrey),
        ]))
        elements.append(totals_table)
        
        doc.build(elements)
        return response
    except ImportError:
        # If reportlab is not installed, return simple text response
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_number}.txt"'
        response.write(f"Invoice #{order.order_number}\n")
        response.write(f"Order Date: {order.created_at}\n")
        response.write(f"Total: ₹{order.total}\n")
        return response
