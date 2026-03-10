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
    Offer, DeliveryBoy, CustomerProfile, PasswordResetOTP, ProductVariant,
)

User = get_user_model()


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_featured')
    readonly_fields = ()


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('value', 'price', 'stock', 'is_active')


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'product', 'rating', 'comment', 'created', 'modified')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    can_delete = False
    readonly_fields = ('product', 'quantity')

    def has_add_permission(self, request, obj=None):
        return False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal', 'created', 'modified')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('name', 'slug', 'created', 'modified')
    list_filter = ('created', 'modified')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    date_hierarchy = 'created'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('name', 'category', 'price', 'discount_price', 'available', 'featured', 'created', 'modified')
    list_filter = ('category', 'available', 'featured', 'created', 'modified')
    search_fields = ('name', 'description', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category',)
    ordering = ('-created',)
    date_hierarchy = 'created'
    fields = (
        'category', 'name', 'slug', 'description',
        'price', 'discount_price', 'stock', 'available', 'featured',
        'unit_type', 'image',
        'created', 'modified',
    )
    inlines = [ProductVariantInline, ProductImageInline, ProductReviewInline]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('product', 'user', 'rating', 'is_approved', 'created')
    list_filter = ('rating', 'is_approved', 'created')
    search_fields = ('product__name', 'user__email', 'comment')
    ordering = ('-created',)
    date_hierarchy = 'created'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('user', 'product', 'created')
    list_filter = ('created',)
    search_fields = ('user__email', 'product__name')
    ordering = ('-created',)
    date_hierarchy = 'created'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('__str__', 'user', 'session_key', 'created', 'modified')
    list_filter = ('created', 'modified')
    search_fields = ('user__email', 'session_key')
    ordering = ('-modified',)
    date_hierarchy = 'created'
    inlines = [CartItemInline]


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'valid_from', 'valid_until', 'created', 'modified')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until', 'created')
    search_fields = ('code', 'description')
    ordering = ('-created',)
    date_hierarchy = 'valid_from'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('user', 'address_type', 'full_name', 'city', 'state', 'is_default', 'created')
    list_filter = ('address_type', 'is_default', 'city', 'state', 'country', 'created')
    search_fields = ('user__email', 'full_name', 'address_line_1', 'city', 'state', 'postal_code', 'country')
    ordering = ('-created',)
    date_hierarchy = 'created'
    raw_id_fields = ('user',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('order_number', 'user', 'status', 'payment_status', 'total', 'created', 'modified')
    list_filter = ('status', 'payment_status', 'payment_method', 'delivery_boy', 'created')
    search_fields = ('order_number', 'user__email', 'user__username')
    ordering = ('-created',)
    date_hierarchy = 'created'
    inlines = [OrderItemInline]

    def changelist_view(self, request, extra_context=None):
        """
        Add high-level sales statistics for the custom Order changelist template.
        """
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            cl = response.context_data.get("cl")
        except Exception:
            return response

        queryset = cl.queryset if hasattr(cl, "queryset") else self.get_queryset(request)

        # Consider only completed/paid orders for revenue numbers
        completed_qs = queryset.filter(
            Q(status__in=["completed", "delivered", "shipped"]) | Q(payment_status__in=["paid", "completed"])
        )

        agg = completed_qs.aggregate(
            total_revenue=Sum("total"),
            avg_order_value=Avg("total"),
        )

        total_revenue = agg.get("total_revenue") or 0
        avg_order_value = agg.get("avg_order_value") or 0

        sales_by_status = (
            completed_qs.values("status")
            .annotate(count=Count("id"), total=Sum("total"))
            .order_by("status")
        )

        top_products = (
            OrderItem.objects.filter(order__in=completed_qs)
            .values("product__name")
            .annotate(
                quantity=Sum("quantity"),
                total=Sum("subtotal"),
            )
            .order_by("-total")[:10]
        )

        response.context_data.update(
            {
                "total_revenue": total_revenue,
                "avg_order_value": avg_order_value,
                "sales_by_status": sales_by_status,
                "top_products": top_products,
            }
        )

        return response


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('order', 'product', 'product_name', 'price', 'quantity', 'subtotal', 'created')
    list_filter = ('created',)
    search_fields = ('order__order_number', 'product__name', 'product_name')
    ordering = ('-created',)
    date_hierarchy = 'created'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('order', 'payment_method', 'payment_status', 'amount', 'currency', 'created')
    list_filter = ('payment_method', 'payment_status', 'created')
    search_fields = ('order__order_number', 'transaction_id', 'payment_id')
    ordering = ('-created',)
    date_hierarchy = 'created'


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('name', 'is_active', 'price', 'min_order_amount', 'estimated_delivery_days', 'created')
    list_filter = ('is_active', 'created')
    search_fields = ('name',)
    ordering = ('price',)
    date_hierarchy = 'created'


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('site_name', 'contact_email', 'contact_phone', 'created', 'modified')
    ordering = ('-modified',)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('title', 'is_active', 'display_order', 'created', 'modified')
    list_filter = ('is_active', 'created')
    search_fields = ('title', 'subtitle')
    ordering = ('display_order', '-created')
    date_hierarchy = 'created'


@admin.register(DeliveryBoy)
class DeliveryBoyAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('user', 'phone', 'is_active', 'vehicle_type', 'created', 'modified')
    list_filter = ('is_active', 'vehicle_type', 'created')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone', 'vehicle_number')
    ordering = ('-created',)
    date_hierarchy = 'created'


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('user', 'phone', 'created', 'modified')
    list_filter = ('created',)
    search_fields = ('user__username', 'user__email', 'phone')
    ordering = ('-created',)
    date_hierarchy = 'created'


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    list_display = ('phone', 'otp', 'is_used', 'expires_at', 'created')
    list_filter = ('is_used', 'created')
    search_fields = ('phone', 'otp')
    ordering = ('-created',)
    date_hierarchy = 'created'
