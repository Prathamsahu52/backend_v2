from django.contrib import admin

# from .models import CustomUser, Vendor, Customer, Transaction, Wallet

# admin.site.register(CustomUser)
# admin.site.register(Vendor)
# admin.site.register(Customer)
# admin.site.register(Transaction)
# admin.site.register(Wallet)
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Vendor, Customer, Transaction, Wallet, Notification,Issue


class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "is_customer",
        "is_vendor",
        "is_staff",
        "is_active",
    )

    search_fields = ("username", "email")
    readonly_fields = ("user_id",)
    list_filter = ()
    fieldsets = ()


class CustomerAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "is_staff",
        "is_active",
    )

    search_fields = ("username", "email")
    readonly_fields = ("user_id",)
    list_filter = ()
    fieldsets = ()


class VendorAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "is_staff",
        "is_active",
    )

    search_fields = ("username", "email")
    readonly_fields = ("user_id",)
    list_filter = ()
    fieldsets = ()


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "sender",
        "receiver",
        "transaction_amount",
        "timestamp",
        "transaction_status",
        "transaction_id",
    )

    search_fields = ("transaction_id",)
    readonly_fields = ("transaction_id",)
    list_filter = ()
    fieldsets = ()


class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "balance",
    )

    search_fields = ("user",)
    readonly_fields = ("user",)
    list_filter = ()
    fieldsets = ()


class NotifAdmin(admin.ModelAdmin):
    list_display = ("user", "timestamp", "subject", "content")
    readonly_fields = ("user", "timestamp", "subject", "content")
    search_fields = ("subject", "content")

class IssueAdmin(admin.ModelAdmin):
    list_display = ("user","subject","content","timestamp","resolved_status")
    search_fields = ("user","resolved_status","subject")
    readonly_fields = ("user","subject","content","timestamp")
    list_filter = ()
    fieldsets = ()

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Notification, NotifAdmin)
admin.site.register(Issue,IssueAdmin)