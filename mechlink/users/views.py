# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Feedback
from django.contrib.auth.decorators import login_required
from django.db import models

from users.models import CustomUser
from mechanics.models import MechanicProfile, Product, Order
from services.models import ServiceRequest, Notification
from services.models import MechanicRating
from django.db.models import Avg


# 🏠 HOME PAGE
def home(request):
    return render(request, 'home.html')


# 🧾 REGISTER
def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role', 'customer')

        # ✅ Password match check
        if password != confirm_password:
            messages.error(request, "❌ Passwords do not match.")
            return redirect('register')

        # ✅ Unique username check
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "❌ Username already exists.")
            return redirect('register')

        # ✅ Create user
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )

        messages.success(request, "✅ Account created successfully! Please log in.")
        return redirect('login')

    return render(request, 'users/register.html')


# 🔑 LOGIN
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if user.is_admin():
                return redirect('admin_dashboard')
            elif user.is_mechanic():
                return redirect('mechanic_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, "❌ Invalid username or password.")
    return render(request, 'users/login.html')


# 🚪 LOGOUT
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "👋 You have logged out successfully.")
    return redirect('login')


# 👤 USER DASHBOARD
@login_required
def user_dashboard(request):
    if not request.user.is_customer():
        return redirect('home')

    recent_orders = Order.objects.filter(customer=request.user).order_by('-ordered_at')[:5]
    service_requests = ServiceRequest.objects.filter(user=request.user).order_by('-created_at')
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]

    return render(request, 'users/user_dashboard.html', {
        'recent_orders': recent_orders,
        'service_requests': service_requests,
        'notifications': notifications,
    })


# 🧰 RAISE REQUEST (Find Nearby Mechanics)
from math import radians, sin, cos, sqrt, atan2


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from math import radians, sin, cos, sqrt, atan2

from services.models import ServiceRequest, Notification, MechanicRating
from users.models import CustomUser, Feedback
from mechanics.models import MechanicProfile


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from math import radians, sin, cos, sqrt, atan2

from users.models import CustomUser, Feedback
from services.models import ServiceRequest, Notification, MechanicRating




# 🧾 MY ORDERS
@login_required
def my_orders(request):
    orders = Order.objects.filter(customer=request.user).order_by('-ordered_at')
    return render(request, "users/my_orders.html", {"orders": orders})



# 📋 MY REQUESTS


@login_required
def my_requests(request):
    if not request.user.is_customer():
        return redirect('home')

    requests = ServiceRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'services/my_requests.html', {'requests': requests})



# 🧑‍💼 ADMIN DASHBOARD
@login_required
def admin_dashboard(request):
    if not request.user.is_admin():
        return redirect('home')

    users = CustomUser.objects.all().order_by('-date_joined')
    service_requests = ServiceRequest.objects.all().order_by('-created_at')
    orders = Order.objects.all().order_by('-ordered_at')
    products = Product.objects.all().order_by('-created_at')

    stats = {
        "total_users": users.count(),
        "total_mechanics": users.filter(role="mechanic").count(),
        "total_customers": users.filter(role="customer").count(),
        "total_orders": orders.count(),
        "total_requests": service_requests.count(),
        "total_products": products.count(),
    }

    return render(request, 'users/admin_dashboard.html', {
        "users": users,
        "orders": orders,
        "products": products,
        "service_requests": service_requests,
        "stats": stats,
    })


# ✅ ADMIN APPROVE / REJECT REQUESTS
@login_required
def admin_approve_request(request, request_id):
    if not request.user.is_admin():
        return redirect('home')
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    service_request.status = 'approved'
    service_request.save()
    messages.success(request, f"✅ Request #{request_id} approved.")
    return redirect('admin_dashboard')


@login_required
def admin_reject_request(request, request_id):
    if not request.user.is_admin():
        return redirect('home')
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    service_request.status = 'rejected'
    service_request.save()
    messages.warning(request, f"❌ Request #{request_id} rejected.")
    return redirect('admin_dashboard')


