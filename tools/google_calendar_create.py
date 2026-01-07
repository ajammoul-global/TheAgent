"""
Google Calendar Create Tool
Creates calendar events via Google Calendar API
"""
from tools.base import BaseTool
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class GoogleCalendarCreateTool(BaseTool):
    """Tool for creating Google Calendar events"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, timezone: str = "Asia/Beirut"):
        """
        Initialize Google Calendar Create Tool
        
        Args:
            timezone: Timezone for events (e.g., "America/New_York", "Asia/Beirut")
        """
        self.timezone = timezone
        self.service = None
        self._name = "google_calendar_create"
        self._description = "Create a new event in Google Calendar. Use this to schedule meetings, appointments, or reminders."
        self._parameters = {
            "summary": {
                "type": "string",
                "description": "Event title/summary (e.g., 'Team Meeting', 'Dentist Appointment')",
                "required": True
            },
            "start_time": {
                "type": "string",
                "description": "Start time in ISO format (e.g., '2024-01-15T10:00:00')",
                "required": True
            },
            "end_time": {
                "type": "string",
                "description": "End time in ISO format (e.g., '2024-01-15T11:00:00')",
                "required": True
            },
            "description": {
                "type": "string",
                "description": "Event description/notes (optional)",
                "required": False
            },
            "location": {
                "type": "string",
                "description": "Event location (optional)",
                "required": False
            },
            "attendees": {
                "type": "string",
                "description": "Comma-separated email addresses of attendees (optional)",
                "required": False
            }
        }
        logger.info(f"GoogleCalendarCreateTool initialized (timezone: {timezone})")
    
    @property
    def name(self) -> str:
        """Tool name"""
        return self._name
    
    @property
    def description(self) -> str:
        """Tool description"""
        return self._description
    
    @property
    def parameters(self) -> dict:
        """Tool parameters"""
        return self._parameters
    
    def _get_credentials(self):
        """Get or refresh Google Calendar credentials"""
        creds = None
        token_path = '/app/credentials/token.pickle'
        credentials_path = '/app/credentials/credentials.json'
        
        # Load existing token
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        f"Google Calendar credentials not found at {credentials_path}. "
                        "Please download credentials.json from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def _get_service(self):
        """Get Google Calendar service"""
        if self.service is None:
            creds = self._get_credentials()
            self.service = build('calendar', 'v3', credentials=creds)
        return self.service
    
    def execute(self, **kwargs) -> str:
        """
        Create a calendar event
        
        Args:
            summary: Event title
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            description: Event description (optional)
            location: Event location (optional)
            attendees: Comma-separated emails (optional)
            
        Returns:
            Success message with event link
        """
        try:
            service = self._get_service()
            
            # Extract parameters
            summary = kwargs.get('summary')
            start_time = kwargs.get('start_time')
            end_time = kwargs.get('end_time')
            description = kwargs.get('description', '')
            location = kwargs.get('location', '')
            attendees_str = kwargs.get('attendees', '')
            
            # Validate required parameters
            if not summary or not start_time or not end_time:
                return "❌ Error: summary, start_time, and end_time are required"
            
            # Build event body
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time,
                    'timeZone': self.timezone,
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': self.timezone,
                },
            }
            
            # Add optional fields
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            if attendees_str:
                emails = [email.strip() for email in attendees_str.split(',')]
                event['attendees'] = [{'email': email} for email in emails]
                event['sendUpdates'] = 'all'  # Send invites to attendees
            
            # Create the event
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            event_link = created_event.get('htmlLink')
            event_id = created_event.get('id')
            
            logger.info(f"Created calendar event: {summary} (ID: {event_id})")
            
            return f"✅ Event created successfully!\n\n" \
                   f"📅 {summary}\n" \
                   f"🕐 {start_time} → {end_time}\n" \
                   f"🔗 {event_link}"
        
        except FileNotFoundError as e:
            logger.error(f"Credentials not found: {e}")
            return f"❌ Error: {str(e)}"
        
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}", exc_info=True)
            return f"❌ Error creating event: {str(e)}"