from django.contrib import admin
from .models import CustomUser, Vendor, Customer, Transaction, Wallet
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Vendor)
admin.site.register(Customer)
admin.site.register(Transaction)
admin.site.register(Wallet)
