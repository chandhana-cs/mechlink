# mechanics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 🧰 Mechanic Dashboard & Profile
    path("dashboard/", views.mechanic_dashboard, name="mechanic_dashboard"),
    path("edit-profile/", views.edit_mechanic_profile, name="edit_mechanic_profile"),

    # 🧾 Service Requests (Accept / Reject / Complete)
    path("update-service/<int:request_id>/<str:action>/", views.update_service_request, name="update_service_request"),

    # 🛍 Product Management
    path("add-product/", views.add_product, name="add_product"),
    path("edit-product/<int:product_id>/", views.edit_product, name="edit_product"),
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),

    # 🛒 Shop, Cart & Checkout
    path("shop/", views.shop, name="shop"),
    path("cart/", views.cart, name="cart"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove-from-cart/<int:cart_item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("update-cart/<int:item_id>/", views.update_cart_quantity, name="update_cart_quantity"),
# 🛒 Checkout
path("checkout/<int:product_id>/", views.checkout, name="checkout"),
path("checkout/", views.checkout, name="checkout"),
path("payment/callback/", views.payment_callback, name="payment_callback"),
path("order/success/", views.order_success, name="order_success"),  # buy-now checkout


    # 🧾 Orders (Mechanic + Customer)
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
    path("update-order/<int:order_id>/<str:action>/", views.update_order_status, name="update_order_status"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("customer-order-update/<int:order_id>/<str:action>/", views.customer_update_order_status, name="customer_update_order_status"),
     path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    # 💳 Demo Razorpay Payment Flow
]
