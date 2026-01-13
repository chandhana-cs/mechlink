# services/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q,Avg
from .models import ServiceRequest, Notification, ChatMessage, MechanicRating
from users.models import CustomUser
from mechanics.models import MechanicProfile  # ✅ if you need mechanic info
from django.urls import reverse
from math import radians, sin, cos, sqrt, atan2

# 🧰 CUSTOMER: Raise a Service Request
@login_required
def raise_request(request):
    # ✅ Only customers can raise a request
    if not request.user.is_customer():
        return redirect("home")

    mechanics = None
    issue = location = pincode = mechanic_type = ""
    latitude = longitude = None
    old_req = None

    # ✅ Prefill data when re-raising an old request
    re_raise_id = request.GET.get("re_raise")
    if re_raise_id:
        try:
            old_req = ServiceRequest.objects.get(id=re_raise_id, user=request.user)
            issue = old_req.issue_description
            location = old_req.location
            mechanic_type = old_req.mechanic_type
            latitude = old_req.latitude
            longitude = old_req.longitude
        except ServiceRequest.DoesNotExist:
            messages.warning(request, "⚠️ Old request not found or invalid.")
            pass

    if request.method == "POST":
        issue = request.POST.get("issue", "").strip()
        location = request.POST.get("location", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        mechanic_type = request.POST.get("mechanic_type", "")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        # ✅ Validation
        if not issue or not mechanic_type or not latitude or not longitude:
            messages.error(request, "⚠️ Please fill all required fields before submitting.")
            return render(request, "users/raise_request.html", {
                "issue": issue,
                "location": location,
                "pincode": pincode,
                "mechanic_type": mechanic_type,
                "latitude": latitude,
                "longitude": longitude,
                "mechanics": mechanics,
            })

        # ✅ If a mechanic is chosen → create the Service Request
        mechanic_id = request.POST.get("mechanic_id")
        if mechanic_id:
            mechanic = get_object_or_404(CustomUser, id=mechanic_id)
            new_request = ServiceRequest.objects.create(
                user=request.user,
                mechanic=mechanic,
                issue_description=issue,
                location=location,
                mechanic_type=mechanic_type,
                latitude=latitude,
                longitude=longitude,
                status="pending",
            )

            # Notify the mechanic
            Notification.objects.create(
                recipient=mechanic,
                sender=request.user,
                message=f"🧰 New {mechanic_type.replace('_', ' ')} service request from {request.user.username}.",
            )

            messages.success(request, f"✅ Request sent to {mechanic.username} successfully!")
            return redirect("my_requests")

        # 🔍 Otherwise → find nearby mechanics based on coordinates
        all_mechanics = CustomUser.objects.filter(
          role="mechanic",
          mechanic_profile__latitude__isnull=False,
          mechanic_profile__longitude__isnull=False,
          mechanic_profile__mechanic_types__icontains=mechanic_type
         ).select_related("mechanic_profile")


        lat1 = radians(float(latitude))
        lon1 = radians(float(longitude))
        MAX_DISTANCE_KM = 10

        nearby_mechanics = []
        for mech in all_mechanics:
            profile = mech.mechanic_profile
            if profile.latitude and profile.longitude:
                lat2 = radians(profile.latitude)
                lon2 = radians(profile.longitude)
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance = 6371 * c
                if distance <= MAX_DISTANCE_KM:
                    mech.distance = round(distance, 2)
                    nearby_mechanics.append(mech)

        mechanics = sorted(nearby_mechanics, key=lambda m: m.distance)

        # ⭐ Attach ratings + reviews for each mechanic
        for m in mechanics:
            m.avg_rating = MechanicRating.objects.filter(mechanic=m).aggregate(Avg("rating"))["rating__avg"] or 0
            m.review_count = MechanicRating.objects.filter(mechanic=m).count()

        if not mechanics:
            messages.warning(request, f"⚠️ No mechanics found within {MAX_DISTANCE_KM} km of your location.")

    # ✅ Render form with prefilled data (for GET or invalid POST)
    return render(request, "users/raise_request.html", {
        "issue": issue,
        "location": location,
        "pincode": pincode,
        "mechanic_type": mechanic_type,
        "latitude": latitude,
        "longitude": longitude,
        "mechanics": mechanics,
    })


# 🧾 CUSTOMER: View Their Requests
@login_required
def my_requests(request):
    # 🔥 Expire old pending requests first
    expire_old_requests()

    requests = ServiceRequest.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "services/my_requests.html", {"requests": requests})


