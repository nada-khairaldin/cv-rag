from googleapiclient.discovery import build
from google.oauth2 import service_account

from . import config

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FILE_FIELDS = "id, name, mimeType, md5Checksum, modifiedTime, webViewLink"


def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        config.GOOGLE_APPLICATION_CREDENTIALS,
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=credentials)


def list_files(folder_id: str = config.DRIVE_FOLDER_ID) -> list[dict]:
    """Return all files (not in trash) inside a Google Drive folder."""
    service = get_drive_service()
    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields=f"nextPageToken, files({FILE_FIELDS})",
            orderBy="name",
            pageSize=100,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            return files


def download_file(file_id: str) -> bytes:
    """Return the content of a Google Drive file as bytes."""
    service = get_drive_service()
    return service.files().get_media(fileId=file_id, supportsAllDrives=True).execute()