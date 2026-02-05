from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product-list"),  # used in navbar
    path("shop/", views.product_list, name="product_list"),  # alias
    path("category/<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    path("products/<int:id>/<slug:slug>/", views.product_detail, name="product_detail"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("account/signup/", views.account_signup, name="account_signup"),
    path("account/profile/", views.account_profile, name="account_profile"),
    path("account/orders/", views.account_orders, name="account_orders"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/track/", views.track_order, name="order_track"),
    path("order/success/<str:order_number>/", views.order_success, name="order_success"),
    # Wishlist URLs
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/add/<int:product_id>/", views.wishlist_add, name="wishlist_add"),
    path("wishlist/remove/<int:product_id>/", views.wishlist_remove, name="wishlist_remove"),
    
    # Delivery URLs
    path('delivery/login/', views.delivery_login, name='delivery_login'),
    path('delivery/logout/', views.delivery_logout, name='delivery_logout'),
    path('delivery/dashboard/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/orders/<str:order_number>/', views.delivery_order_detail, name='delivery_order_detail'),
    path('delivery/orders/<str:order_number>/update/', views.delivery_order_update, name='delivery_order_update'),
    path('delivery/location/update/', views.delivery_update_location, name='delivery_update_location'),
    
    # Product Reviews
    path("product/<int:product_id>/review/", views.product_review_create, name="product_review_create"),
    
    # Account Management
    path("account/profile/edit/", views.account_profile_edit, name="account_profile_edit"),
    path("account/password/change/", views.account_change_password, name="account_change_password"),
    
    # Address Management
    path("account/addresses/", views.address_list, name="address_list"),
    path("account/address/add/", views.address_create, name="address_create"),
    path("account/address/<int:address_id>/edit/", views.address_edit, name="address_edit"),
    path("account/address/<int:address_id>/delete/", views.address_delete, name="address_delete"),
    
    # Order Management
    path("order/<str:order_number>/cancel/", views.order_cancel, name="order_cancel"),
    path("order/<str:order_number>/invoice/", views.order_invoice, name="order_invoice"),
    
    # Promo Code
    path("checkout/promo-code/apply/", views.apply_promo_code, name="apply_promo_code"),
    path("checkout/promo-code/set/", views.set_promo_code, name="set_promo_code"),
]
