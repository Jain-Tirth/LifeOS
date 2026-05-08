"""
Google Integration Service.
This service syncs `CalendarEvent` and `EmailMessage` models 
to Google Calendar and Gmail APIs.

Uses per-user OAuth tokens stored in the database (GoogleToken model)
instead of single-user file-based tokens.
"""

import logging
import base64
from typing import Optional
from email.message import EmailMessage as PyEmailMessage

from asgiref.sync import sync_to_async
from django.utils import timezone
from agents.models import CalendarEvent, EmailMessage, GoogleToken, User

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from google.oauth2.credentials import Credentials  # type: ignore[reportMissingImports]
    from google.auth.transport.requests import Request  # type: ignore[reportMissingImports]
    from googleapiclient.discovery import build  # type: ignore[reportMissingImports]
    GOOGLE_LIBS_INSTALLED = True
except ImportError:
    GOOGLE_LIBS_INSTALLED = False

logger = logging.getLogger(__name__)

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/gmail.compose'
]


class GoogleIntegration:

    def __init__(self):
        """Initialize the service. No file-based auth at import time."""
        pass

    def get_credentials(self, user: User) -> Optional[Credentials]:
        """
        Load and refresh credentials for a specific user from the database.
        
        Args:
            user: The User object to get credentials for
            
        Returns:
            Credentials object or None if token doesn't exist or refresh fails
        """
        if not GOOGLE_LIBS_INSTALLED:
            logger.warning("Google libraries not installed")
            return None
        
        try:
            google_token = GoogleToken.objects.get(user=user)
        except GoogleToken.DoesNotExist:
            logger.warning(f"No Google token found for user {user.email}")
            return None
        
        try:
            # Reconstruct Credentials object from DB
            creds = Credentials(
                token=google_token.access_token,
                refresh_token=google_token.refresh_token,
                token_uri=google_token.token_uri,
                client_id=google_token.client_id,
                client_secret=google_token.client_secret,
                scopes=google_token.scopes.split(',') if google_token.scopes else SCOPES,
            )
            creds.expiry = google_token.expiry
            
            # Refresh if expired
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Update DB with refreshed token
                    google_token.access_token = creds.token
                    google_token.expiry = creds.expiry
                    google_token.save(update_fields=['access_token', 'expiry'])
                    logger.info(f"Refreshed Google token for user {user.email}")
                except Exception as e:
                    logger.error(f"Failed to refresh Google token for user {user.email}: {e}")
                    return None
            
            return creds
            
        except Exception as e:
            logger.error(f"Failed to load credentials for user {user.email}: {e}", exc_info=True)
            return None
                
                
    def _sync_calendar_event_sync(self, user: User, event: CalendarEvent) -> Optional[str]:
        """Pure sync implementation — intended to be called from threadpool wrappers.

        This extracts the synchronous work into a private helper so that
        `@sync_to_async` wrappers call this function directly (avoids returning
        coroutine objects from within sync threads).
        
        Args:
            user: The User object with Google OAuth credentials
            event: The CalendarEvent to sync
            
        Returns:
            Event ID from Google Calendar or None if sync failed
        """
        creds = self.get_credentials(user)
        if not creds:
            logger.error(f"Cannot sync calendar for user {user.email}: No Google credentials")
            return None

        try:
            service = build('calendar', 'v3', credentials=creds)

            body = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            created_event = service.events().insert(calendarId='primary', body=body).execute()
            event_id = created_event.get('id')

            # Update local record with external ID
            event.event_id = event_id
            event.save(update_fields=['event_id'])

            logger.info(f"Successfully synced event '{event.title}' to Google Calendar (ID: {event_id}) for user {user.email}")
            return event_id

        except Exception as e:
            logger.error(f"Failed to sync calendar event for user {user.email}: {e}", exc_info=True)
            return None

    @sync_to_async
    def sync_calendar_event(self, user: User, event: CalendarEvent) -> Optional[str]:
        """Creates an event in the user's primary Google Calendar (async wrapper)."""
        return self._sync_calendar_event_sync(user, event)

    @sync_to_async
    def create_event(self, user: User, event: CalendarEvent) -> Optional[str]:
        """Alias used by the execution agent prompt for creating calendar events."""
        return self._sync_calendar_event_sync(user, event)

    @sync_to_async
    def update_event(self, user: User, event: CalendarEvent) -> Optional[str]:
        """Alias used by the execution agent prompt for updating calendar events."""
        return self._sync_calendar_event_sync(user, event)

    @sync_to_async
    def get_events(self, user: User, limit: int = 20):
        """Return recent local calendar events for a user."""
        queryset = CalendarEvent.objects.filter(user=user).order_by('-start_time')
        return list(queryset[:limit])

    @sync_to_async
    def sync_email_draft(self, user: User, email_model: EmailMessage) -> Optional[str]:
        """Creates a draft email in the user's Gmail account."""
        creds = self.get_credentials(user)
        if not creds:
            logger.error(f"Cannot sync email for user {user.email}: No Google credentials")
            return None
            
        try:
            service = build('gmail', 'v1', credentials=creds)
            profile = service.users().getProfile(userId='me').execute()
            authenticated_email = profile.get('emailAddress')

            if authenticated_email and getattr(email_model, 'from_address', None) != authenticated_email:
                email_model.from_address = authenticated_email
                email_model.save(update_fields=['from_address'])
            
            message = PyEmailMessage()
            message.set_content(email_model.body)
            if authenticated_email:
                message['From'] = authenticated_email
            elif getattr(email_model, 'from_address', None):
                message['From'] = email_model.from_address
            message['To'] = email_model.to_address
            message['Subject'] = email_model.subject
            
            # Encode as base64url string
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            create_message = {
                'message': {
                    'raw': encoded_message
                }
            }
            
            draft = service.users().drafts().create(userId="me", body=create_message).execute()
            draft_id = draft.get('id')
            
            # Update local record with external ID
            email_model.message_id = draft_id
            email_model.save(update_fields=['message_id'])
            
            logger.info(f"Successfully synced email draft '{email_model.subject}' to Gmail (ID: {draft_id}) for user {user.email}")
            return draft_id
            
        except Exception as e:
            logger.error(f"Failed to sync email draft for user {user.email}: {e}", exc_info=True)
            return None
