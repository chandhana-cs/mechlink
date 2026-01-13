from django.contrib import admin
from .models import MechanicProfile, Product, Order, CartItem

admin.site.register(MechanicProfile)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(CartItem)


# Register your models here.
