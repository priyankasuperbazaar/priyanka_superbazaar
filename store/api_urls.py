from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as token_views
from . import api

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'categories', api.CategoryViewSet)
router.register(r'products', api.ProductViewSet)
router.register(r'reviews', api.ProductReviewViewSet)
router.register(r'wishlist', api.WishlistViewSet, basename='wishlist')
router.register(r'cart', api.CartViewSet, basename='cart')
router.register(r'addresses', api.AddressViewSet, basename='addresses')
router.register(r'orders', api.OrderViewSet, basename='orders')
router.register(r'shipping-methods', api.ShippingMethodViewSet)
router.register(r'site-settings', api.SiteSettingsViewSet)
router.register(r'offers', api.OfferViewSet)
router.register(r'delivery-boys', api.DeliveryBoyViewSet)

# API URL patterns
api_urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', token_views.obtain_auth_token, name='api_token_auth'),
    path('auth/register/', api.register, name='api_register'),
    path('auth/login/', api.login_view, name='api_login'),
    path('auth/send-otp/', api.send_otp, name='api_send_otp'),
    path('auth/verify-otp/', api.verify_otp, name='api_verify_otp'),
    path('checkout/', api.checkout_api, name='api_checkout'),
]

# Django expects `urlpatterns` when including this module.
urlpatterns = api_urlpatterns
