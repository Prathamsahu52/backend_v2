from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import RegexValidator
import random
import string
from datetime import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError


USER_ID_LENGTH = 8
TXN_ID_LENGTH = 10


def generate_random_string(length):
    random.seed(datetime.now().timestamp())
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
    )

# Create your models here.

# Wallet model for storing wallet balance, created when a user is created
class Wallet(models.Model):
    user = models.OneToOneField(
        "CustomUser", on_delete=models.CASCADE, primary_key=True
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # list of all transactions made by the user
    transactions = models.ManyToManyField("Transaction")

    def __str__(self):
        return f"{self.user.username}'s wallet"
    

# Transaction model for storing transaction details
class Transaction(models.Model):
    # sender and receiver of the transaction
    # throws error FOREIGN KEY constraint failed if the user is deleted

    sender = models.ForeignKey("CustomUser", on_delete=models.CASCADE, related_name="sender", null=True)
    receiver = models.ForeignKey("CustomUser", on_delete=models.CASCADE, related_name="receiver", null=True)

    timestamp = models.DateTimeField(default=timezone.now)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=TXN_ID_LENGTH, primary_key=True, unique=True)

    # status of the transaction
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

    transaction_status = models.IntegerField(choices=TRANSACTION_STATUS, default=PENDING)

    class Meta:
        unique_together = ('sender', 'receiver', 'transaction_id')

    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_status}"
    
    def clean(self):
        if self.transaction_amount < 0:
            raise ValidationError("Transaction amount cannot be negative")
        if self.sender == self.receiver:
            raise ValidationError("Sender and receiver cannot be the same")
        if self.sender.wallet.balance < self.transaction_amount:
            raise ValidationError("Insufficient balance")
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.transaction_id:
            self.transaction_id = generate_random_string(TXN_ID_LENGTH)
        self.sender.wallet.balance -= self.transaction_amount
        self.receiver.wallet.balance += self.transaction_amount
        self.sender.wallet.save()
        self.receiver.wallet.save()

        if self.sender.wallet.balance < 0:
            self.transaction_status = Transaction.FAILED
        else:
            self.transaction_status = Transaction.SUCCESS
        
        super().save(*args, **kwargs)


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have a username")
        if not email:
            raise ValueError("Users must have an email address")
        if not phone_number:
            raise ValueError("Users must have a phone number")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, username, email, phone_number, password=None, **extra_fields
    ):
        user = self.create_user(username, email, phone_number, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


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

    user_id = models.CharField(max_length=USER_ID_LENGTH, unique=True, primary_key=True)
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
        # instantiating a wallet for the user
        if not Wallet.objects.filter(user=self).exists():
            Wallet.objects.create(user=self)

        return super().save(*args, **kwargs)

class VendorManager(models.Manager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have a username")
        if not email:
            raise ValueError("Users must have an email address")
        if not phone_number:
            raise ValueError("Users must have a phone number")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def get_queryset(seld, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=CustomUser.Types.VENDOR)
    
class Vendor(CustomUser):
    objects = VendorManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.type = CustomUser.Types.VENDOR
        self.is_customer = False
        self.is_vendor = True

        return super().save(*args, **kwargs)

class CustomerManager(models.Manager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have a username")
        if not email:
            raise ValueError("Users must have an email address")
        if not phone_number:
            raise ValueError("Users must have a phone number")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def get_queryset(seld, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=CustomUser.Types.CUSTOMER)

class Customer(CustomUser):
    objects = CustomerManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.type = CustomUser.Types.CUSTOMER
        self.is_customer = True
        self.is_vendor = False

        return super().save(*args, **kwargs)