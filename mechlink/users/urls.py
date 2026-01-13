from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Customer
    
    path('my-orders/', views.my_orders, name='user_orders'),   # ✅ FIXED
    path('my-requests/', views.my_requests, name='user_service_requests'),  # ✅ FIXED
    path('cart/', views.cart, name='cart'),
    path('feedback/<int:request_id>/', views.submit_feedback, name='submit_feedback'),
    path("mechanic/<int:mechanic_id>/", views.mechanic_detail, name="mechanic_detail"),
    path('profile/', views.user_profile, name='user_profile'),


    # Admin actions
    path('approve-request/<int:request_id>/', views.admin_approve_request, name='admin_approve_request'),
    path('reject-request/<int:request_id>/', views.admin_reject_request, name='admin_reject_request'),
    path('suspend-mechanic/<int:mechanic_id>/', views.suspend_mechanic, name='suspend_mechanic'),
    path('activate-mechanic/<int:mechanic_id>/', views.activate_mechanic, name='activate_mechanic'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]
