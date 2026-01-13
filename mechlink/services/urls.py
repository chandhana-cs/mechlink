from django.urls import path
from . import views

urlpatterns = [
    # 🧰 Customer actions
    path("raise-request/", views.raise_request, name="raise_request"),
    path("my-requests/", views.my_requests, name="my_requests"),

    # 🧑‍🔧 Mechanic actions
    path("accept-request/<int:request_id>/", views.accept_request, name="accept_request"),
    path("reject-request/<int:request_id>/", views.reject_request, name="reject_request"),
    path("complete-service/<int:request_id>/", views.complete_service, name="complete_service"),

    # 💬 Chat system
    path("chat/<int:request_id>/", views.chat_view, name="chat_view"),
    path("chats/", views.chat_list, name="chat_list"),

    # ⭐ Rating
    path("rate/<int:request_id>/", views.rate_mechanic, name="rate_mechanic"),

    # 🧾 Mechanic Dashboard
    path("mechanic-requests/", views.mechanic_requests, name="mechanic_requests"),
    path("re-raise/<int:request_id>/", views.re_raise_request, name="re_raise_request"),

]
