import csv
import datetime
from django import forms
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, F, Q, Avg, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.conf import settings

from .models import (
    Category, Product, ProductImage, ProductReview, Wishlist, Cart, CartItem,
    PromoCode, Address, Order, OrderItem, Payment, ShippingMethod, SiteSettings,
    Offer, DeliveryBoy,
)

User = get_user_model()

# ====================
# Inlines
# ====================

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('preview_image',)
    fields = ('image', 'alt_text', 'is_featured', 'preview_image')
    
    def preview_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="auto" />')
        return "-"
    preview_image.short_description = _('Preview')


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('user', 'product', 'rating', 'comment', 'created_at')
    can_delete = False


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'get_cost')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False
    
    def get_cost(self, obj):
        return obj.get_cost()
    get_cost.short_description = _('Cost')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    readonly_fields = ('order_number', 'user', 'status', 'total', 'created_at')
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj):
        return False


# ====================
# Custom Filters
# ====================

class PriceRangeFilter(admin.SimpleListFilter):
    title = _('price range')
    parameter_name = 'price_range'
    
    def lookups(self, request, model_admin):
        return (
            ('0-1000', _('Under ₹1,000')),
            ('1000-5000', _('₹1,000 - ₹5,000')),
            ('5000-10000', _('₹5,000 - ₹10,000')),
            ('10000-50000', _('₹10,000 - ₹50,000')),
            ('50000+', _('Over ₹50,000')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '0-1000':
            return queryset.filter(price__lt=1000)
        if self.value() == '1000-5000':
            return queryset.filter(price__gte=1000, price__lt=5000)
        if self.value() == '5000-10000':
            return queryset.filter(price__gte=5000, price__lt=10000)
        if self.value() == '10000-50000':
            return queryset.filter(price__gte=10000, price__lt=50000)
        if self.value() == '50000+':
            return queryset.filter(price__gte=50000)


class StockFilter(admin.SimpleListFilter):
    title = _('stock status')
    parameter_name = 'stock_status'
    
    def lookups(self, request, model_admin):
        return (
            ('in_stock', _('In Stock')),
            ('out_of_stock', _('Out of Stock')),
            ('low_stock', _('Low Stock (Less than 10)')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(stock__gt=0)
        if self.value() == 'out_of_stock':
            return queryset.filter(stock=0)
        if self.value() == 'low_stock':
            return queryset.filter(stock__gt=0, stock__lt=10)


# ====================
# ModelAdmins
# ====================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'is_active')
        }),
        ('Images', {
            'fields': ('image', 'description')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            product_count=Count('products')
        )
    
    def product_count(self, obj):
        return obj.product_count
    product_count.admin_order_field = 'product_count'
    product_count.short_description = _('Products')


class ProductImageInline(admin.StackedInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_featured', 'preview')
    readonly_fields = ('preview',)
    
    def preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="150" height="auto" />')
        return ""
    preview.short_description = _('Preview')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'price',
        'discount_price',
        'available',
        'stock_status',
        'is_available',
        'featured',
        'created_at',
    )
    list_filter = ('category', 'available', 'featured', 'created_at', PriceRangeFilter, StockFilter)
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('price', 'discount_price', 'available', 'featured')
    readonly_fields = ('created_at', 'updated_at', 'preview_image')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category',)
    inlines = [ProductImageInline, ProductReviewInline]
    actions = ['make_featured', 'remove_featured', 'export_selected_products']
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price')
        }),
        ('Inventory', {
            'fields': ('stock', 'available')
        }),
        ('Display', {
            'fields': ('featured', 'image', 'preview_image')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def preview_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="200" height="auto" />')
        return "No Image"
    preview_image.short_description = _('Preview')
    
    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: red;">Out of Stock</span>')
        elif obj.stock < 10:
            return format_html(f'<span style="color: orange;">Low ({obj.stock})</span>')
        return obj.stock
    stock_status.short_description = _('Stock Status')
    
    def is_available(self, obj):
        return obj.available
    is_available.boolean = True
    is_available.short_description = _('Available')
    
    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} products marked as featured.', messages.SUCCESS)
    make_featured.short_description = _('Mark selected products as featured')
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} products removed from featured.', messages.SUCCESS)
    remove_featured.short_description = _('Remove selected products from featured')
    
    def export_selected_products(self, request, queryset):
        # This will be handled by ExportActionMixin
        pass
    export_selected_products.short_description = _('Export selected products')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reviews approved.', messages.SUCCESS)
    approve_reviews.short_description = _('Approve selected reviews')
    
    def disapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} reviews disapproved.', messages.SUCCESS)
    disapprove_reviews.short_description = _('Disapprove selected reviews')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'product__name')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'product')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'get_cost')
    
    def get_cost(self, obj):
        return obj.get_cost()
    get_cost.short_description = _('Cost')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'item_count', 'total_price', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('user__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            item_count=Count('items'),
            total_price=Sum(F('items__product__price') * F('items__quantity'))
        )
    
    def item_count(self, obj):
        return obj.item_count
    item_count.admin_order_field = 'item_count'
    item_count.short_description = _('Items')
    
    def total_price(self, obj):
        return f'₹{obj.total_price or 0:.2f}'
    total_price.admin_order_field = 'total_price'
    total_price.short_description = _('Total Price')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'valid_from', 'valid_until', 'usage_count', 'max_usage')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('usage_count', 'created_at', 'updated_at')
    date_hierarchy = 'valid_from'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('orders')
        )
    
    def usage_count(self, obj):
        return obj.usage_count
    usage_count.admin_order_field = 'usage_count'
    usage_count.short_description = _('Usage Count')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_type', 'full_name', 'city', 'state', 'is_default')
    list_filter = ('address_type', 'is_default', 'city', 'state', 'country')
    search_fields = ('user__email', 'full_name', 'address_line_1', 'city', 'state', 'postal_code', 'country')
    list_editable = ('is_default',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    ordering = ('display_order', '-created_at')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal')
    
    def has_add_permission(self, request, obj):
        return False


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
        widgets = {
            'user': AutocompleteSelect(
                field=Order._meta.get_field('user'),
                admin_site=admin.site
            ),
            'billing_address': AutocompleteSelect(
                field=Order._meta.get_field('billing_address'),
                admin_site=admin.site
            ),
            'shipping_address': AutocompleteSelect(
                field=Order._meta.get_field('shipping_address'),
                admin_site=admin.site
            ),
            'promo_code': AutocompleteSelect(
                field=Order._meta.get_field('promo_code'),
                admin_site=admin.site
            ),
            'delivery_boy': AutocompleteSelect(
                field=Order._meta.get_field('delivery_boy'),
                admin_site=admin.site
            ),
        }


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    list_display = ('order_number', 'customer_name', 'customer_email', 'customer_phone', 'customer_address', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'delivery_boy', 'created_at')
    search_fields = (
        'order_number',
        'user__email',
        'user__first_name',
        'user__last_name',
        'user__username',
        'billing_address__full_name',
        'billing_address__phone',
        'billing_address__city',
        'billing_address__state',
        'shipping_address__full_name',
        'shipping_address__phone',
        'shipping_address__city',
        'shipping_address__state',
        'delivery_boy__user__first_name',
        'delivery_boy__user__last_name',
        'delivery_boy__user__email',
    )
    list_editable = ('status', 'payment_status')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'ip_address', 'payment_details_display', 'customer_info_display')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    actions = ['export_orders_csv', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'customer_note', 'ip_address')
        }),
        ('Customer Information', {
            'fields': ('customer_info_display',)
        }),
        ('Delivery', {
            'fields': ('delivery_boy',),
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'payment_method', 'payment_id', 'payment_details_display')
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total')
        }),
        ('Address Information', {
            'classes': ('collapse',),
            'fields': ('billing_address', 'shipping_address')
        }),
        ('Promo Code', {
            'classes': ('collapse',),
            'fields': ('promo_code',)
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def payment_details_display(self, obj):
        if obj.payment_id:
            return format_html('<a href="{}" target="_blank">View in Stripe Dashboard</a>', 
                             f"https://dashboard.stripe.com/payments/{obj.payment_id}")
        return "-"
    payment_details_display.short_description = _('Payment Details')
    
    def customer_name(self, obj):
        """Display customer name"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        elif obj.shipping_address:
            return obj.shipping_address.full_name
        elif obj.billing_address:
            return obj.billing_address.full_name
        return "-"
    customer_name.short_description = _('Customer Name')
    customer_name.admin_order_field = 'user__first_name'
    
    def customer_email(self, obj):
        """Display customer email"""
        if obj.user and obj.user.email:
            return format_html('<a href="mailto:{}">{}</a>', obj.user.email, obj.user.email)
        return "-"
    customer_email.short_description = _('Email')
    customer_email.admin_order_field = 'user__email'
    
    def customer_phone(self, obj):
        """Display customer phone number"""
        if obj.shipping_address and obj.shipping_address.phone:
            return format_html('<a href="tel:{}">{}</a>', obj.shipping_address.phone, obj.shipping_address.phone)
        elif obj.billing_address and obj.billing_address.phone:
            return format_html('<a href="tel:{}">{}</a>', obj.billing_address.phone, obj.billing_address.phone)
        return "-"
    customer_phone.short_description = _('Phone')
    
    def customer_address(self, obj):
        """Display customer address"""
        address = obj.shipping_address or obj.billing_address
        if address:
            address_parts = [
                address.address_line_1,
                address.address_line_2 if address.address_line_2 else None,
                f"{address.city}, {address.state} {address.postal_code}",
                address.country
            ]
            address_str = ", ".join([part for part in address_parts if part])
            return format_html('<span title="{}">{}</span>', address_str, address.city if address.city else "-")
        return "-"
    customer_address.short_description = _('Address')
    
    def customer_info_display(self, obj):
        """Display detailed customer information in detail view"""
        info_parts = []
        
        if obj.user:
            info_parts.append(f"<strong>Username:</strong> {obj.user.username}")
            if obj.user.email:
                info_parts.append(f"<strong>Email:</strong> <a href='mailto:{obj.user.email}'>{obj.user.email}</a>")
            if obj.user.get_full_name():
                info_parts.append(f"<strong>Full Name:</strong> {obj.user.get_full_name()}")
        
        address = obj.shipping_address or obj.billing_address
        if address:
            info_parts.append(f"<strong>Phone:</strong> <a href='tel:{address.phone}'>{address.phone}</a>")
            info_parts.append(f"<strong>Address:</strong> {address.get_full_address().replace(chr(10), '<br>')}")
        
        if info_parts:
            return format_html("<br>".join(info_parts))
        return "-"
    customer_info_display.short_description = _('Customer Information')
    
    def total_amount(self, obj):
        return f'₹{obj.total:.2f}'
    total_amount.admin_order_field = 'total'
    total_amount.short_description = _('Total')
    
    def export_orders_csv(self, request, queryset):
        # This will be handled by ExportActionMixin
        pass
    export_orders_csv.short_description = _('Export selected orders to CSV')
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_PROCESSING)
        self.message_user(request, f'{updated} orders marked as processing.', messages.SUCCESS)
    mark_as_processing.short_description = _('Mark selected orders as processing')
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_SHIPPED)
        self.message_user(request, f'{updated} orders marked as shipped.', messages.SUCCESS)
    mark_as_shipped.short_description = _('Mark selected orders as shipped')
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_DELIVERED, payment_status=Order.PAYMENT_STATUS_PAID)
        self.message_user(request, f'{updated} orders marked as delivered.', messages.SUCCESS)
    mark_as_delivered.short_description = _('Mark selected orders as delivered')
    
    def mark_as_cancelled(self, request, queryset):
        updated = 0
        for order in queryset:
            if order.can_cancel():
                order.cancel()
                updated += 1
        self.message_user(request, f'{updated} orders cancelled.', messages.SUCCESS)
    mark_as_cancelled.short_description = _('Cancel selected orders')
    
    change_list_template = 'admin/store/order/change_list.html'
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        if not hasattr(response, 'context_data'):
            return response
            
        # Sales statistics
        today = timezone.now().date()
        last_week = today - datetime.timedelta(days=7)
        last_month = today - datetime.timedelta(days=30)
        
        # Daily sales for the last 7 days
        daily_sales = (
            Order.objects
            .filter(created_at__date__gte=last_week)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(total=Sum('total'))
            .order_by('day')
        )
        
        # Monthly sales for the last 12 months
        monthly_sales = (
            Order.objects
            .filter(created_at__date__gte=last_month)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('total'))
            .order_by('month')
        )
        
        # Sales by status
        sales_by_status = (
            Order.objects
            .values('status')
            .annotate(count=Count('id'), total=Sum('total'))
            .order_by('-total')
        )
        
        # Top selling products
        from django.db.models import ExpressionWrapper, DecimalField, F
        
        top_products = (
            OrderItem.objects
            .values('product__name')
            .annotate(
                quantity=Sum('quantity'),
                price=Sum('price')
            )
            .annotate(
                total=ExpressionWrapper(
                    F('quantity') * F('price'),
                    output_field=DecimalField()
                )
            )
            .order_by('-quantity')[:10]
        )
        
        response.context_data.update({
            'daily_sales': daily_sales,
            'monthly_sales': monthly_sales,
            'sales_by_status': sales_by_status,
            'top_products': top_products,
            'total_orders': Order.objects.count(),
            'total_revenue': Order.objects.aggregate(total=Sum('total'))['total'] or 0,
            'avg_order_value': Order.objects.aggregate(avg=Avg('total'))['avg'] or 0,
        })
        
        return response


@admin.register(DeliveryBoy)
class DeliveryBoyAdmin(admin.ModelAdmin):
    """Admin interface for managing delivery boys"""
    list_display = ('user', 'phone', 'is_active', 'vehicle_type', 'total_deliveries', 'average_rating')
    list_filter = ('is_active', 'vehicle_type', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone', 'vehicle_number')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at', 'total_deliveries', 'average_rating')
    fieldsets = (
        (None, {
            'fields': ('user', 'phone', 'address', 'is_active')
        }),
        ('Vehicle Information', {
            'fields': ('vehicle_type', 'vehicle_number')
        }),
        ('Verification', {
            'fields': ('id_proof', 'aadhar_number', 'pan_number')
        }),
        ('Location', {
            'fields': ('current_location',)
        }),
        ('Statistics', {
            'fields': ('total_deliveries', 'average_rating')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make user field read-only when editing"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        """Set the user as staff when creating a new delivery boy"""
        if not change:  # Only for new objects
            obj.user.is_staff = True
            obj.user.save()
        super().save_model(request, obj, form, change)