# ⚙️ MECHANIC: Accept / Reject / Complete Requests
@login_required
def accept_request(request, request_id):
    req = get_object_or_404(ServiceRequest, id=request_id, mechanic=request.user)

    if req.status != "pending":
        messages.warning(request, "⚠️ This request has already been processed.")
        return redirect("mechanic_dashboard")

    req.status = "accepted"
    req.save()

    # ✅ Notify the customer
    Notification.objects.create(
        recipient=req.user,
        sender=request.user,
        message=f"✅ Your service request #{req.id} has been accepted by {request.user.username}.",
    )

    messages.success(request, f"Service request #{req.id} accepted successfully.")
    return redirect("mechanic_dashboard")


@login_required
def reject_request(request, request_id):
    req = get_object_or_404(ServiceRequest, id=request_id, mechanic=request.user)

    if req.status != "pending":
        messages.warning(request, "⚠️ This request has already been processed.")
        return redirect("mechanic_dashboard")

    req.status = "rejected"
    req.save()

    # ✅ Notify customer
    Notification.objects.create(
        recipient=req.user,
        sender=request.user,
        message=f"❌ Your service request #{req.id} has been rejected by {request.user.username}.",
    )

    messages.warning(request, f"Request #{req.id} rejected.")
    return redirect("mechanic_dashboard")


@login_required
def complete_service(request, request_id):
    req = get_object_or_404(ServiceRequest, id=request_id, mechanic=request.user)

    if req.status not in ["accepted", "in_progress"]:
        messages.warning(request, "⚠️ Only accepted services can be marked as completed.")
        return redirect("mechanic_dashboard")

    req.status = "completed"
    req.save()

    # ✅ Notify the customer
    Notification.objects.create(
        recipient=req.user,
        sender=request.user,
        message=f"🎉 Your service request #{req.id} has been completed by {request.user.username}.",
    )

    messages.success(request, f"✅ Service request #{req.id} marked as completed.")
    return redirect("mechanic_dashboard")


# 💬 CHAT BETWEEN USER & MECHANIC
@login_required
def chat_view(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)

    # ✅ Only the mechanic or the user can view this chat
    if request.user not in [service_request.user, service_request.mechanic]:
        messages.error(request, "You are not authorized to view this chat.")
        return redirect("home")

    # ✅ Chat is allowed only for accepted/in-progress
    if service_request.status not in ["accepted", "in_progress"]:
        messages.warning(request, "Chat is only available for active service requests.")
        return redirect("user_dashboard" if request.user.role == "customer" else "mechanic_dashboard")

    chat_messages = ChatMessage.objects.filter(service_request=service_request).order_by("timestamp")
    receiver = service_request.mechanic if request.user == service_request.user else service_request.user

    if request.method == "POST":
        msg_text = request.POST.get("message", "").strip()
        if msg_text and receiver:
            ChatMessage.objects.create(
                service_request=service_request,
                sender=request.user,
                receiver=receiver,
                message=msg_text,
            )
            return redirect("chat_view", request_id=request_id)

    context = {
        "service_request": service_request,
        "chat_messages": chat_messages,
        "receiver": receiver,
        "chat_disabled": service_request.status == "completed",
    }
    return render(request, "services/chat.html", context)


# 💬 OPTIONAL CHAT LIST
@login_required
def chat_list(request):
    if request.user.role == "mechanic":
        service_requests = ServiceRequest.objects.filter(mechanic=request.user)
    else:
        service_requests = ServiceRequest.objects.filter(user=request.user)

    return render(request, "services/chat_list.html", {"service_requests": service_requests})


