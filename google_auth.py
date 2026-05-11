import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import settings

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]
_TOKEN_FILE = "token.json"


def get_credentials() -> Credentials:
    creds = None
    if os.path.exists(_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(_TOKEN_FILE, _SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(settings.google_credentials_file, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def get_sheets_service():
    return build("sheets", "v4", credentials=get_credentials())


def get_docs_service():
    return build("docs", "v1", credentials=get_credentials())


def get_drive_service():
    return build("drive", "v3", credentials=get_credentials())
