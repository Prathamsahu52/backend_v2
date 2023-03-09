from django.shortcuts import render
from rest_framework import generics

from .models import CustomUser, Customer, Vendor, Transaction, Wallet,Notification
from .serializers import CustomUserSerializer, TransactionSerializer,NotificationSerializer

# Create your views here.
# List of all CustomUsers
class CustomUserList(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

# Detail of a CustomUser
class CustomUserDetail(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.get(user_id=self.kwargs["user_id"])
        return obj

# List of all the customers
class CustomerList(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomUserSerializer

# List of all the Vendors
class VendorList(generics.ListCreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = CustomUserSerializer

# list of all the transactions
class TransactionList(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

# detail of a transaction
class TransactionDetail(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.get(transaction_id=self.kwargs["transaction_id"])
        return obj

# list of all the transactions of a User
class UserTransactionList(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        sender = CustomUser.objects.get(user_id=user_id)
        wallet1 = Wallet.objects.get(user=sender)
        # as well as the reciever of the transaction
        receiver = CustomUser.objects.get(user_id=user_id)
        wallet2 = Wallet.objects.get(user=receiver)
        return Transaction.objects.filter(sender=wallet1) | Transaction.objects.filter(receiver=wallet2)

# list of all the vendors only if the user is a customer
class CustomerVendorList(generics.ListAPIView):
    serializer_class = CustomUserSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        customer = Customer.objects.get(user_id=user_id)
        wallet = Wallet.objects.get(user=customer)
        # list of all the ransactions made by the customer
        transactions = Transaction.objects.filter(sender=wallet)
        # list of all the vendors at the end of the transactions
        vendors = []
        for transaction in transactions:
            if transaction.receiver.user.is_vendor:
                vendors.append(transaction.receiver.user)
        return vendors
# list of all the customers only if the user is a vendor
class VendorCustomerList(generics.ListAPIView):
    serializer_class = CustomUserSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        vendor = Vendor.objects.get(user_id=user_id)
        wallet = Wallet.objects.get(user=vendor)
        # list of all the ransactions made by the vendor
        transactions = Transaction.objects.filter(receiver=wallet)
        # list of all the customers at the end of the transactions
        customers = []
        for transaction in transactions:
            if transaction.sender.user.is_customer:
                customers.append(transaction.sender.user)
        return customers
#list of all the notifications
class NotificationList(generics.ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

#list of all the notifications of a user
class UserNotificationList(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        user = CustomUser.objects.get(user_id=user_id)
        return Notification.objects.filter(user=user)

"""
Remaining Views
1. List of customers to a vendor --done
2. Pending dues for a vendor
4. Pending dues of a customer
3. Set of all notifs -- done
"""
