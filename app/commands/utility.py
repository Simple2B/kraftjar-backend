import re
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from config import config, BASE_DIR

CFG = config()

ROOT_PATH = Path(BASE_DIR)
TOKEN_FILE = ROOT_PATH / "token.json"

SEARCH_IDS = re.compile(r"\((?P<id>\d+)\)")

ALL_UKRAINE = "вся україна"


# an internal function for authorization in Google Sheets
def authorized_user_in_google_spreadsheets() -> Credentials:
    credentials = None
    # auth process - > create token.json
    if Path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, CFG.SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", CFG.SCOPES)
            credentials = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(credentials.to_json())
    return credentials
