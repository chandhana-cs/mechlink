from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class MechanicProfile(models.Model):
    MECHANIC_TYPE_CHOICES = [
        ('two_wheeler', 'Two-Wheeler Mechanic'),
        ('automotive', 'Automotive Mechanic'),
        ('heavy_vehicle', 'Heavy Vehicle Mechanic'),
    ]

    user = models.OneToOneField(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='mechanic_profile'
    )

    shop_name = models.CharField(max_length=100, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    address = models.TextField(blank=True, default="")
    location = models.CharField(max_length=100, blank=True, default="Unknown")
    pincode = models.CharField(max_length=10, blank=True, default="000000")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # 👇 NEW FIELD
    mechanic_types = models.CharField(max_length=255, blank=True)


    def __str__(self):
        return self.shop_name or self.user.username

class Product(models.Model):
    mechanic = models.ForeignKey(MechanicProfile, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.mechanic.user.username})"


from django.db import models
from django.conf import settings

class Order(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="Pending")  # e.g. Pending, Paid, Cancelled, Delivered

    # ✅ Add Razorpay integration fields
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"



class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} × {self.product.name} ({self.user.username})"
