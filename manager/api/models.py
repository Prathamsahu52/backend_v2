from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
import random
import string


WALLET_ID_LENGTH = 6
USER_ID_LENGTH = 8

# to generate random string
def generate_random_string(length):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# Create your models here.

# Wallet model
class Wallet(models.Model):
    wallet_id = models.CharField(max_length=WALLET_ID_LENGTH, unique=True)
    balance = models.FloatField(default=0.0)

    def __str__(self):
        return self.wallet_id


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field is required")

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(max_length=17, validators=[phone_regex])
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE, null=True)
    is_customer = models.BooleanField(default=True)
    is_vendor = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = "__all__"

    objects = CustomUserManager()

    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.username = self.email.split("@")[0]
        super().save(*args, **kwargs)


class Vendor(User):
    vendor_id = models.CharField(
        max_length=8, default=generate_random_string(USER_ID_LENGTH), unique=True
    )
    is_vendor = True
    is_customer = False
    customers = models.ManyToManyField(
        User, related_name="customers", through="VendorCustomer"
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.username = self.email.split("@")[0]
        super().save(*args, **kwargs)


class Customer(User):
    customer_id = models.CharField(
        max_length=8, default=generate_random_string(USER_ID_LENGTH), unique=True
    )
    is_customer = True
    is_vendor = False
    vendors = models.ManyToManyField(
        User, related_name="vendors", through="VendorCustomer"
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.username = self.email.split("@")[0]
        super().save(*args, **kwargs)


class VendorCustomer(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.DO_NOTHING)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = ["vendor", "customer"]

    def __str__(self):
        return f"{self.vendor.username} - {self.customer.username}"
