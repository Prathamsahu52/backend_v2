from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView
from .models import CustomUser, Customer, Vendor, Transaction, Wallet, Notification
from .serializers import (
    CustomUserSerializer,
    TransactionSerializer,
    NotificationSerializer,
)
from rest_framework import status, serializers, permissions

from rest_framework.response import Response

# Create your views here.
# List of all CustomUsers
class CustomUserList(generics.ListCreateAPIView):
    permissions_classes = (permissions.IsAuthenticated,)

    # if user is not admin, send a 403 error
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not request.user.is_superuser:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


# Detail of a CustomUser
class CustomUserDetail(generics.RetrieveAPIView):
    # if user is the same as the user_id, or user is admin, send the data
    permissions_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        # if user is not authenticated
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not (
            request.user.is_superuser or request.user.user_id == self.kwargs["user_id"]
        ):
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.get(user_id=self.kwargs["user_id"])
        return obj


# List of all the customers
class CustomerList(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not request.user.is_superuser:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    queryset = Customer.objects.all()
    serializer_class = CustomUserSerializer


# List of all the Vendors
class VendorList(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not request.user.is_superuser:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    queryset = Vendor.objects.all()
    serializer_class = CustomUserSerializer


# list of all the transactions
class TransactionList(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not request.user.is_superuser:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


# detail of a transaction
class TransactionDetail(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not request.user.is_superuser:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.get(transaction_id=self.kwargs["transaction_id"])
        return obj


# list of all the transactions of a User
class UserTransactionList(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not (
            request.user.is_superuser or request.user.user_id == self.kwargs["user_id"]
        ):
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        sender = CustomUser.objects.get(user_id=user_id)
        wallet1 = Wallet.objects.get(user=sender)
        # as well as the reciever of the transaction
        receiver = CustomUser.objects.get(user_id=user_id)
        wallet2 = Wallet.objects.get(user=receiver)
        return Transaction.objects.filter(sender=wallet1) | Transaction.objects.filter(
            receiver=wallet2
        )


class UserMakeTransaction(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        receiver_id = request.data.get("receiver_id")
        sender_id = self.kwargs["user_id"]
        print(receiver_id, sender_id)

        sender = CustomUser.objects.get(user_id=sender_id)
        wallet_sender = Wallet.objects.get(user=sender)

        receiver = CustomUser.objects.get(user_id=receiver_id)
        wallet_receiver = Wallet.objects.get(user=receiver)

        transaction_data = {
            "sender": wallet_sender.pk,
            "receiver": wallet_receiver.pk,
            "transaction_amount": request.data.get("transaction_amount"),
            "transaction_status": request.data.get("transaction_status"),
        }

        serializer = TransactionSerializer(data=transaction_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Transaction updated"})


# list of all the vendors only if the user is a customer
class CustomerVendorList(generics.ListAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not (
            request.user.is_superuser or request.user.user_id == self.kwargs["user_id"]
        ):
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        customer = Customer.objects.get(user_id=user_id)
        wallet = Wallet.objects.get(user=customer)
        # list of all the ransactions made by the customer
        transactions = Transaction.objects.filter(sender=wallet)
        # list of all the vendors at the end of the transactions
        vendors = []
        for transaction in transactions:
            if transaction.receiver.user.is_vendor and transaction.receiver.user not in vendors:
                vendors.append(transaction.receiver.user)
        return vendors


# list of all the customers only if the user is a vendor
class VendorCustomerList(generics.ListAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not (
            request.user.is_superuser or request.user.user_id == self.kwargs["user_id"]
        ):
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        vendor = Vendor.objects.get(user_id=user_id)
        wallet = Wallet.objects.get(user=vendor)
        # list of all the ransactions made by the vendor
        transactions = Transaction.objects.filter(receiver=wallet)
        # list of all the customers at the end of the transactions
        customers = []
        for transaction in transactions:
            if transaction.sender.user.is_customer and transaction.sender.user not in customers:
                customers.append(transaction.sender.user)
        return customers


# list of all the notifications
class NotificationList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not request.user.is_superuser:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


# list of all the notifications of a user
class UserNotificationList(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not (
            request.user.is_superuser or request.user.user_id == self.kwargs["user_id"]
        ):
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        user = CustomUser.objects.get(user_id=user_id)
        return Notification.objects.filter(user=user)


# list of all the pending dues of a customer
class PendingDuesList(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not (
            request.user.is_superuser or request.user.user_id == self.kwargs["user_id"]
        ):
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        user = CustomUser.objects.get(user_id=user_id)
        wallet = Wallet.objects.get(user=user)
        return Transaction.objects.filter(sender=wallet, transaction_status=2)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        pending_dues = {}
        for transaction in queryset:
            receiver_wallet = transaction.receiver
            receiver = receiver_wallet.user
            if receiver.user_id not in pending_dues:
                pending_dues[receiver.user_id] = {
                    "receiver_name": receiver.username,
                    "receiver_id": receiver.user_id,
                    "dues": 0
                }
            pending_dues[receiver.user_id]["dues"] += transaction.transaction_amount
        result = {"pending_dues": list(pending_dues.values())}
        return Response(result)


# list of all the pending dues for a vendor
class PendingDuesVendor(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not (
            request.user.is_superuser or request.user.user_id == self.kwargs["user_id"]
        ):
            return Response(
                {"message": "Not Authorized to access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        user = CustomUser.objects.get(user_id=user_id)
        wallet = Wallet.objects.get(user=user)
        return Transaction.objects.filter(receiver=wallet, transaction_status=2)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        pending_dues = {}
        for transaction in queryset:
            sender_wallet = transaction.sender
            sender = sender_wallet.user
            if sender.user_id not in pending_dues:
                pending_dues[sender.user_id] = {
                    "receiver_name": sender.username,
                    "receiver_id": sender.user_id,
                    "dues": 0
                }
            pending_dues[sender.user_id]["dues"] += transaction.transaction_amount
        result = {"pending_dues": list(pending_dues.values())}
        return Response(result)


class ClearDues(APIView):
    permissions_classes = (permissions.IsAuthenticated,)

    # send the total dues of a customer to all the vendors
    def post(self, request, *args, **kwargs):
        user_id = self.kwargs["user_id"]
        user = CustomUser.objects.get(user_id=user_id)
        wallet = Wallet.objects.get(user=user)
        transactions = Transaction.objects.filter(
            sender=wallet, transaction_status=2
        )

        total_pending_dues = 0
        pending_dues = {}
        for transaction in transactions:
            total_pending_dues += transaction.transaction_amount
            # transaction.transaction_status = 4 # 4 means cleared
            # transaction.save()
            # receiver_wallet = transaction.receiver
            # receiver = receiver_wallet.user.user_id
            # if receiver not in pending_dues:
            #     pending_dues[receiver] = 0
            # pending_dues[receiver] += transaction.transaction_amount


        if wallet.balance < total_pending_dues:
            return Response({"message": "Insufficient balance. Kindly recharge."})
        else:
            for transaction in transactions:
                transaction.transaction_status = 4 # 4 means cleared
                transaction.save()
                receiver_wallet = transaction.receiver
                receiver = receiver_wallet.user.user_id
                if receiver not in pending_dues:
                    pending_dues[receiver] = 0
                pending_dues[receiver] += transaction.transaction_amount

            wallet = Wallet.objects.get(user=user)

            for receiver in pending_dues:
                receiver_wallet = Wallet.objects.get(user__user_id=receiver)
                transaction = Transaction.objects.create(
                    sender=wallet,
                    receiver=receiver_wallet,
                    transaction_amount=pending_dues[receiver],
                    transaction_status=0,
                )
                print("New Transaction instantiated while clearing dues")
                # transaction.save()
            return Response({"message": "Dues cleared successfully."})
        
        
# clearing all the dues of a customer to a particular vendor
class ClearDuesVendor(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user_id = self.kwargs["user_id"]
        receiver_id = request.data["receiver_id"]
        user = CustomUser.objects.get(user_id=user_id)
        receiver = CustomUser.objects.get(user_id=receiver_id)
        wallet = Wallet.objects.get(user=user)
        receiver_wallet = Wallet.objects.get(user=receiver)
        transactions = Transaction.objects.filter(
            sender=wallet, receiver=receiver_wallet, transaction_status=2
        )

        total_pending_dues = 0
        for transaction in transactions:
            total_pending_dues += transaction.transaction_amount
            # transaction.transaction_status = 4
            # transaction.save()
        
        # wallet = Wallet.objects.get(user=user)
        # receiver_wallet = Wallet.objects.get(user=receiver)

        if wallet.balance < total_pending_dues:
            return Response({"message": "Insufficient balance. Kindly recharge."})
        else:
            for transaction in transactions:
                transaction.transaction_status = 4
                transaction.save()
            wallet = Wallet.objects.get(user=user)
            receiver_wallet = Wallet.objects.get(user=receiver)
            # print("Views sender pending, ", wallet.pending)
            transaction = Transaction.objects.create(
                sender=wallet,
                receiver=receiver_wallet,
                transaction_amount=total_pending_dues,
                transaction_status=0,
            )
            # print("New Transaction instantiated while clearing dues")
            return Response({"message": "Dues cleared successfully."})
        
class UserAddBalance(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        user_id = self.kwargs["user_id"]
        user = CustomUser.objects.get(user_id=user_id)
        wallet = Wallet.objects.get(user=user)

        wallet.balance += request.data["amount"]
        wallet.save()
        return Response({"message": "Balance addition successful!"})