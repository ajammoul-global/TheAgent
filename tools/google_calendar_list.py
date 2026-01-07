"""
Google Calendar List Tool
Lists upcoming calendar events
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


class GoogleCalendarListTool(BaseTool):
    """Tool for listing Google Calendar events"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self):
        """Initialize Google Calendar List Tool"""
        self.service = None
        self._name = "google_calendar_list"
        self._description = "List upcoming events from Google Calendar. Use this to check your schedule, find appointments, or see what's coming up."
        self._parameters = {
            "max_results": {
                "type": "integer",
                "description": "Maximum number of events to return (default: 10)",
                "required": False
            },
            "time_min": {
                "type": "string",
                "description": "Start time filter in ISO format (default: now)",
                "required": False
            },
            "time_max": {
                "type": "string",
                "description": "End time filter in ISO format (optional)",
                "required": False
            },
            "query": {
                "type": "string",
                "description": "Search query to filter events (optional)",
                "required": False
            }
        }
        logger.info("GoogleCalendarListTool initialized")
    
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
    
    def _format_datetime(self, dt_str):
        """Format datetime string for display"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return dt_str
    
    def execute(self, **kwargs) -> str:
        """
        List calendar events
        
        Args:
            max_results: Maximum number of events (default: 10)
            time_min: Start time filter (default: now)
            time_max: End time filter (optional)
            query: Search query (optional)
            
        Returns:
            Formatted list of events
        """
        try:
            service = self._get_service()
            
            # Extract parameters
            max_results = int(kwargs.get('max_results', 10))
            time_min = kwargs.get('time_min')
            time_max = kwargs.get('time_max')
            query = kwargs.get('query')
            
            # Default time_min to now if not provided
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            
            # Build request parameters
            request_params = {
                'calendarId': 'primary',
                'timeMin': time_min,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            if time_max:
                request_params['timeMax'] = time_max
            
            if query:
                request_params['q'] = query
            
            # Get events
            events_result = service.events().list(**request_params).execute()
            events = events_result.get('items', [])
            
            if not events:
                return "📅 No upcoming events found."
            
            # Format events
            output = f"📅 Upcoming Events ({len(events)}):\n\n"
            
            for i, event in enumerate(events, 1):
                summary = event.get('summary', 'No title')
                start = event.get('start', {})
                end = event.get('end', {})
                
                # Get start time
                start_time = start.get('dateTime', start.get('date', 'N/A'))
                end_time = end.get('dateTime', end.get('date', 'N/A'))
                
                # Format display
                output += f"{i}. {summary}\n"
                output += f"   🕐 {self._format_datetime(start_time)}"
                
                if end_time != 'N/A':
                    output += f" → {self._format_datetime(end_time)}"
                
                # Add location if available
                location = event.get('location')
                if location:
                    output += f"\n   📍 {location}"
                
                # Add description preview if available
                description = event.get('description')
                if description:
                    preview = description[:50] + "..." if len(description) > 50 else description
                    output += f"\n   📝 {preview}"
                
                output += "\n\n"
            
            logger.info(f"Listed {len(events)} calendar events")
            return output.strip()
        
        except FileNotFoundError as e:
            logger.error(f"Credentials not found: {e}")
            return f"❌ Error: {str(e)}"
        
        except Exception as e:
            logger.error(f"Error listing calendar events: {e}", exc_info=True)
            return f"❌ Error listing events: {str(e)}"