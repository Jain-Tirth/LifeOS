from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.core.cache import cache
from backend.users.models import User, UserProfile
from backend.execution.logs.event_bus import audit_logger
from .auth_serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserSerializer,
    UserProfileSerializer
)
from .throttles import AuthRateThrottle


# Rate limiting configuration
LOGIN_RATE_LIMIT = 5  # Max failed attempts
LOGIN_LOCKOUT_TIME = 900  # 15 minutes in seconds


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_login_rate_limit(email):
    """Check if email is rate limited due to failed login attempts"""
    cache_key = f'login_failed_{email}'
    attempts = cache.get(cache_key, 0)
    
    if attempts >= LOGIN_RATE_LIMIT:
        lockout_time = cache.ttl(cache_key) or LOGIN_LOCKOUT_TIME
        return False, lockout_time
    
    return True, None


def record_failed_login(email):
    """Record a failed login attempt"""
    cache_key = f'login_failed_{email}'
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, timeout=LOGIN_LOCKOUT_TIME)
    return attempts


def reset_login_attempts(email):
    """Reset login attempts after successful login"""
    cache_key = f'login_failed_{email}'
    cache.delete(cache_key)


@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """Get CSRF token for subsequent requests."""
    return Response({'csrfToken': get_token(request)})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def register(request):
    """Register a new user. UserProfile is auto-created via signal. Rate limited to prevent abuse."""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Ensure profile exists (signal should create it, but be safe)
        UserProfile.objects.get_or_create(user=user)
        
        # Generate both access and refresh tokens for persistent sessions
        refresh = RefreshToken.for_user(user)
        
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
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)
    
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
@throttle_classes([AuthRateThrottle])
def login(request):
    """Login with email and password. Includes rate limiting for brute-force protection."""
    serializer = UserLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    # Check rate limit before attempting authentication
    is_allowed, lockout_time = check_login_rate_limit(email)
    if not is_allowed:
        audit_logger.log_authentication(
            action='Failed Login - Rate Limited',
            user=None,
            details={'email': email},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            success=False,
            error_message=f'Account temporarily locked due to too many failed attempts'
        )
        return Response({
            'error': f'Too many failed login attempts. Please try again in {lockout_time // 60} minutes.'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            # Record failed attempt
            attempts = record_failed_login(email)
            
            audit_logger.log_authentication(
                action='Failed Login - Invalid Password',
                user=user,
                details={'email': email, 'attempts': attempts},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                success=False,
                error_message='Invalid password'
            )
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
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
        
        # Reset failed attempts on successful login
        reset_login_attempts(email)
        
        # Ensure profile exists for existing users
        UserProfile.objects.get_or_create(user=user)
        
        # Generate both access and refresh tokens for persistent sessions
        refresh = RefreshToken.for_user(user)
        
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
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # Record failed attempt for non-existent user (prevents user enumeration)
        record_failed_login(email)
        
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout endpoint for clients that want a consistent API response."""
    return Response({
        'message': 'Logout successful'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh a JWT access token using a valid refresh token."""
    serializer = TokenRefreshSerializer(data=request.data)

    if serializer.is_valid():
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get current user profile including preferences."""
    UserProfile.objects.get_or_create(user=request.user)
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """Update current user's basic info (first_name, last_name)."""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_preferences(request):
    """
    Update user preferences that agents use for personalization.
    
    Example request body:
    {
        "timezone": "Asia/Kolkata",
        "dietary_preferences": {"type": "vegetarian", "allergies": ["nuts"]},
        "work_hours": {"start": "09:00", "end": "18:00"},
        "fitness_level": "intermediate",
        "goals": [{"goal": "Lose 5kg", "deadline": "2026-06-01", "category": "wellness"}],
        "about_me": "I'm a software developer who works from home"
    }
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Preferences updated successfully',
            'preferences': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    '''Request password reset email.'''
    # In a real application, we would generate a token and send an email
    # For now, we just return a success message to avoid exposing whether the user exists
    return Response({'message': 'If the user exists, a password reset email has been sent'}, status=status.HTTP_200.OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    '''Reset password using token and new password.'''
    # In a real application, we would validate the token and set the password
    # For now, we just return a success message
    return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200.OK)
