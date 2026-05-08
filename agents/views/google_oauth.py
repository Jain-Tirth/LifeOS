"""Google OAuth view handlers for multi-user token management."""

import logging
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.utils import timezone

try:
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    GOOGLE_LIBS_INSTALLED = True
except ImportError:
    GOOGLE_LIBS_INSTALLED = False

from agents.models import GoogleToken

logger = logging.getLogger(__name__)

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/gmail.compose'
]


@login_required
@require_http_methods(['GET'])
def google_oauth_start(request):
    """
    Initiate Google OAuth flow.
    
    Redirects user to Google consent screen. Stores state in session for CSRF validation.
    """
    if not GOOGLE_LIBS_INSTALLED:
        logger.error("Google libraries not installed")
        return HttpResponseBadRequest("Google OAuth not configured")
    
    try:
        creds_path = getattr(settings, 'GOOGLE_CREDENTIALS_PATH', None)
        if not creds_path:
            logger.error("GOOGLE_CREDENTIALS_PATH not configured in settings")
            return HttpResponseBadRequest("Google OAuth not configured")
        
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback/')
        
        flow = Flow.from_client_secrets_file(
            creds_path,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        auth_url, state = flow.authorization_url(access_type='offline', prompt='consent')
        request.session['google_oauth_state'] = state
        
        logger.info(f"OAuth flow initiated for user {request.user.email}")
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Failed to initiate OAuth flow: {e}", exc_info=True)
        return HttpResponseBadRequest(f"OAuth error: {e}")


@login_required
@require_http_methods(['GET'])
def google_oauth_callback(request):
    """
    Handle OAuth callback from Google.
    
    Validates state, exchanges code for credentials, and saves token to DB.
    Redirects to success page after storing credentials.
    """
    if not GOOGLE_LIBS_INSTALLED:
        logger.error("Google libraries not installed")
        return HttpResponseBadRequest("Google OAuth not configured")
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    # Check for OAuth errors from Google
    if error:
        logger.warning(f"OAuth error from Google: {error}")
        return HttpResponseBadRequest(f"Authorization failed: {error}")
    
    # Validate state for CSRF protection
    session_state = request.session.get('google_oauth_state')
    if not state or state != session_state:
        logger.warning(f"Invalid state in OAuth callback for user {request.user.email}")
        return HttpResponseBadRequest("Invalid state parameter (CSRF validation failed)")
    
    if not code:
        logger.warning("No authorization code in OAuth callback")
        return HttpResponseBadRequest("No authorization code provided")
    
    try:
        creds_path = getattr(settings, 'GOOGLE_CREDENTIALS_PATH', None)
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback/')
        
        flow = Flow.from_client_secrets_file(
            creds_path,
            scopes=SCOPES,
            redirect_uri=redirect_uri,
            state=state
        )
        
        creds = flow.fetch_token(code=code)
        
        # Save or update GoogleToken in DB for this user
        token_data = {
            'access_token': creds.get('access_token', ''),
            'refresh_token': creds.get('refresh_token', ''),
            'token_uri': creds.get('token_uri', 'https://oauth2.googleapis.com/token'),
            'client_id': creds.get('client_id', ''),
            'client_secret': creds.get('client_secret', ''),
            'scopes': ','.join(creds.get('scopes', SCOPES)),
        }
        
        # Parse expiry if present
        if creds.get('expires_in'):
            token_data['expiry'] = timezone.now() + timezone.timedelta(seconds=creds['expires_in'])
        
        google_token, created = GoogleToken.objects.update_or_create(
            user=request.user,
            defaults=token_data
        )
        
        logger.info(f"Google OAuth token {'created' if created else 'updated'} for user {request.user.email}")
        
        # Clean up state from session
        del request.session['google_oauth_state']
        
        success_redirect = getattr(settings, 'GOOGLE_OAUTH_SUCCESS_REDIRECT', '/')
        return redirect(success_redirect)
        
    except Exception as e:
        logger.error(f"Failed to exchange OAuth code for user {request.user.email}: {e}", exc_info=True)
        return HttpResponseBadRequest(f"Token exchange failed: {e}")
