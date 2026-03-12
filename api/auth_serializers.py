from rest_framework import serializers
from agents.models import User, UserProfile
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import AccessToken

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create new user with hashed password"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user preferences — the brain of personalization"""
    
    class Meta:
        model = UserProfile
        fields = (
            'timezone', 'dietary_preferences', 'work_hours',
            'fitness_level', 'health_conditions', 'learning_style',
            'goals', 'about_me', 'updated_at'
        )
        read_only_fields = ('updated_at',)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details with nested profile"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'date_joined', 'profile')
        read_only_fields = ('id', 'date_joined')
