from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import Product, Order, CartItem, MechanicProfile
from services.models import ServiceRequest, Notification, ChatMessage, MechanicRating
from users.models import Feedback
from math import radians, sin, cos, sqrt, atan2
import json


# 🧰 Mechanic Dashboard (Main)
@login_required
def mechanic_dashboard(request):
    if request.user.role != "mechanic":
        return redirect("home")

    mechanic = request.user
    mechanic_profile = MechanicProfile.objects.filter(user=mechanic).first()

    service_requests = ServiceRequest.objects.filter(mechanic=mechanic).order_by("-created_at")
    notifications = Notification.objects.filter(recipient=mechanic).order_by("-created_at")[:5]
    products = Product.objects.filter(mechanic=mechanic_profile)
    all_orders = Order.objects.filter(product__mechanic=mechanic_profile).order_by("-ordered_at")

    # 🧩 Split by status for tabs
    paid_orders = all_orders.filter(status="Paid")
    accepted_orders = all_orders.filter(status="Accepted")
    processing_orders = all_orders.filter(status="Processing")
    delivered_orders = all_orders.filter(status="Delivered")
    cancelled_orders = all_orders.filter(status="Cancelled")

    feedbacks = Feedback.objects.filter(mechanic=mechanic).order_by("-created_at")
    ratings = MechanicRating.objects.filter(mechanic=mechanic)
    average_rating = ratings.aggregate(Avg("rating"))["rating__avg"] or 0
    rating_breakdown = {i: ratings.filter(rating=i).count() for i in range(5, 0, -1)}
    total_ratings = sum(rating_breakdown.values())

    context = {
        "mechanic_profile": mechanic_profile,
        "service_requests": service_requests,
        "notifications": notifications,
        "products": products,
        "all_orders": all_orders,
        "paid_orders": paid_orders,
        "accepted_orders": accepted_orders,
        "processing_orders": processing_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "feedbacks": feedbacks,
        "average_rating": round(average_rating, 1),
        "rating_breakdown": rating_breakdown,
        "total_ratings": total_ratings,
    }
    return render(request, "mechanics/mechanic_dashboard.html", context)



# 🧾 ✅ Accept / Reject / Complete Service Request
@login_required
@require_POST
@csrf_protect
def update_service_request(request, request_id, action):
    req = get_object_or_404(ServiceRequest, id=request_id)

    if request.user.role != "mechanic":
        messages.error(request, "You are not authorized for this action.")
        return redirect("home")

    # Only assigned mechanic can update except for 'accept'
    if req.mechanic != request.user and action != "accept":
        messages.error(request, "You are not assigned to this request.")
        return redirect("mechanic_dashboard")

    if action == "accept":
        req.status = "accepted"
        req.mechanic = request.user
        Notification.objects.create(
            recipient=req.user,
            sender=request.user,
            message=f"🧰 Your service request has been accepted by {request.user.username}.",
            link=reverse("chat_view", args=[req.id]),
        )
        messages.success(request, "✅ Service request accepted.")
    elif action == "reject":
        req.status = "rejected"
        Notification.objects.create(
            recipient=req.user,
            sender=request.user,
            message=f"❌ Your service request has been rejected by {request.user.username}.",
        )
        messages.warning(request, "❌ Service request rejected.")
    elif action == "complete":
        req.status = "completed"
        Notification.objects.create(
            recipient=req.user,
            sender=request.user,
            message=f"✅ Your service request #{req.id} has been completed by {request.user.username}.",
        )
        messages.success(request, "✅ Service marked as completed.")
    else:
        messages.error(request, "Invalid action.")
        return redirect("mechanic_dashboard")

    req.save()
    return redirect("mechanic_dashboard")


# 🛒 Update Cart Quantity
@login_required
def update_cart_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'quantity': cart_item.quantity})
    return redirect('cart')


