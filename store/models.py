import os
import uuid
from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def product_image_path(instance, filename):
    """Generate file path for product images"""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('products', filename)


class TimeStampedModel(models.Model):
    """Abstract base model with created and modified timestamps"""
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """Product category model"""
    name = models.CharField(_('name'), max_length=200, db_index=True)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    image = models.ImageField(_('image'), upload_to='categories/', blank=True, null=True)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('is active'), default=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ('name',)
        indexes = [
            models.Index(fields=['name'], name='category_name_idx'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_list_by_category', args=[self.slug])


class Product(TimeStampedModel):
    """Product model"""
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name=_('category')
    )
    name = models.CharField(_('name'), max_length=200, db_index=True)
    slug = models.SlugField(_('slug'), max_length=200, db_index=True)
    description = models.TextField(_('description'), blank=True)
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_price = models.DecimalField(
        _('discount price'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField(_('stock'), default=0)
    available = models.BooleanField(_('available'), default=True)
    featured = models.BooleanField(_('featured'), default=False)
    image = models.ImageField(
        _('main image'),
        upload_to=product_image_path,
        blank=True
    )

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name'], name='product_name_idx'),
            models.Index(fields=['-created_at'], name='created_at_idx'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.id, self.slug])

    def get_discount_percentage(self):
        """Calculate discount percentage if discount price is set"""
        if self.discount_price:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return round(discount)
        return 0

    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0


class ProductImage(models.Model):
    """Additional product images"""
    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE,
        verbose_name=_('product')
    )
    image = models.ImageField(_('image'), upload_to=product_image_path)
    alt_text = models.CharField(_('alt text'), max_length=200, blank=True)
    is_featured = models.BooleanField(_('is featured'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ('-is_featured', 'created_at')

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductReview(TimeStampedModel):
    """Product reviews by users"""
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    product = models.ForeignKey(
        Product,
        related_name='reviews',
        on_delete=models.CASCADE,
        verbose_name=_('product')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('user')
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_('comment'), max_length=1000)
    is_approved = models.BooleanField(_('is approved'), default=False)

    class Meta:
        verbose_name = _('product review')
        verbose_name_plural = _('product reviews')
        ordering = ('-created_at',)
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user}'s review for {self.product}"


class Wishlist(TimeStampedModel):
    """User's wishlist"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist',
        verbose_name=_('user')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        verbose_name=_('product')
    )

    class Meta:
        verbose_name = _('wishlist item')
        verbose_name_plural = _('wishlist items')
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user}'s wishlist item: {self.product}"


class Cart(TimeStampedModel):
    """Shopping cart model"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('user'),
        null=True,
        blank=True
    )
    session_key = models.CharField(
        _('session key'),
        max_length=40,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')
        ordering = ('-updated_at',)

    def __str__(self):
        if self.user:
            return f"{self.user}'s cart"
        return f"Anonymous cart ({self.session_key})"

    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Remove all items from the cart"""
        self.items.all().delete()


class CartItem(TimeStampedModel):
    """Items in the shopping cart"""
    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name=_('cart')
    )
    product = models.ForeignKey(
        Product,
        related_name='cart_items',
        on_delete=models.CASCADE,
        verbose_name=_('product')
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = ('cart', 'product')
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_cost(self):
        """Calculate the total cost of this cart item"""
        price = self.product.discount_price or self.product.price
        return price * self.quantity

    def save(self, *args, **kwargs):
        # Update cart's updated_at timestamp
        self.cart.save()
        super().save(*args, **kwargs)


class PromoCode(TimeStampedModel):
    """Promo code model for discounts"""
    DISCOUNT_TYPE_PERCENTAGE = 'percentage'
    DISCOUNT_TYPE_FLAT = 'flat'
    
    DISCOUNT_TYPES = [
        (DISCOUNT_TYPE_PERCENTAGE, _('Percentage')),
        (DISCOUNT_TYPE_FLAT, _('Flat Amount')),
    ]
    
    code = models.CharField(_('code'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)
    discount_type = models.CharField(
        _('discount type'),
        max_length=10,
        choices=DISCOUNT_TYPES,
        default=DISCOUNT_TYPE_PERCENTAGE
    )
    discount_value = models.DecimalField(
        _('discount value'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_discount = models.DecimalField(
        _('maximum discount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Maximum discount amount (for percentage discount)'),
        validators=[MinValueValidator(0)]
    )
    min_purchase = models.DecimalField(
        _('minimum purchase amount'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    max_usage = models.PositiveIntegerField(
        _('maximum usage'),
        null=True,
        blank=True,
        help_text=_('Leave empty for unlimited usage')
    )
    used_count = models.PositiveIntegerField(_('times used'), default=0)
    is_active = models.BooleanField(_('is active'), default=True)
    valid_from = models.DateTimeField(_('valid from'))
    valid_until = models.DateTimeField(_('valid until'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('promo code')
        verbose_name_plural = _('promo codes')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['code'], name='promo_code_idx'),
            models.Index(fields=['is_active'], name='promo_active_idx'),
        ]
    
    def __str__(self):
        return f"{self.code} ({self.get_discount_display()})"
    
    def clean(self):
        if self.valid_until and self.valid_until <= self.valid_from:
            raise ValidationError({
                'valid_until': _('Valid until must be after valid from')
            })
        
        if self.discount_type == self.DISCOUNT_TYPE_PERCENTAGE and self.discount_value > 100:
            raise ValidationError({
                'discount_value': _('Percentage discount cannot be greater than 100%')
            })
    
    def is_valid(self, cart_total=0):
        """Check if the promo code is valid for the given cart total"""
        if not self.is_active:
            return False, _('This promo code is not active')
        
        now = timezone.now()
        if now < self.valid_from:
            return False, _('This promo code is not yet valid')
        
        if self.valid_until and now > self.valid_until:
            return False, _('This promo code has expired')
        
        if self.max_usage is not None and self.used_count >= self.max_usage:
            return False, _('This promo code has reached its maximum usage limit')
        
        if cart_total < self.min_purchase:
            return False, _(f'Minimum purchase amount of {self.min_purchase} is required')
        
        return True, _('Valid promo code')
    
    def calculate_discount(self, amount):
        """Calculate discount amount for the given total"""
        if self.discount_type == self.DISCOUNT_TYPE_PERCENTAGE:
            discount = (amount * self.discount_value) / 100
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        return min(self.discount_value, amount)
    
    def use(self):
        """Mark the promo code as used"""
        self.used_count += 1
        self.save(update_fields=['used_count'])


class Address(TimeStampedModel):
    """User address model"""
    ADDRESS_TYPE_CHOICES = [
        ('billing', _('Billing')),
        ('shipping', _('Shipping')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('user')
    )
    address_type = models.CharField(
        _('address type'),
        max_length=10,
        choices=ADDRESS_TYPE_CHOICES
    )
    full_name = models.CharField(_('full name'), max_length=100)
    phone = models.CharField(_('phone number'), max_length=20)
    address_line_1 = models.CharField(_('address line 1'), max_length=255)
    address_line_2 = models.CharField(_('address line 2'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state/province/region'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(_('country'), max_length=100)
    is_default = models.BooleanField(_('default address'), default=False)
    
    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ('-is_default', '-created_at')
        indexes = [
            models.Index(fields=['user', 'address_type'], name='user_address_type_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_address_type_display()} - {self.full_name}, {self.city}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address of each type per user
        if self.is_default:
            Address.objects.filter(
                user=self.user,
                address_type=self.address_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    def get_full_address(self):
        """Return formatted address as a single string"""
        parts = [
            self.full_name,
            self.address_line_1,
            self.address_line_2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country,
            f"Phone: {self.phone}"
        ]
        return '\n'.join(filter(None, parts))


class Order(TimeStampedModel):
    """Order model"""
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDED = 'refunded'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_PROCESSING, _('Processing')),
        (STATUS_SHIPPED, _('Shipped')),
        (STATUS_DELIVERED, _('Delivered')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_REFUNDED, _('Refunded')),
    ]
    
    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_REFUNDED = 'refunded'
    PAYMENT_STATUS_PARTIALLY_REFUNDED = 'partially_refunded'
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, _('Pending')),
        (PAYMENT_STATUS_PAID, _('Paid')),
        (PAYMENT_STATUS_FAILED, _('Failed')),
        (PAYMENT_STATUS_REFUNDED, _('Refunded')),
        (PAYMENT_STATUS_PARTIALLY_REFUNDED, _('Partially Refunded')),
    ]
    
    PAYMENT_METHOD_COD = 'cod'
    PAYMENT_METHOD_STRIPE = 'stripe'
    PAYMENT_METHOD_PAYPAL = 'paypal'
    
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_COD, _('Cash on Delivery')),
        (PAYMENT_METHOD_STRIPE, _('Credit/Debit Card (Stripe)')),
        (PAYMENT_METHOD_PAYPAL, _('PayPal')),
    ]
    
    order_number = models.CharField(
        _('order number'),
        max_length=20,
        unique=True,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name=_('user')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    payment_status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_STRIPE
    )
    payment_id = models.CharField(
        _('payment ID'),
        max_length=100,
        blank=True,
        help_text=_('Payment processor transaction ID')
    )
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        _('tax amount'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    delivery_boy = models.ForeignKey(
        'DeliveryBoy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders',
        verbose_name=_('delivery boy')
    )
    discount_amount = models.DecimalField(
        _('discount amount'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        _('total'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('promo code')
    )
    billing_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        related_name='billing_orders',
        verbose_name=_('billing address')
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shipping_orders',
        verbose_name=_('shipping address')
    )
    customer_note = models.TextField(_('customer note'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['order_number'], name='order_number_idx'),
            models.Index(fields=['status', 'payment_status'], name='order_status_idx'),
            models.Index(fields=['created_at'], name='order_created_at_idx'),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        self.total = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        super().save(*args, **kwargs)
    
    def _generate_order_number(self):
        """Generate a unique order number"""
        import random
        import string
        
        # Format: ORD-{timestamp}-{random 6 chars}
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD-{timestamp}-{random_str}"
    
    def mark_as_paid(self, payment_id=None):
        """Mark order as paid"""
        self.payment_status = self.PAYMENT_STATUS_PAID
        if payment_id:
            self.payment_id = payment_id
        self.save(update_fields=['payment_status', 'payment_id', 'updated_at'])
    
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in [self.STATUS_PENDING, self.STATUS_PROCESSING]
    
    def cancel(self):
        """Cancel the order"""
        if not self.can_cancel():
            raise ValidationError(_('This order cannot be cancelled'))
        
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=['status', 'updated_at'])
    
    def get_absolute_url(self):
        return reverse('store:order_detail', args=[self.order_number])


class OrderItem(TimeStampedModel):
    """Ordered items"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('product')
    )
    product_name = models.CharField(_('product name'), max_length=200)
    product_sku = models.CharField(_('SKU'), max_length=100, blank=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
    
    def get_cost(self):
        return self.price * self.quantity


class Payment(TimeStampedModel):
    """Payment details for orders"""
    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_COMPLETED = 'completed'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_REFUNDED = 'refunded'
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, _('Pending')),
        (PAYMENT_STATUS_COMPLETED, _('Completed')),
        (PAYMENT_STATUS_FAILED, _('Failed')),
        (PAYMENT_STATUS_REFUNDED, _('Refunded')),
    ]
    
    PAYMENT_METHOD_STRIPE = 'stripe'
    PAYMENT_METHOD_PAYPAL = 'paypal'
    PAYMENT_METHOD_COD = 'cod'
    
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_STRIPE, _('Credit/Debit Card (Stripe)')),
        (PAYMENT_METHOD_PAYPAL, _('PayPal')),
        (PAYMENT_METHOD_COD, _('Cash on Delivery')),
    ]
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name=_('order')
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    payment_status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=10,
        decimal_places=2
    )
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='INR'
    )
    transaction_id = models.CharField(
        _('transaction ID'),
        max_length=100,
        blank=True,
        help_text=_('Payment processor transaction ID')
    )
    payment_intent_id = models.CharField(
        _('payment intent ID'),
        max_length=100,
        blank=True,
        help_text=_('Stripe PaymentIntent ID')
    )
    payment_details = models.JSONField(
        _('payment details'),
        default=dict,
        blank=True,
        help_text=_('Raw payment response from the payment gateway')
    )
    failure_code = models.CharField(
        _('failure code'),
        max_length=50,
        blank=True,
        help_text=_('Error code if the payment failed')
    )
    failure_message = models.TextField(
        _('failure message'),
        blank=True,
        help_text=_('Error message if the payment failed')
    )
    
    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['transaction_id'], name='payment_txn_id_idx'),
            models.Index(fields=['payment_status'], name='payment_status_idx'),
        ]
    
    def __str__(self):
        return f"Payment for {self.order} ({self.get_payment_status_display()})"
    
    def mark_as_completed(self, transaction_id='', payment_details=None):
        """Mark payment as completed"""
        self.payment_status = self.PAYMENT_STATUS_COMPLETED
        self.transaction_id = transaction_id or self.transaction_id
        if payment_details is not None:
            self.payment_details = payment_details
        self.save()
        
        # Update order status
        self.order.mark_as_paid(transaction_id)
    
    def mark_as_failed(self, failure_code='', failure_message=''):
        """Mark payment as failed"""
        self.payment_status = self.PAYMENT_STATUS_FAILED
        self.failure_code = failure_code
        self.failure_message = failure_message
        self.save()
        
        # Update order status
        self.order.payment_status = Order.PAYMENT_STATUS_FAILED
        self.order.save(update_fields=['payment_status', 'updated_at'])


