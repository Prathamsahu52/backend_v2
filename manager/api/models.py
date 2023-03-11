from django.db import models
from django.db.models import Q, OuterRef
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    AbstractUser,
)
from django.core.validators import RegexValidator
from datetime import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
import random
import string

USER_ID_LENGTH = 8
TXN_ID_LENGTH = 10
MAX_NOTIF_LEN = 256
MAX_NOTIF_SUB_LEN = 64
MAX_ISSUE_LEN = 512
MAX_ISSUE_SUB_LEN = 64
PENDING_LIMIT = 100000.0


def get_time(timestamp):
    return f"{timestamp.hour:02d}:{timestamp.minute:02d}, {timestamp.day:02d}-{timestamp.month:02d}-{timestamp.year:02d}"


def generate_random_string(length):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_user_id():
    return generate_random_string(USER_ID_LENGTH)


def generate_txn_id():
    return generate_random_string(TXN_ID_LENGTH)


# Create your models here.

# Wallet Model instantiated when a User is created
class Wallet(models.Model):
    user = models.OneToOneField("CustomUser", on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    pending = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username}'s Wallet"


class Notification(models.Model):
    """
    Class for managing notifications
    Currently supports subject line, content, read status (TODO: frontend integration)
    """

    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=MAX_NOTIF_SUB_LEN)
    content = models.TextField(max_length=MAX_NOTIF_LEN)
    mark_as_read = models.BooleanField(default=False)


# Transaction Model instantiated when a Transaction is created
class Transaction(models.Model):
    transaction_id = models.CharField(
        max_length=TXN_ID_LENGTH, primary_key=True, unique=True, default=generate_txn_id
    )
    # Sender and Receiver are both Wallets
    sender = models.ForeignKey(
        "Wallet", on_delete=models.CASCADE, related_name="sender"
    )
    receiver = models.ForeignKey(
        "Wallet", on_delete=models.CASCADE, related_name="receiver"
    )

    timestamp = models.DateTimeField(auto_now_add=True)
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
    transaction_status = models.IntegerField(
        choices=TRANSACTION_STATUS, default=SUCCESS
    )

    class Meta:
        unique_together = ["sender", "receiver", "transaction_id"]

    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_status}"

    def clean(self):
        if self.transaction_amount <= 0:
            Notification.objects.create(
                user=self.sender.user,
                timestamp=self.timestamp,
                subject="Transaction failed.",
                content=f"Transaction at {get_time(datetime.now())} failed: amount must be greater than 0.",
            )
            raise ValidationError("Transaction amount must be greater than 0")

        if self.sender == self.receiver:
            Notification.objects.create(
                user=self.sender.user,
                timestamp=self.timestamp,
                subject="Transaction failed.",
                content=f"Transaction at {get_time(datetime.now())} failed: sender and receiver identical.",
            )
            raise ValidationError("Sender and Receiver cannot be the same")

    def save(self, *args, **kwargs):
        self.clean()
        if self.transaction_id is None:
            self.transaction_id = generate_txn_id()

        if self.transaction_status == self.PENDING:
            if (self.sender.pending + self.transaction_amount) <= PENDING_LIMIT:
                self.sender.pending += self.transaction_amount
                Notification.objects.create(
                    user=self.sender.user,
                    timestamp=self.timestamp,
                    subject="Transaction with payment pending.",
                    content=f"Paid Rs. {self.transaction_amount} as PENDING to {self.receiver.user.username}  at {get_time(datetime.now())}.",
                )

                Notification.objects.create(
                    user=self.receiver.user,
                    timestamp=self.timestamp,
                    subject="Transaction with payment pending.",
                    content=f"Received Rs. {self.transaction_amount} as PENDING from {self.sender.user.username} at {get_time(datetime.now())}.",
                )

            else:
                self.transaction_status = self.FAILED
                Notification.objects.create(
                    user=self.sender.user,
                    timestamp=self.timestamp,
                    subject="Transaction failed.",
                    content=f"Transaction at {get_time(datetime.now())} failed: exceeded pending dues limit.",
                )

        elif self.sender.balance < self.transaction_amount:
            # Could ask user if they want to switch to pending mode
            self.transaction_status = self.FAILED
            Notification.objects.create(
                user=self.sender.user,
                timestamp=self.timestamp,
                subject="Transaction failed.",
                content=f"Transaction at {get_time(datetime.now())} failed: insufficient funds.",
            )

        else:
            self.transaction_status = self.SUCCESS
            self.sender.balance -= self.transaction_amount
            self.receiver.balance += self.transaction_amount

            Notification.objects.create(
                user=self.sender.user,
                timestamp=self.timestamp,
                subject="Transaction success.",
                content=f"Rs. {self.transaction_amount} sent successfully to {self.receiver.user.username} at {get_time(datetime.now())}.",
            )
            Notification.objects.create(
                user=self.receiver.user,
                timestamp=self.timestamp,
                subject="Transaction success.",
                content=f"Rs. {self.transaction_amount} received from {self.sender.user.username} at {get_time(datetime.now())}.",
            )

        self.sender.save()
        self.receiver.save()

        if self.sender.balance < 0:
            self.transaction_status = self.FAILED
            self.sender.balance += self.transaction_amount
            self.receiver.balance -= self.transaction_amount
            self.sender.save()
            self.receiver.save()

        super().save(*args, **kwargs)


