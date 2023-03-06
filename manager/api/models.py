from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import RegexValidator
from datetime import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
import random
import string

USER_ID_LENGTH = 8
TXN_ID_LENGTH = 10


def generate_random_string(length):
    random.seed(datetime.now().timestamp())
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# Create your models here.

# Wallet Model instantiated when a User is created
class Wallet(models.Model):
    user = models.OneToOneField("Customuser", on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

# Transaction Model instantiated when a Transaction is created
class Transaction(models.Model):
    transaction_id = models.CharField(
        max_length=TXN_ID_LENGTH, primary_key=True, unique=True
    )
    # Sender and Receiver are both Wallets
    sender = models.ForeignKey(
        "Wallet", on_delete=models.DO_NOTHING, related_name="sender"
    )
    receiver = models.ForeignKey(
        "Wallet", on_delete=models.DO_NOTHING, related_name="receiver"
    )

    timestap = models.DateTimeField(auto_now_add=True)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # STATUS
    SUCCESS = 0
    FAILED = 1
    PENDING = 2
    IN_REVIEW = 3

    TRANSACTION_STATUS = [
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (PENDING, "Pending"),
        (IN_REVIEW, "In Review"),
    ]
    transaction_status = models.IntegerField(choices=TRANSACTION_STATUS, default=SUCCESS)

    class Meta:
        unique_together = ["sender", "receiver", "transaction_id"]

    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_status}"
    
    def clean(self):
        if self.transaction_amount <= 0:
            raise ValidationError("Transaction amount must be greater than 0")
        if self.sender == self.receiver:
            raise ValidationError("Sender and Receiver cannot be the same")
        if self.sender.balance < self.transaction_amount:
            raise ValidationError("Insufficient funds")

    def save(self, *args, **kwargs):
        self.clean()
        if self.transaction_id is None:
            self.transaction_id = generate_random_string(TXN_ID_LENGTH)
        self.sender.balance -= self.transaction_amount
        self.receiver.balance += self.transaction_amount
        self.sender.save()
        self.receiver.save()

        if self.sender.balance < 0:
            self.transaction_status = self.FAILED
            self.sender.balance += self.transaction_amount
            self.receiver.balance -= self.transaction_amount
            self.sender.save()
            self.receiver.save()
        else:
            self.transaction_status = self.SUCCESS

        super().save(*args, **kwargs)

# Now to our User models
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(username=username, email=self.normalize_email(email), phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, username, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, phone_number, password, **extra_fields)
    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Types(models.TextChoices):
        VENDOR = "VENDOR", "vendor"
        CUSTOMER = "CUSTOMER", "customer"

    type = models.CharField(
        max_length=10, choices=Types.choices, default=Types.CUSTOMER
    )
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True
    )  # validators should be a list
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    user_id = models.CharField(max_length=USER_ID_LENGTH, unique=True, primary_key=True, default=generate_random_string(USER_ID_LENGTH))
    is_vendor = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "phone_number"]

    objects = CustomUserManager()

    def __str__(self):
        return self.username
    
    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)
        if CustomUser.objects.filter(email=self.email).exclude(pk=self.pk).exists():
            raise ValidationError({'email': 'This email address is already in use.'})
        if CustomUser.objects.filter(phone_number=self.phone_number).exclude(pk=self.pk).exists():
            raise ValidationError({'phone_number': 'This phone number is already in use.'})
    
    def save(self, *args, **kwargs):
        self.validate_unique()
        if not self.user_id:
            self.user_id = generate_random_string(USER_ID_LENGTH)
        if not self.type or self.type == None:
            self.type = self.Types.CUSTOMER
        if self.type == self.Types.VENDOR:
            self.is_vendor = True
            self.is_customer = False
        else:
            self.is_vendor = False
            self.is_customer = True
        super().save(*args, **kwargs)
         # instantiating a wallet for the user
        if not Wallet.objects.filter(user=self).exists():
            Wallet.objects.create(user=self)

class VendorManager(models.Manager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(username=username, email=self.normalize_email(email), phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=CustomUser.Types.VENDOR)
    
class Vendor(CustomUser):
    objects = VendorManager()

    class Meta:
        proxy = True
    
    def save(self, *args, **kwargs):
        self.is_customer = False
        self.is_vendor = True
        self.type = self.Types.VENDOR
        super().save(*args, **kwargs)

class CustomerManager(models.Manager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(username=username, email=self.normalize_email(email), phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=CustomUser.Types.CUSTOMER)

class Customer(CustomUser):
    objects = CustomerManager()

    class Meta:
        proxy = True
    
    def save(self, *args, **kwargs):
        self.is_customer = True
        self.is_vendor = False
        self.type = self.Types.CUSTOMER
        super().save(*args, **kwargs)