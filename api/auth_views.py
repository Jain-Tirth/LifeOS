from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework_simplejwt.tokens import AccessToken
from agents.models import User
from agents.services.event_bus import audit_logger
from .auth_serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserSerializer
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """
    Get CSRF token for subsequent requests.
    This sets the CSRF cookie and returns the token.
    """
    return Response({'csrfToken': get_token(request)})


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user with email and password.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "strongpassword123",
        "password_confirm": "strongpassword123",
        "first_name": "John",  (optional)
        "last_name": "Doe"     (optional)
    }
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT token
        token = AccessToken.for_user(user)
        
        # Audit log
        audit_logger.log_authentication(
            action='User Registration',
            user=user,
            details={
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            success=True
        )
        
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(user).data,
            'token': str(token)
        }, status=status.HTTP_201_CREATED)
    
    # Audit failed registration
    audit_logger.log_authentication(
        action='Failed User Registration',
        user=None,
        details={
            'email': request.data.get('email'),
            'errors': serializer.errors
        },
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        success=False,
        error_message=str(serializer.errors)
    )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login with email and password.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "yourpassword"
    }
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    # Authenticate user
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            # Audit failed login
            audit_logger.log_authentication(
                action='Failed Login - Invalid Password',
                user=user,
                details={'email': email},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                success=False,
                error_message='Invalid password'
            )
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            # Audit failed login - inactive account
            audit_logger.log_authentication(
                action='Failed Login - Inactive Account',
                user=user,
                details={'email': email},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                success=False,
                error_message='Account is disabled'
            )
            return Response({
                'error': 'Account is disabled'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate JWT token
        token = AccessToken.for_user(user)
        
        # Audit successful login
        audit_logger.log_authentication(
            action='User Login',
            user=user,
            details={'email': email},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            success=True
        )
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'token': str(token)
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # Audit failed login - user not found
        audit_logger.log_authentication(
            action='Failed Login - User Not Found',
            user=None,
            details={'email': email},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            success=False,
            error_message='User does not exist'
        )
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get current user profile.
    Requires Authentication header: Bearer <token>
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Update current user profile.
    Requires Authentication header: Bearer <token>
    
    Request body:
    {
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
