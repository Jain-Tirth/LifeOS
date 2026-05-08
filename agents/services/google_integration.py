"""
Google Integration Service.
This service syncs `CalendarEvent` and `EmailMessage` models 
to Google Calendar and Gmail APIs.
"""

import os
import logging
import base64
from typing import Optional
from email.message import EmailMessage as PyEmailMessage

from asgiref.sync import sync_to_async
from django.conf import settings
from agents.models import CalendarEvent, EmailMessage

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_LIBS_INSTALLED = True
except ImportError:
    GOOGLE_LIBS_INSTALLED = False

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/gmail.compose'
]

class GoogleIntegration:

    def __init__(self):
        self.creds = None
        if GOOGLE_LIBS_INSTALLED:
            self._authenticate()
        else:
            logger.warning("Google API libraries are not installed. Please run `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`.")

    def _authenticate(self):
        """
        Handles Google OAuth2 authentication.
        Expects a `credentials.json` file in the root directory.
        Creates a `token.json` file on successful auth.
        """
        token_path = os.path.join(settings.BASE_DIR, 'token.json')
        creds_path = os.path.join(settings.BASE_DIR, 'credentials.json')

        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh Google token: {e}")
                    self.creds = None
            
            if not self.creds and os.path.exists(creds_path):
                # Note: In a production web environment, InstalledAppFlow (which opens a browser)
                # should be replaced with a proper Web OAuth flow using redirect URIs.
                logger.info("Initiating Google OAuth flow...")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)

                    # Save the credentials for the next run
                    with open(token_path, 'w') as token:
                        token.write(self.creds.to_json())
                except Exception as e:
                    logger.error(f"Google OAuth flow failed: {e}")
            elif not os.path.exists(creds_path):
                logger.warning("credentials.json not found. Google API integration disabled.")

    @sync_to_async
    def sync_calendar_event(self, event: CalendarEvent) -> Optional[str]:
        """Creates an event in the user's primary Google Calendar."""
        if not self.creds:
            logger.error("Cannot sync calendar: Google API not authenticated.")
            return None

        try:
            service = build('calendar', 'v3', credentials=self.creds)

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

            logger.info(f"Successfully synced event '{event.title}' to Google Calendar (ID: {event_id})")
            return event_id

        except Exception as e:
            logger.error(f"Failed to sync calendar event: {e}", exc_info=True)
            return None

    @sync_to_async
    def sync_email_draft(self, email_model: EmailMessage) -> Optional[str]:
        """Creates a draft email in the user's Gmail account."""
        if not self.creds:
            logger.error("Cannot sync email: Gmail API not authenticated.")
            return None
            
        try:
            service = build('gmail', 'v1', credentials=self.creds)
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
            
            logger.info(f"Successfully synced email draft '{email_model.subject}' to Gmail (ID: {draft_id})")
            return draft_id
            
        except Exception as e:
            logger.error(f"Failed to sync email draft: {e}", exc_info=True)
            return None

google_service = GoogleIntegration()
