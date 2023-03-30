from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.CustomUserList.as_view(), name="users"),
    path("users/customers/", views.CustomerList.as_view(), name="customers"),
    path("users/vendors/", views.VendorList.as_view(), name="vendors"),
    path("users/<str:user_id>/", views.CustomUserDetail.as_view(), name="user"),
    path("users/<str:user_id>/transactions/", views.UserTransactionList.as_view(), name="user_transactions"),
    path("users/<str:user_id>/navbar/", views.OverviewNavbar.as_view(), name="navbar-details"),
    path("users/<str:user_id>/overview/", views.OverviewTable.as_view(), name="overview-details"),
    path("users/<str:user_id>/transactions/make/", views.UserMakeTransaction.as_view(), name="user_transactions_post"),
    path("users/<str:user_id>/clear_dues/", views.ClearDues.as_view(), name="clear_dues"),
    path("users/<str:user_id>/clear_vendor_dues/", views.ClearDuesVendor.as_view(), name="clear_dues_vendor"),
    path("users/<str:user_id>/vendors/", views.CustomerVendorList.as_view(), name="customer_vendor"),
    path("users/<str:user_id>/customers/", views.VendorCustomerList.as_view(), name="vendor_customer"),
    path("users/<str:user_id>/pending_dues/", views.PendingDuesList.as_view(), name="pending_dues"),
    path("users/<str:user_id>/pending_dues_vendor/", views.PendingDuesVendor.as_view(), name="pending_due_for_vendor"),
    path("users/<str:user_id>/request_clearance/", views.RequestClearance.as_view(), name="request_clearance"),
    path("users/<str:user_id>/notifications/", views.UserNotificationList.as_view(), name="notification"),
    path("users/<str:user_id>/add_balance/", views.UserAddBalance.as_view(), name="add_balance"), 
    path("transactions/", views.TransactionList.as_view(), name="transactions"),
    path("transactions/<str:transaction_id>/", views.TransactionDetail.as_view(), name="transaction"),
    path("notifications/", views.NotificationList.as_view(), name="notifications"),
]
