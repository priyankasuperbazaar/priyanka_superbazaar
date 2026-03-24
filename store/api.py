from rest_framework import serializers, viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
import random
import json

from cloudinary.utils import cloudinary_url

from .models import (
    Category, Product, ProductImage, ProductVariant, CustomerProfile,
    PasswordResetOTP, ProductReview, Wishlist, Cart, CartItem,
    PromoCode, Address, Order, OrderItem, Payment, ShippingMethod,
    SiteSettings, Offer, DeliveryBoy
)
from .utils import (
    send_order_confirmation_email, send_order_status_update_email,
    send_order_confirmation_sms, calculate_tax, calculate_shipping_cost,
    send_registration_confirmation_email, send_registration_confirmation_sms
)


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        if not getattr(obj, 'image', None):
            return None
        try:
            url = getattr(obj.image, 'url', None)
            if url:
                return request.build_absolute_uri(url) if request and url.startswith('/') else url
        except Exception:
            pass

        try:
            public_id = str(obj.image)
            if public_id:
                url, _ = cloudinary_url(public_id, secure=True)
                return url
        except Exception:
            pass

        return None


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        if not getattr(obj, 'image', None):
            return None
        try:
            url = getattr(obj.image, 'url', None)
            if url:
                return request.build_absolute_uri(url) if request and url.startswith('/') else url
        except Exception:
            pass

        try:
            public_id = str(obj.image)
            if public_id:
                url, _ = cloudinary_url(public_id, secure=True)
                return url
        except Exception:
            pass

        return None


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_image_url = serializers.SerializerMethodField()
    category_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_main_image_url(self, obj):
        request = self.context.get('request')
        if not getattr(obj, 'image', None):
            return None
        try:
            url = getattr(obj.image, 'url', None)
            if url:
                return request.build_absolute_uri(url) if request and url.startswith('/') else url
        except Exception:
            pass

        try:
            public_id = str(obj.image)
            if public_id:
                url, _ = cloudinary_url(public_id, secure=True)
                return url
        except Exception:
            pass

        return None

    def get_category_image_url(self, obj):
        request = self.context.get('request')
        category = getattr(obj, 'category', None)
        if not category or not getattr(category, 'image', None):
            return None
        try:
            url = getattr(category.image, 'url', None)
            if url:
                return request.build_absolute_uri(url) if request and url.startswith('/') else url
        except Exception:
            pass

        try:
            public_id = str(category.image)
            if public_id:
                url, _ = cloudinary_url(public_id, secure=True)
                return url
        except Exception:
            pass

        return None


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = '__all__'


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductReview
        fields = '__all__'


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = '__all__'

    def get_total_price(self, obj):
        return obj.get_cost()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = '__all__'

    def get_total_price(self, obj):
        return obj.get_total_price()

    def get_total_quantity(self, obj):
        return obj.get_total_quantity()


class AddressSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Address
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    billing_address_details = AddressSerializer(source='billing_address', read_only=True)
    shipping_address_details = AddressSerializer(source='shipping_address', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = '__all__'


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = '__all__'


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'


class DeliveryBoySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = DeliveryBoy
        fields = '__all__'


# ViewSets
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(available=True).select_related('category').prefetch_related('images', 'variants')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'slug', 'description', 'category__name']

    def get_queryset(self):
        qs = super().get_queryset()

        category = self.request.query_params.get('category')
        if category:
            try:
                qs = qs.filter(category_id=int(category))
            except (TypeError, ValueError):
                qs = qs.filter(category__slug=category)

        featured = self.request.query_params.get('featured')
        if featured is not None:
            if str(featured).lower() in {'1', 'true', 'yes', 'y'}:
                qs = qs.filter(featured=True)
            elif str(featured).lower() in {'0', 'false', 'no', 'n'}:
                qs = qs.filter(featured=False)

        return qs

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        product = self.get_object()
        reviews = ProductReview.objects.filter(product=product, is_approved=True)
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.filter(is_approved=True)
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_approved=False)


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id, available=True)
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user,
                product=product
            )
            if not created:
                wishlist_item.delete()
                return Response({'status': 'removed'})
            return Response({'status': 'added'})
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id, available=True)
            variant = None
            if variant_id:
                variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)

            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant
            )
            if created:
                item.quantity = quantity
            else:
                item.quantity += quantity
            item.save()

            return Response({'status': 'added'})
        except (Product.DoesNotExist, ProductVariant.DoesNotExist):
            return Response({'error': 'Product not found'}, status=404)

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        cart = Cart.objects.get(user=request.user)
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()
            return Response({'status': 'updated'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart = Cart.objects.get(user=request.user)
        item_id = request.data.get('item_id')

        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            return Response({'status': 'removed'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related(
            'billing_address', 'shipping_address'
        ).prefetch_related('items')

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if not order.can_cancel():
            return Response({'error': 'Order cannot be cancelled'}, status=400)

        with transaction.atomic():
            order.cancel()
            try:
                send_order_status_update_email(order, 'Your order has been cancelled.')
            except Exception:
                pass

        return Response({'status': 'cancelled'})


class ShippingMethodViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShippingMethod.objects.filter(is_active=True)
    serializer_class = ShippingMethodSerializer
    permission_classes = [AllowAny]


class SiteSettingsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer
    permission_classes = [AllowAny]

    def list(self, request):
        settings = SiteSettings.load()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)


class OfferViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Offer.objects.filter(is_active=True)
    serializer_class = OfferSerializer
    permission_classes = [AllowAny]


class DeliveryBoyViewSet(viewsets.ModelViewSet):
    queryset = DeliveryBoy.objects.all()
    serializer_class = DeliveryBoySerializer
    permission_classes = [IsAdminUser]


class DeliveryOrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        if not hasattr(self.request.user, 'delivery_profile'):
            raise PermissionDenied('Delivery access required')
        delivery_boy = self.request.user.delivery_profile
        return Order.objects.filter(delivery_boy=delivery_boy).select_related(
            'billing_address', 'shipping_address'
        ).prefetch_related('items')

    @action(detail=False, methods=['get'])
    def active(self, request):
        qs = self.get_queryset().filter(status__in=[Order.STATUS_PENDING, Order.STATUS_PROCESSING, Order.STATUS_SHIPPED])
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        qs = self.get_queryset().filter(status=Order.STATUS_DELIVERED).order_by('-modified')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        try:
            order = self.get_object()
            new_status = str(request.data.get('status', '')).strip()

            allowed = {
                Order.STATUS_PROCESSING,
                Order.STATUS_SHIPPED,
                Order.STATUS_DELIVERED,
            }
            if new_status not in allowed:
                return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

            order.status = new_status
            order.save(update_fields=['status', 'modified'])
            return Response({'status': 'ok', 'order_number': order.order_number, 'new_status': order.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        try:
            order = self.get_object()
            method = str(request.data.get('method', '')).strip().lower()

            if method == 'cod':
                order.payment_method = Order.PAYMENT_METHOD_COD
            elif method in {'online', 'stripe'}:
                order.payment_method = Order.PAYMENT_METHOD_STRIPE
            else:
                return Response({'error': 'Invalid payment method'}, status=status.HTTP_400_BAD_REQUEST)

            order.mark_as_paid()
            return Response({'status': 'ok', 'order_number': order.order_number, 'payment_status': order.payment_status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def delivery_me(request):
    if not hasattr(request.user, 'delivery_profile'):
        return Response({'error': 'Delivery access required'}, status=status.HTTP_403_FORBIDDEN)
    serializer = DeliveryBoySerializer(request.user.delivery_profile)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    phone = request.data.get('phone')

    if not all([username, email, password, phone]):
        return Response({'error': 'All fields are required'}, status=400)

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', '')
        )
        CustomerProfile.objects.create(user=user, phone=phone)

        # Send confirmation emails/SMS
        try:
            send_registration_confirmation_email(user)
            send_registration_confirmation_sms(phone, user_name=user.get_full_name() or user.username)
        except Exception:
            pass

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    identifier = request.data.get('identifier')  # email, username, or phone
    password = request.data.get('password')

    if not identifier or not password:
        return Response({'error': 'Identifier and password are required'}, status=400)

    normalized = str(identifier).strip()
    normalized_no_spaces = normalized.replace(' ', '')

    username_for_auth = normalized
    try:
        User = get_user_model()
        if '@' in normalized:
            user_obj = User.objects.filter(email__iexact=normalized).first()
            if user_obj:
                username_for_auth = user_obj.get_username()
        else:
            phone_candidate = normalized_no_spaces
            if phone_candidate.startswith('+'):
                phone_candidate = phone_candidate[1:]

            if phone_candidate.isdigit() and len(phone_candidate) >= 10:
                profile = CustomerProfile.objects.select_related('user').filter(
                    phone__in=[normalized, normalized_no_spaces, phone_candidate]
                ).first()
                if profile and profile.user:
                    username_for_auth = profile.user.get_username()
    except Exception:
        username_for_auth = normalized

    user = authenticate(request, username=username_for_auth, password=password)
    if user:
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
    return Response({'error': 'Invalid credentials'}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    phone = request.data.get('phone')
    if not phone:
        return Response({'error': 'Phone number is required'}, status=400)

    try:
        profile = CustomerProfile.objects.select_related('user').filter(phone=phone).first()
        if not profile:
            return Response({'error': 'Phone number not registered'}, status=400)

        otp = f"{random.randint(100000, 999999)}"
        expires_at = timezone.now() + timezone.timedelta(seconds=300)  # 5 minutes

        PasswordResetOTP.objects.create(phone=phone, otp=otp, expires_at=expires_at)

        # Send OTP via SMS (implement as needed)
        try:
            from .utils import send_sms
            send_sms(phone, f"Your OTP is {otp}. Valid for 5 minutes.")
        except Exception:
            pass

        return Response({'message': 'OTP sent successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get('phone')
    otp = request.data.get('otp')
    new_password = request.data.get('new_password')

    if not all([phone, otp, new_password]):
        return Response({'error': 'All fields are required'}, status=400)

    try:
        otp_obj = PasswordResetOTP.objects.filter(
            phone=phone,
            otp=otp,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).order_by('-created').first()

        if not otp_obj:
            return Response({'error': 'Invalid or expired OTP'}, status=400)

        profile = CustomerProfile.objects.select_related('user').filter(phone=phone).first()
        if not profile:
            return Response({'error': 'User not found'}, status=400)

        user = profile.user
        user.set_password(new_password)
        user.save()

        otp_obj.is_used = True
        otp_obj.save()

        return Response({'message': 'Password reset successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_api(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=400)

    # Get checkout data from request
    shipping_address_id = request.data.get('shipping_address_id')
    billing_address_id = request.data.get('billing_address_id', shipping_address_id)
    shipping_method_id = request.data.get('shipping_method_id')
    promo_code = request.data.get('promo_code')

    promo = None

    try:
        shipping_address = Address.objects.get(id=shipping_address_id, user=request.user)
        billing_address = Address.objects.get(id=billing_address_id, user=request.user)

        subtotal = cart.get_total_price()
        discount_amount = Decimal('0.00')

        # Apply promo code if provided
        if promo_code:
            try:
                promo = PromoCode.objects.get(code__iexact=promo_code, is_active=True)
                is_valid, message = promo.is_valid(subtotal)
                if is_valid:
                    discount_amount = promo.calculate_discount(subtotal)
                else:
                    return Response({'error': message}, status=400)
            except PromoCode.DoesNotExist:
                return Response({'error': 'Invalid promo code'}, status=400)

        # Calculate shipping and tax
        shipping_method = None
        shipping_cost = Decimal('0.00')
        if shipping_method_id:
            shipping_method = ShippingMethod.objects.get(id=shipping_method_id, is_active=True)
            shipping_cost = calculate_shipping_cost(subtotal, shipping_method)

        tax_amount = calculate_tax(subtotal - discount_amount)
        total = subtotal + tax_amount + shipping_cost - discount_amount

        # Create order
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                billing_address=billing_address,
                shipping_address=shipping_address,
                promo_code=promo,
                customer_note=request.data.get('customer_note', ''),
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_cost=shipping_cost,
                discount_amount=discount_amount,
                total=total,
            )

            # Auto-assign an active delivery boy (best-effort)
            try:
                if order.delivery_boy_id is None:
                    candidates = DeliveryBoy.objects.filter(is_active=True)
                    if candidates.exists():
                        chosen = None
                        min_active = None
                        for dboy in candidates:
                            active_count = dboy.delivery_orders.filter(
                                status__in=[Order.STATUS_PENDING, Order.STATUS_PROCESSING, Order.STATUS_SHIPPED]
                            ).count()
                            if min_active is None or active_count < min_active:
                                chosen = dboy
                                min_active = active_count
                        if chosen is not None:
                            order.delivery_boy = chosen
                            order.save(update_fields=['delivery_boy', 'modified'])
            except Exception:
                pass

            # Create payment record
            Payment.objects.create(
                order=order,
                payment_method=Payment.PAYMENT_METHOD_COD,
                amount=total,
                payment_status=Payment.PAYMENT_STATUS_PENDING,
            )

            # Create order items and update stock
            for item in cart.items.all():
                price = item.product.discount_price or item.product.price
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=price,
                    quantity=item.quantity,
                )
                # Update stock
                if item.product.stock >= item.quantity:
                    item.product.stock -= item.quantity
                    item.product.save()

            # Use promo code
            if promo_code:
                promo.use()

            # Clear cart
            cart.clear()

            # Send confirmation
            try:
                send_order_confirmation_email(order)
                send_order_confirmation_sms(order)
            except Exception:
                pass

        return Response({
            'order_id': order.id,
            'order_number': order.order_number,
            'total': float(total),
            'message': f'Order placed successfully! Order #{order.order_number}'
        })

    except Exception as e:
        return Response({'error': str(e)}, status=400)