# 🧰 Mechanic Profile Edit
@login_required
def edit_mechanic_profile(request):
    if request.user.role != "mechanic":
        return redirect("home")

    profile, created = MechanicProfile.objects.get_or_create(user=request.user)

    MECHANIC_TYPE_CHOICES = [
        ('two_wheeler', 'Two-Wheeler Mechanic'),
        ('automotive', 'Automotive Mechanic'),
        ('heavy_vehicle', 'Heavy Vehicle Mechanic'),
    ]

    if request.method == "POST":
        profile.shop_name = request.POST.get("shop_name", "").strip()
        profile.phone = request.POST.get("phone", "").strip()

        # ✅ Fix: Convert mechanic types list → comma-separated string
        selected_types = request.POST.getlist("mechanic_types")
        profile.mechanic_types = ",".join(selected_types)

        # 🗺 Coordinates
        lat = request.POST.get("latitude")
        lon = request.POST.get("longitude")

        # 📍 Reverse geocode fields
        location = request.POST.get("location", "").strip()
        pincode = request.POST.get("pincode", "").strip()

        try:
            lat = float(lat) if lat else None
            lon = float(lon) if lon else None
            if lat is not None and not (-90 <= lat <= 90):
                raise ValueError("Invalid latitude.")
            if lon is not None and not (-180 <= lon <= 180):
                raise ValueError("Invalid longitude.")
        except ValueError:
            messages.error(request, "⚠️ Invalid map coordinates. Please reselect your workshop location.")
            return redirect("edit_mechanic_profile")

        # ✅ Save map-based info
        profile.latitude = lat
        profile.longitude = lon
        profile.location = location       # string from reverse geocode
        profile.pincode = pincode         # string from reverse geocode
        profile.save()

        messages.success(request, "✅ Workshop profile updated successfully!")
        return redirect("mechanic_dashboard")

    return render(
        request,
        "mechanics/edit_mechanic_profile.html",
        {
            "profile": profile,
            "mechanic_type_choices": MECHANIC_TYPE_CHOICES,
        },
    )



# 🛍 Product Management
@login_required
def add_product(request):
    if request.user.role != "mechanic":
        return redirect("home")

    profile, _ = MechanicProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        image = request.FILES.get("image")

        if not all([name, description, price, stock]):
            messages.error(request, "⚠️ Please fill all fields.")
            return redirect("add_product")

        Product.objects.create(
            mechanic=profile,
            name=name,
            description=description,
            price=price,
            stock=stock,
            image=image,
        )
        messages.success(request, f"✅ '{name}' added successfully.")
        return redirect("mechanic_dashboard")

    return render(request, "mechanics/add_product.html")


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'mechanics/product_detail.html', {'product': product})


# 🛒 Shop, Cart & Checkout (Customer)
@login_required
def shop(request):
    products = Product.objects.all().order_by("-created_at")
    return render(request, "mechanics/shop.html", {"products": products})


@login_required
def order_detail(request, order_id):
    mechanic_profile = MechanicProfile.objects.filter(user=request.user).first()
    order = get_object_or_404(Order, id=order_id, product__mechanic=mechanic_profile)
    return render(request, "mechanics/order_detail.html", {"order": order})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"✅ {product.name} added to cart.")
    return redirect("cart")


@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.total_price() for item in cart_items)
    return render(request, "mechanics/cart.html", {"cart_items": cart_items, "total_price": total_price})


@login_required
def remove_from_cart(request, cart_item_id):
    item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    item.delete()
    messages.warning(request, "🗑️ Item removed from your cart.")
    return redirect("cart")


import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Order  # adjust model imports

import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import razorpay
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import Product, Order

@login_required
def checkout(request, product_id):
    """Checkout page — Razorpay integrated for Buy Now only"""

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    product = get_object_or_404(Product, id=product_id)
    total_price = product.price
    amount_paise = int(total_price * 100)

    if request.method == "POST":
        address = request.POST.get("address", "").strip()
        pincode = request.POST.get("pincode", "").strip()

        if not address or not pincode:
            messages.error(request, "⚠️ Please enter address and pincode to proceed.")
            return redirect("checkout", product_id=product.id)

        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": "1",
        })

        order = Order.objects.create(
            customer=request.user,
            product=product,
            quantity=1,
            total_price=total_price,
            status="Pending",
            razorpay_order_id=razorpay_order["id"],
            address=address,
            pincode=pincode,
        )

        context = {
            "product": product,
            "total_price": total_price,
            "razorpay_order_id": razorpay_order["id"],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "amount": amount_paise,
            "currency": "INR",
            "order": order,
        }
        return render(request, "mechanics/checkout_payment.html", context)

    return render(request, "mechanics/checkout.html", {"product": product, "total_price": total_price})



