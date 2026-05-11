from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import settings
from models import SheetRow

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def _get_service():
    creds = Credentials.from_service_account_file(settings.google_credentials_file, scopes=_SCOPES)
    return build("sheets", "v4", credentials=creds)


def read_rows() -> list[SheetRow]:
    service = _get_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=settings.google_sheets_id, range=settings.sheets_range)
        .execute()
    )
    raw_rows = result.get("values", [])
    rows: list[SheetRow] = []
    for i, row in enumerate(raw_rows, start=2):  # data starts at row 2
        if len(row) < 3:
            continue
        keyword = row[0].strip()
        geo = row[1].strip()
        language = row[2].strip()
        result_link = row[3].strip() if len(row) > 3 else ""
        if not keyword or not geo or not language:
            continue
        rows.append(
            SheetRow(
                row_index=i,
                keyword=keyword,
                geo=geo,
                language=language,
                result=result_link,
            )
        )
    return rows


def write_result_link(row_index: int, doc_url: str) -> None:
    service = _get_service()
    cell_range = f"Sheet1!D{row_index}"
    service.spreadsheets().values().update(
        spreadsheetId=settings.google_sheets_id,
        range=cell_range,
        valueInputOption="USER_ENTERED",
        body={"values": [[doc_url]]},
    ).execute()
