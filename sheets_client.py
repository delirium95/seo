from config import settings
from google_auth import get_sheets_service
from models import SheetRow


def _get_service():
    return get_sheets_service()


def _get_first_sheet_name() -> str:
    service = _get_service()
    meta = service.spreadsheets().get(spreadsheetId=settings.google_sheets_id).execute()
    return meta["sheets"][0]["properties"]["title"]


def read_rows() -> list[SheetRow]:
    service = _get_service()
    sheet_name = _get_first_sheet_name()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=settings.google_sheets_id, range=f"{sheet_name}!A2:D")
        .execute()
    )
    raw_rows = result.get("values", [])
    rows: list[SheetRow] = []
    for i, row in enumerate(raw_rows, start=2):
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
    sheet_name = _get_first_sheet_name()
    cell_range = f"{sheet_name}!D{row_index}"
    service.spreadsheets().values().update(
        spreadsheetId=settings.google_sheets_id,
        range=cell_range,
        valueInputOption="USER_ENTERED",
        body={"values": [[doc_url]]},
    ).execute()