# 💳 Order Status Update by Mechanic
@login_required
def update_order_status(request, order_id, action):
    """Mechanic updates order status (Accept, Processing, Deliver, Cancel)."""
    mechanic_profile = MechanicProfile.objects.filter(user=request.user).first()
    if not mechanic_profile:
        messages.error(request, "⚠️ Only mechanics can update orders.")
        return redirect("home")

    # Ensure this order belongs to the mechanic
    order = get_object_or_404(Order, id=order_id, product__mechanic=mechanic_profile)

    if action == "accept":
        order.status = "Accepted"
        messages.success(request, f"✅ Order #{order.id} accepted successfully.")
    elif action == "processing":
        order.status = "Processing"
        messages.info(request, f"⚙️ Order #{order.id} is now being processed.")
    elif action == "deliver":
        order.status = "Delivered"
        messages.success(request, f"📦 Order #{order.id} delivered successfully.")
    elif action == "cancel":
        order.status = "Cancelled"
        messages.warning(request, f"❌ Order #{order.id} cancelled.")
    else:
        messages.error(request, "⚠️ Invalid action.")
        return redirect("mechanic_dashboard")

    order.save()
    return redirect("mechanic_dashboard")



@login_required
def my_orders(request):
    orders = Order.objects.filter(customer=request.user).order_by('-ordered_at')
    return render(request, 'mechanics/my_orders.html', {'orders': orders})


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, mechanic__user=request.user)
    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.stock = request.POST.get("stock")
        image = request.FILES.get("image")
        if image:
            product.image = image
        product.save()
        messages.success(request, f"✅ '{product.name}' updated successfully.")
        return redirect("mechanic_dashboard")
    return render(request, "mechanics/edit_product.html", {"product": product})


@csrf_exempt
def payment_callback(request):
    """Verify Razorpay payment and mark order as Paid."""
    if request.method == "POST":
        try:
            data = request.POST or request.body.decode()
            if isinstance(data, str):
                from urllib.parse import parse_qs
                data = {k: v[0] for k, v in parse_qs(data).items()}

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            params_dict = {
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature'),
            }

            # ✅ Verify Razorpay signature
            client.utility.verify_payment_signature(params_dict)

            # ✅ Find the order in DB
            order = get_object_or_404(Order, razorpay_order_id=data.get('razorpay_order_id'))

            # ✅ Update order details
            order.razorpay_payment_id = data.get('razorpay_payment_id')
            order.razorpay_signature = data.get('razorpay_signature')
            order.status = "Paid"
            order.phone = data.get('phone') or order.phone
            order.address = data.get('address') or order.address
            order.save()

            # 🟢 Redirect with success message
            messages.success(request, "✅ Payment successful! Your order has been placed.")
            return redirect("order_success")

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "❌ Payment verification failed. Please try again.")
        except Exception as e:
            messages.error(request, f"⚠️ Unexpected error: {str(e)}")

    # 🔁 If something goes wrong, go back to orders
    return redirect("my_orders")


@login_required
def order_success(request):
    """Order confirmation after payment."""
    latest_order = Order.objects.filter(customer=request.user).order_by("-ordered_at").first()
    return render(request, "mechanics/order_success.html", {"order": latest_order})

# 🧾 Customer Cancelling Order
@login_required
def customer_update_order_status(request, order_id, action):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    if action == "cancel" and order.status in ["Pending", "Processing", "Accepted"]:
        order.status = "Cancelled"
        order.save()
        messages.success(request, f"❌ Your order #{order.id} has been cancelled.")
    else:
        messages.error(request, "You cannot cancel this order at this stage.")

    return redirect("my_orders")

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Product  # adjust import to your Product model path

@login_required
def delete_product(request, pk):
    # Only allow deletion via POST for safety
    product = get_object_or_404(Product, id=pk)

    # Optional: restrict to product owner/mechanic, adjust as needed:
    # if product.owner != request.user:
    #     messages.error(request, "You don't have permission to delete that product.")
    #     return redirect('mechanic_dashboard')

    if request.method == "POST":
        product.delete()
        messages.success(request, "✅ Product deleted.")
        return redirect("mechanic_dashboard")  # or whichever view name you want to return to

    # If GET request, optionally redirect (or render a confirm template)
    messages.info(request, "Please confirm deletion.")
    return redirect("mechanic_dashboard")

