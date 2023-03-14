from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers, permissions
from .serializers import UserRegisterSerializer, UserLoginSerializer, UserSerializer
from django.contrib.auth import get_user_model, authenticate, login, logout
from rest_framework.authentication import SessionAuthentication


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