# ✅ ADMIN: Suspend / Activate Mechanic
@login_required
def suspend_mechanic(request, mechanic_id):
    if not request.user.is_admin():
        return redirect('home')
    mechanic = get_object_or_404(CustomUser, id=mechanic_id, role='mechanic')
    mechanic.is_active = False
    mechanic.save()
    messages.warning(request, f"🔒 Mechanic {mechanic.username} has been suspended.")
    return redirect('admin_dashboard')


@login_required
def activate_mechanic(request, mechanic_id):
    if not request.user.is_admin():
        return redirect('home')
    mechanic = get_object_or_404(CustomUser, id=mechanic_id, role='mechanic')
    mechanic.is_active = True
    mechanic.save()
    messages.success(request, f"✅ Mechanic {mechanic.username} has been reactivated.")
    return redirect('admin_dashboard')


# 🗑️ ADMIN: Delete User
@login_required
def delete_user(request, user_id):
    if not request.user.is_admin():
        return redirect('home')
    user = get_object_or_404(CustomUser, id=user_id)
    username = user.username
    user.delete()
    messages.warning(request, f"🗑️ User '{username}' has been deleted.")
    return redirect('admin_dashboard')


# 🛒 CUSTOMER CART VIEW
@login_required
def cart(request):
    if not request.user.is_customer():
        return redirect('home')
    return render(request, 'users/cart.html')
@login_required
def submit_feedback(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id, user=request.user)

    if service_request.status != 'completed':
        messages.error(request, "⚠️ You can only give feedback after completion.")
        return redirect('user_dashboard')

    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        feedback = request.POST.get("comment")

        # Save into ServiceRequest
        service_request.rating = rating
        service_request.feedback = feedback
        service_request.save()

        # Also store into Feedback model (so it shows in mechanic_detail)
        Feedback.objects.create(
            customer=request.user,
            mechanic=service_request.mechanic,
            rating=rating,
            comment=feedback,
        )

        messages.success(request, "✅ Thank you for your feedback!")
        return redirect('user_dashboard')

    return render(request, "users/submit_feedback.html", {"request": service_request})


@login_required
def user_profile(request):
    user = request.user

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        location = request.POST.get('location')
        pincode = request.POST.get('pincode')

        # ✅ Update user fields
        user.username = username
        user.email = email
        user.phone = phone
        user.address = address
        user.location = location
        user.pincode = pincode
        user.save()

        messages.success(request, "✅ Your profile has been updated successfully!")
        return redirect('user_profile')

    return render(request, 'users/user_profile.html', {'user': user})

@login_required
def mechanic_detail(request, mechanic_id):
    """
    Public view for customers to see mechanic info, ratings & reviews.
    """
    mechanic = get_object_or_404(CustomUser, id=mechanic_id, role="mechanic")

    # Get all ratings & feedbacks
    ratings = MechanicRating.objects.filter(mechanic=mechanic)
    feedbacks = Feedback.objects.filter(mechanic=mechanic).order_by("-created_at")

    # Calculate average rating
    avg_rating = ratings.aggregate(Avg("rating"))["rating__avg"] or 0

    # Combine reviews (ratings + feedback)
    combined_reviews = []
    for fb in feedbacks:
        combined_reviews.append({
            "customer": fb.customer.username,
            "rating": fb.rating,
            "comment": fb.comment,
            "created_at": fb.created_at,
        })
    for r in ratings:
        combined_reviews.append({
            "customer": r.customer.username,
            "rating": r.rating,
            "comment": r.feedback,
            "created_at": r.created_at,
        })
    combined_reviews.sort(key=lambda x: x["created_at"], reverse=True)

    return render(request, "users/mechanic_detail.html", {
        "mechanic": mechanic,
        "avg_rating": round(avg_rating, 1),
        "total_reviews": len(combined_reviews),
        "reviews": combined_reviews,
    })