# Issues instantiated when a User raises one
class Issue(models.Model):

    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    subject = models.CharField(max_length=MAX_ISSUE_SUB_LEN)
    content = models.TextField(max_length=MAX_ISSUE_LEN)
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, null=True, blank=True
    )
    # transaction_id = Transaction.objects.get(
    #     transaction_id=self.transaction.transaction_id
    # )

    resolved_status = models.IntegerField(
        choices=Transaction.TRANSACTION_STATUS, default=Transaction.IN_REVIEW
    )

    def __str__(self):
        return f"{self.user.username} raised an issue"

    def clean(self):
        if self.transaction is None:
            raise ValidationError("Transaction cannot be empty")
        if (
            self.transaction.receiver.user.username != self.user.username
            and self.transaction.sender.user.username != self.user.username
        ):
            raise ValidationError(
                f"Not authorized to raise an issue on this transaction"
            )

    def save(self, *args, **kwargs):
        self.clean()

        self.transaction.transaction_status = Transaction.IN_REVIEW  # In_Review
        super(Transaction, self.transaction).save()

        if (
            self.resolved_status == Transaction.SUCCESS
            or self.resolved_status == Transaction.PENDING
        ):
            # Do nothing to balance
            self.transaction.transaction_status = self.resolved_status
            super(Transaction, self.transaction).save()

            Notification.objects.create(
                user=self.transaction.sender.user,
                timestamp=self.timestamp,
                subject="Issue resolved.",
                content=f"Issue for transaction {self.transaction.transaction_id} resolved to status {Transaction.TRANSACTION_STATUS[self.resolved_status][1]} at {get_time(self.timestamp)}.",
            )
            Notification.objects.create(
                user=self.transaction.receiver.user,
                timestamp=self.timestamp,
                subject="Issue resolved.",
                content=f"Issue for transaction {self.transaction.transaction_id} resolved to status {Transaction.TRANSACTION_STATUS[self.resolved_status][1]} at {get_time(self.timestamp)}.",
            )

        elif self.resolved_status == Transaction.FAILED:
            # Revert pending amount
            self.transaction.transaction_status = Transaction.FAILED
            self.transaction.sender.pending -= self.transaction.transaction_amount
            super(Transaction, self.transaction).save()
            super(Wallet, self.transaction.sender).save()

            Notification.objects.create(
                user=self.transaction.sender.user,
                timestamp=self.timestamp,
                subject="Issue resolved.",
                content=f"Issue for transaction {self.transaction.transaction_id} resolved to status FAILED at {get_time(self.timestamp)}, pending amount Rs. {self.transaction.transaction_amount} reverted.",
            )
            Notification.objects.create(
                user=self.transaction.receiver.user,
                timestamp=self.timestamp,
                subject="Issue resolved.",
                content=f"Issue for transaction {self.transaction.transaction_id} resolved to status FAILED at {get_time(self.timestamp)}.",
            )

        super().save(*args, **kwargs)

        Notification.objects.create(
            user=self.transaction.sender.user,
            timestamp=self.timestamp,
            subject="Issue raised.",
            content='Issue: "'
            + self.content
            + f'" for transaction ID {self.transaction.transaction_id} raised at {get_time(self.timestamp)}.',
        )

        Notification.objects.create(
            user=self.transaction.receiver.user,
            timestamp=self.timestamp,
            subject="Issue raised.",
            content='Issue: "'
            + self.content
            + f'" for transaction ID {self.transaction.transaction_id} raised at {get_time(self.timestamp)}.',
        )


# Now to our User models
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self, username, email, phone_number, password=None, **extra_fields
    ):
        # extra_fields.setdefault("is_staff", True)
        # extra_fields.setdefault("is_superuser", True)
        # return self.create_user(username, email, phone_number, password, **extra_fields)
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields,
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
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

    user_id = models.CharField(
        max_length=USER_ID_LENGTH,
        unique=True,
        primary_key=True,
        default=generate_user_id,
    )
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
            raise ValidationError({"email": "This email address is already in use."})
        if (
            CustomUser.objects.filter(phone_number=self.phone_number)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {"phone_number": "This phone number is already in use."}
            )

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

            if self.type == self.Types.VENDOR:
                Notification.objects.create(
                    user=self,
                    timestamp=datetime.now().timestamp(),
                    subject="Welcome!",
                    content=f"Hello Vendor {self.username}, Welcome to CampusPay!",
                )
            else:
                Notification.objects.create(
                    user=self,
                    timestamp=datetime.now().timestamp(),
                    subject="Welcome!",
                    content=f"Hello Customer {self.username}, Welcome to CampusPay!",
                )


class VendorManager(models.Manager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def get_queryset(self, *args, **kwargs):
        return (
            super().get_queryset(*args, **kwargs).filter(type=CustomUser.Types.VENDOR)
        )


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

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def get_queryset(self, *args, **kwargs):
        return (
            super().get_queryset(*args, **kwargs).filter(type=CustomUser.Types.CUSTOMER)
        )


class Customer(CustomUser):
    objects = CustomerManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.is_customer = True
        self.is_vendor = False
        self.type = self.Types.CUSTOMER
        super().save(*args, **kwargs)