class ShippingMethod(TimeStampedModel):
    """Available shipping methods"""
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    min_order_amount = models.DecimalField(
        _('minimum order amount'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Minimum order amount for free shipping')
    )
    estimated_delivery_days = models.PositiveIntegerField(
        _('estimated delivery days'),
        default=3,
        help_text=_('Estimated delivery time in days')
    )
    
    class Meta:
        verbose_name = _('shipping method')
        verbose_name_plural = _('shipping methods')
        ordering = ('price',)
    
    def __str__(self):
        return self.name
    
    def is_available_for_order(self, order_total):
        """Check if this shipping method is available for the given order total"""
        if not self.is_active:
            return False
        return order_total >= self.min_order_amount


class SiteSettings(TimeStampedModel):
    """Site-wide settings"""
    site_name = models.CharField(_('site name'), max_length=100, default='Priyanka Superbazaar')
    site_logo = models.ImageField(_('site logo'), upload_to='site/', blank=True)
    site_favicon = models.ImageField(_('favicon'), upload_to='site/', blank=True)
    contact_email = models.EmailField(_('contact email'), default='contact@priyankasuperbazaar.com')
    contact_phone = models.CharField(_('contact phone'), max_length=20, default='+91 1234567890')
    address = models.TextField(_('address'), blank=True)
    facebook_url = models.URLField(_('Facebook URL'), blank=True)
    twitter_url = models.URLField(_('Twitter URL'), blank=True)
    instagram_url = models.URLField(_('Instagram URL'), blank=True)
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True)
    youtube_url = models.URLField(_('YouTube URL'), blank=True)
    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)
    meta_keywords = models.TextField(_('meta keywords'), blank=True)
    
    # Store contact details
    store_name = models.CharField(_('store name'), max_length=200, default='Priyanka Superbazaar')
    store_address_line1 = models.CharField(_('address line 1'), max_length=255, blank=True, default='123 Main Street')
    store_address_line2 = models.CharField(_('address line 2'), max_length=255, blank=True, default='Your City, Your State')
    store_country = models.CharField(_('country'), max_length=100, blank=True, default='India')
    store_phone = models.CharField(_('phone'), max_length=30, blank=True, default='+91 1234567890')
    store_email = models.EmailField(_('email'), blank=True, default='info@priyankasuperbazaar.com')
    store_hours = models.CharField(_('business hours'), max_length=255, blank=True, default='Everyday, 8:00 AM – 10:00 PM')

    # Order settings
    min_order_amount = models.DecimalField(
        _('minimum order amount'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Minimum order amount to place an order')
    )
    enable_cod = models.BooleanField(
        _('enable cash on delivery'),
        default=True,
        help_text=_('Allow customers to pay with cash on delivery')
    )
    
    # Maintenance mode
    maintenance_mode = models.BooleanField(
        _('maintenance mode'),
        default=False,
        help_text=_('Take the site down for maintenance')
    )
    maintenance_message = models.TextField(
        _('maintenance message'),
        blank=True,
        default='We are currently performing maintenance. Please check back soon.'
    )
    
    class Meta:
        verbose_name = _('site settings')
        verbose_name_plural = _('site settings')
    
    def __str__(self):
        return 'Site Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Get or create the site settings"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Offer(TimeStampedModel):
    """Homepage promotional offers/banners editable from admin."""
    title = models.CharField(_('title'), max_length=200)
    subtitle = models.CharField(_('subtitle'), max_length=255, blank=True)
    image = models.ImageField(_('image'), upload_to='offers/', blank=True, null=True)
    button_text = models.CharField(_('button text'), max_length=50, blank=True, default='Shop Now')
    button_url = models.CharField(_('button URL'), max_length=255, blank=True, help_text=_('Relative URL such as /products/ or full URL'))
    is_active = models.BooleanField(_('is active'), default=True)
    display_order = models.PositiveIntegerField(_('display order'), default=0)

    class Meta:
        verbose_name = _('offer')
        verbose_name_plural = _('offers')
        ordering = ('display_order', '-created_at')

    def __str__(self):
        return self.title


class DeliveryBoy(TimeStampedModel):
    """Delivery personnel who handle order deliveries"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_profile',
        verbose_name=_('user')
    )
    phone = models.CharField(
        _('phone number'),
        max_length=15,
        help_text=_('Contact number of the delivery boy')
    )
    address = models.TextField(
        _('address'),
        help_text=_('Current residential address')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Designates whether this delivery boy is active')
    )
    current_location = models.CharField(
        _('current location'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Last known location (latitude, longitude)')
    )
    vehicle_number = models.CharField(
        _('vehicle number'),
        max_length=20,
        blank=True,
        help_text=_('Vehicle registration number')
    )
    vehicle_type = models.CharField(
        _('vehicle type'),
        max_length=50,
        blank=True,
        help_text=_('e.g., Bike, Scooter, Car')
    )
    id_proof = models.ImageField(
        _('ID proof'),
        upload_to='delivery_boy/id_proofs/',
        help_text=_('Upload a scanned copy of ID proof (Aadhar, Driving License, etc.)')
    )
    aadhar_number = models.CharField(
        _('Aadhar number'),
        max_length=12,
        blank=True,
        help_text=_('12-digit Aadhar number')
    )
    pan_number = models.CharField(
        _('PAN number'),
        max_length=10,
        blank=True,
        help_text=_('10-character PAN number')
    )

    class Meta:
        verbose_name = _('delivery boy')
        verbose_name_plural = _('delivery boys')
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.phone})"

    def save(self, *args, **kwargs):
        # Ensure the user is marked as staff
        if not self.user.is_staff:
            self.user.is_staff = True
            self.user.save()
        super().save(*args, **kwargs)

    def get_active_orders(self):
        """Get all active delivery orders assigned to this delivery boy"""
        return self.delivery_orders.filter(
            status__in=[Order.STATUS_PENDING, Order.STATUS_PROCESSING, Order.STATUS_SHIPPED]
        )

    @property
    def total_deliveries(self):
        """Total number of completed deliveries"""
        return self.delivery_orders.filter(status='delivered').count()

    @property
    def average_rating(self):
        """Average rating from order deliveries"""
        # For now, return None as we don't have a rating system implemented yet
        # You can implement this later by adding a rating field to the Order model
        return None
