from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator


UserModel = get_user_model()
Types = UserModel.Types


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=128, write_only=True)
    confirm_password = serializers.CharField(max_length=128, write_only=True)
    # type = serializers.ChoiceField(choices=Types)

    class Meta:
        model = UserModel
        fields = (
            "username",
            "email",
            "phone_number",
            "type",
            "password",
            "confirm_password",
        )
        extra_kwargs = {"password": {"write_only": True}, "type": {"required": True}}

    def validate(self, data):
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError("Passwords must match")
        return data

    def create(self, validated_data):
        # password = validated_data.pop("password")
        user = UserModel.objects.create_user(**validated_data)
        user.save()
        return user


class UserLoginSerializer(serializers.ModelSerializer):
    # logging using username and password
    username = serializers.CharField(max_length=255, required=False)
    password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = UserModel
        fields = ("username", "password")
    
    def validate(self, data):
        username = data.get("username", None)
        password = data.get("password", None)
        if username is None:
            raise serializers.ValidationError("A username is required to login")
        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError("A user with this username and password is not found")
        if not user.is_active:
            raise serializers.ValidationError("This user has been deactivated")
        return data
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ("user_id", "email", "username", "type", "phone_number")

class EmailSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField(max_length=255)
    class Meta:
        fields = ("email",)
    
class PasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, write_only=True)
    confirm_password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        fields = ("password", "confirm_password")

    def validate(self, data):
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError("Passwords must match")
        password = data.get("password")
        token = self.context.get("kwargs").get("token")
        encoded_pk = self.context.get("kwargs").get("encoded_pk")

        if token is None or encoded_pk is None:
            raise serializers.ValidationError("Invalid token or user id")
        
        pk = urlsafe_base64_decode(encoded_pk).decode()
        user = UserModel.objects.get(pk=pk)

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError("The reset token is invalid")
        
        user.set_password(password)
        user.save()

        return data
        