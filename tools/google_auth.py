"""
Google API Authentication Module

Shared OAuth and credential management for all Google Workspace tools.
Handles token loading, refresh, and API client initialization.

Usage:
    from tools.google_auth import GoogleAPIClient
    
    client = GoogleAPIClient(service='calendar', version='v3')
    service = client.get_service()
"""

import os
import pickle
from typing import Optional
from infra.logging import logger


class GoogleAPIClient:
    """
    Reusable Google API client with OAuth2 authentication.
    
    Handles:
    - Token loading from file
    - Token refresh and validation
    - OAuth flow for new credentials
    - API service initialization
    
    Supports multiple Google Workspace services (Calendar, Gmail, Drive, etc.)
    """
    
    CREDENTIALS_DIR = '/app/credentials'
    TOKEN_FILE = os.path.join(CREDENTIALS_DIR, 'token.pickle')
    CREDS_FILE = os.path.join(CREDENTIALS_DIR, 'credentials.json')
    
    def __init__(self, service: str = 'calendar', version: str = 'v3', scopes: Optional[list] = None):
        """
        Initialize Google API client.
        
        Args:
            service: Google API service name (e.g., 'calendar', 'gmail', 'drive')
            version: API version (e.g., 'v3')
            scopes: List of OAuth scopes. If None, uses default for service.
        """
        self.service_name = service
        self.version = version
        self._credentials = None
        self._service = None
        self._initialized = False
        
        # Default scopes for each service
        if scopes is None:
            scopes = self._get_default_scopes(service)
        self.scopes = scopes
        
        logger.info(f"GoogleAPIClient initialized for {service}/{version}")
    
    @staticmethod
    def _get_default_scopes(service: str) -> list:
        """Return default OAuth scopes for a given service."""
        scopes_map = {
            'calendar': ['https://www.googleapis.com/auth/calendar'],
            'gmail': ['https://www.googleapis.com/auth/gmail.modify'],
            'drive': ['https://www.googleapis.com/auth/drive'],
            'sheets': ['https://www.googleapis.com/auth/spreadsheets'],
        }
        return scopes_map.get(service, [f'https://www.googleapis.com/auth/{service}'])
    
    def _load_credentials(self):
        """Load credentials from file or return None."""
        if os.path.exists(self.TOKEN_FILE):
            try:
                with open(self.TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded credentials from token file")
                return creds
            except Exception as e:
                logger.warning(f"Failed to load token file: {e}")
        return None
    
    def _refresh_credentials(self, creds):
        """Refresh expired credentials."""
        try:
            from google.auth.transport.requests import Request
            
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("Refreshed expired credentials")
                self._save_credentials(creds)
                return True
        except Exception as e:
            logger.warning(f"Failed to refresh credentials: {e}")
        return False
    
    def _authenticate_new(self):
        """Run OAuth flow for new credentials."""
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            if not os.path.exists(self.CREDS_FILE):
                raise FileNotFoundError(
                    f"Google credentials file not found at {self.CREDS_FILE}. "
                    f"Please download credentials.json from Google Cloud Console and place it in /app/credentials/"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(self.CREDS_FILE, self.scopes)
            creds = flow.run_local_server(port=0)
            
            logger.info("Authenticated with new OAuth credentials")
            self._save_credentials(creds)
            return creds
            
        except ImportError:
            raise ImportError(
                "Google OAuth libraries not installed. "
                "Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
    
    def _save_credentials(self, creds):
        """Save credentials to file for reuse."""
        try:
            os.makedirs(self.CREDENTIALS_DIR, exist_ok=True)
            with open(self.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            logger.debug(f"Saved credentials to {self.TOKEN_FILE}")
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")
    
    def _initialize_credentials(self):
        """Initialize and validate OAuth credentials."""
        # Try loading existing token
        creds = self._load_credentials()
        
        if creds:
            # Validate and refresh if needed
            if not creds.valid:
                if not self._refresh_credentials(creds):
                    # Refresh failed, need new auth
                    creds = self._authenticate_new()
        else:
            # No credentials, run OAuth flow
            creds = self._authenticate_new()
        
        self._credentials = creds
    
    def get_service(self):
        """
        Get Google API service instance.
        
        Initializes credentials and builds service on first call.
        Subsequent calls return cached service.
        
        Returns:
            Google API service object
            
        Raises:
            ImportError: If required libraries not installed
            FileNotFoundError: If credentials.json not found
        """
        if self._initialized:
            return self._service
        
        try:
            from googleapiclient.discovery import build
            
            # Initialize credentials
            self._initialize_credentials()
            
            # Build service
            self._service = build(
                self.service_name,
                self.version,
                credentials=self._credentials
            )
            self._initialized = True
            
            logger.info(f"Initialized {self.service_name} API service")
            return self._service
            
        except ImportError as e:
            logger.error(f"Missing Google API library: {e}")
            raise ImportError(
                "Google API libraries not installed. "
                "Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
    
    def is_authenticated(self) -> bool:
        """Check if credentials are available and valid."""
        return self._credentials is not None and self._credentials.valid
