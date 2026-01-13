from django.db import models
from django.utils import timezone
from users.models import CustomUser


# 🧰 Service Request Model
class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    MECHANIC_TYPE_CHOICES = [
        ('two_wheeler', 'Two-Wheeler Mechanic'),
        ('automotive', 'Automotive Mechanic'),
        ('heavy_vehicle', 'Heavy Vehicle Mechanic'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='service_requests'
    )
    mechanic = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests'
    )

    issue_description = models.TextField()
    location = models.CharField(max_length=255)

    # 🆕 Add these:
    mechanic_type = models.CharField(max_length=50, choices=MECHANIC_TYPE_CHOICES,default='automotive')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # ⭐ Optional Rating + Feedback
    rating = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.issue_description[:30]}"

    class Meta:
        ordering = ['-created_at']

# 🔔 Notification Model
class Notification(models.Model):
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To {self.recipient.username}: {self.message[:40]}"

    class Meta:
        ordering = ['-created_at']


# 💬 Chat Message Model
class ChatMessage(models.Model):
    service_request = models.ForeignKey(
        ServiceRequest, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.message[:30]}"

    class Meta:
        ordering = ['timestamp']  # ✅ auto order messages


# ⭐ Mechanic Rating Model
class MechanicRating(models.Model):
    service_request = models.OneToOneField(
        ServiceRequest, 
        on_delete=models.CASCADE, 
        related_name='service_rating'
    )
    mechanic = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'mechanic'}, 
        related_name='received_ratings'
    )
    customer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'customer'}, 
        related_name='given_ratings'
    )
    rating = models.IntegerField(default=0)
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} → {self.mechanic.username} ({self.rating}/5)"

    class Meta:
        ordering = ['-created_at']
