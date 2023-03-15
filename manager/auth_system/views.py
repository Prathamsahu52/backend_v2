from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers, permissions
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserSerializer,
    EmailSerializer,
    PasswordResetSerializer,
)
from django.contrib.auth import get_user_model, authenticate, login, logout
from rest_framework.authentication import SessionAuthentication

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.contrib.auth.tokens import PasswordResetTokenGenerator

UserModel = get_user_model()


class UserRegister(APIView):
    permission_classes = (permissions.AllowAny,)

    def clean_data(self, data):
        if UserModel.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError("This email is already registered")
        if UserModel.objects.filter(phone_number=data["phone_number"]).exists():
            raise serializers.ValidationError("This phone number is already registered")
        return data

    def post(self, request, format=None):
        data = self.clean_data(request.data)
        serializer = UserRegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogin(APIView):
    # use the UserLoginSerializer to validate the data
    serializer_class = UserLoginSerializer
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return Response(
                    {"message": "User logged in succesfully"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class UserLogout(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        logout(request)
        return Response(
            {"message": "User logged out succesfully"}, status=status.HTTP_200_OK
        )


class UserView(APIView):
    permissions_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({"user": serializer.data}, status=status.HTTP_200_OK)


class PasswordReset(APIView):
    permissions = (permissions.AllowAny,)
    serializer_class = EmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = UserModel.objects.get(email=email)
            if user is not None:
                encoded_pk = urlsafe_base64_encode(force_bytes(user.pk))
                token = PasswordResetTokenGenerator().make_token(user)
                url = reverse(
                    "reset-password", kwargs={"encoded_pk": encoded_pk, "token": token}
                )
                link = request.build_absolute_uri(url)

                return Response(
                    {"message": f"Password reset link: {link}"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPI(APIView):

    serializer_class = PasswordResetSerializer

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"kwargs": kwargs}
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": "Password reset complete"},
            status=status.HTTP_200_OK,
        )