# ⭐ CUSTOMER: Rate Mechanic
@login_required
def rate_mechanic(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)

    if request.user != service_request.user:
        messages.error(request, "You are not authorized to rate this service.")
        return redirect("home")

    if request.method == "POST":
        rating_value = int(request.POST.get("rating", 0))
        feedback_text = request.POST.get("feedback", "").strip()

        MechanicRating.objects.update_or_create(
            service_request=service_request,
            defaults={
                "mechanic": service_request.mechanic,
                "customer": request.user,
                "rating": rating_value,
                "feedback": feedback_text,
            },
        )

        service_request.rating = rating_value
        service_request.feedback = feedback_text
        service_request.save()

        # ✅ Notify the mechanic
        Notification.objects.create(
            recipient=service_request.mechanic,
            sender=request.user,
            message=f"⭐ You received a new {rating_value}-star rating from {request.user.username}.",
        )

        messages.success(request, "✅ Your feedback has been submitted successfully!")
        return redirect("my_requests")

    existing_rating = getattr(service_request, "service_rating", None)

    return render(request, "services/rate_mechanic.html", {
        "service_request": service_request,
        "existing_rating": existing_rating,
    })


# 🧾 MECHANIC: View Their Service Requests (with filter)
@login_required
def mechanic_requests(request):
    # ✅ Ensure only mechanics can view this page
    if not request.user.is_mechanic():
        return redirect("home")

    # 🔥 Expire old pending requests first
    expire_old_requests()

    # Optional: filter by status from dropdown
    status_filter = request.GET.get("status", "")
    service_requests = ServiceRequest.objects.filter(mechanic=request.user)

    if status_filter:
        service_requests = service_requests.filter(status=status_filter)

    # ✅ Dashboard counts for the summary cards
    pending_count = ServiceRequest.objects.filter(mechanic=request.user, status="pending").count()
    accepted_count = ServiceRequest.objects.filter(mechanic=request.user, status="accepted").count()
    completed_count = ServiceRequest.objects.filter(mechanic=request.user, status="completed").count()
    rejected_count = ServiceRequest.objects.filter(mechanic=request.user, status="rejected").count()

    # Include expired in filters (optional)
    statuses = ["pending", "accepted", "in_progress", "completed", "rejected", "expired"]

    # ✅ Pass everything to template
    return render(request, "services/mechanic_requests.html", {
        "service_requests": service_requests,
        "statuses": statuses,
        "selected_status": status_filter,
        "pending_count": pending_count,
        "accepted_count": accepted_count,
        "completed_count": completed_count,
        "rejected_count": rejected_count,
    })


from django.utils import timezone
from datetime import timedelta
from .models import ServiceRequest, Notification

def expire_old_requests():
    """
    Automatically expire old pending requests (older than 5 minutes)
    when someone opens a page like 'my_requests' or 'mechanic_requests'.
    """
    expiry_time = timezone.now() - timedelta(minutes=5)
    old_requests = ServiceRequest.objects.filter(status='pending', created_at__lt=expiry_time)

    for req in old_requests:
        req.status = 'expired'
        req.save()

        # Notify the customer
        Notification.objects.create(
            recipient=req.user,
            message=f"⚠️ Your service request #{req.id} expired (no mechanic accepted in time)."
        )

@login_required
def re_raise_request(request, request_id):
    """
    Allow a user to resend an expired request.
    Duplicates the old one as a new pending request.
    """
    old_req = get_object_or_404(ServiceRequest, id=request_id, user=request.user)

    # Only allow re-raising expired requests
    if old_req.status != "expired":
        messages.warning(request, "Only expired requests can be re-raised.")
        return redirect("my_requests")

    # Create a new identical pending request
    new_req = ServiceRequest.objects.create(
        user=request.user,
        issue_description=old_req.issue_description,
        location=old_req.location,
        mechanic_type=old_req.mechanic_type,
        latitude=old_req.latitude,
        longitude=old_req.longitude,
        status="pending",
    )

    # Notify user
    messages.success(
        request,
        f"✅ Your request #{old_req.id} has been re-raised as new request #{new_req.id}!"
    )

    return redirect(f"{reverse('raise_request')}?re_raise={old_req.id}")


