from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'role'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_role(self, value):
        """Only admin users can create other admin users"""
        request = self.context.get('request')
        if value == 'admin' and request and request.user.is_authenticated:
            if not request.user.is_admin_lawyer:
                raise serializers.ValidationError(
                    "Only admin lawyers can create admin accounts"
                )
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization'
            )


class UserProfileSerializer(serializers.ModelSerializer):
    lawyer_name = serializers.CharField(
        source='lawyer_profile.name',
        read_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'lawyer_profile', 'lawyer_name', 'date_joined',
            'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'lawyer_profile']
    
    def validate_role(self, value):
        """Users cannot change their own role"""
        if self.instance and self.instance.role != value:
            request = self.context.get('request')
            if request and request.user == self.instance:
                raise serializers.ValidationError(
                    "You cannot change your own role"
                )
            if request and not request.user.is_admin_lawyer:
                raise serializers.ValidationError(
                    "Only admin lawyers can change user roles"
                )
        return value


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for user lists"""
    lawyer_name = serializers.CharField(
        source='lawyer_profile.name',
        read_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'lawyer_name', 'is_active'
        ]