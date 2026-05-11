from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import settings
from models import GeneratedMeta, ScrapedPage

_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


def _get_services():
    creds = Credentials.from_service_account_file(settings.google_credentials_file, scopes=_SCOPES)
    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return docs, drive


def _build_requests(
    keyword: str,
    geo: str,
    successful: list[ScrapedPage],
    failed: list[ScrapedPage],
    meta: GeneratedMeta,
) -> list[dict]:
    """Build Google Docs batchUpdate requests to populate the document."""
    requests = []
    cursor = 1  # insert index, advances as we add content

    def insert_text(text: str, index: int) -> dict:
        return {"insertText": {"location": {"index": index}, "text": text}}

    def style_paragraph(start: int, end: int, named_style: str) -> dict:
        return {
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end},
                "paragraphStyle": {"namedStyleType": named_style},
                "fields": "namedStyleType",
            }
        }

    # Title heading
    heading = f"Analysis for {keyword} - {geo}\n"
    requests.append(insert_text(heading, cursor))
    requests.append(style_paragraph(cursor, cursor + len(heading), "HEADING_1"))
    cursor += len(heading)

    # Competitor Reports section
    section_header = "Competitor Reports\n"
    requests.append(insert_text(section_header, cursor))
    requests.append(style_paragraph(cursor, cursor + len(section_header), "HEADING_2"))
    cursor += len(section_header)

    for page in successful:
        block = (
            f"Position #{page.position}: {page.url}\n"
            f"H1: {page.h1}\n"
            f"Meta Title: {page.meta_title}\n"
            f"Meta Description: {page.meta_description}\n"
        )
        if page.site_structure:
            block += "Site Structure:\n"
            for item in page.site_structure:
                block += f"  • {item}\n"
        block += "\n"
        requests.append(insert_text(block, cursor))
        cursor += len(block)

    if failed:
        failed_header = "Failed / Blocked Sites\n"
        requests.append(insert_text(failed_header, cursor))
        requests.append(style_paragraph(cursor, cursor + len(failed_header), "HEADING_3"))
        cursor += len(failed_header)
        for page in failed:
            line = f"Position #{page.position}: {page.url} — {page.error}\n"
            requests.append(insert_text(line, cursor))
            cursor += len(line)
        requests.append(insert_text("\n", cursor))
        cursor += 1

    # Optimized SEO Content section
    optimized_header = "Optimized SEO Content\n"
    requests.append(insert_text(optimized_header, cursor))
    requests.append(style_paragraph(cursor, cursor + len(optimized_header), "HEADING_2"))
    cursor += len(optimized_header)

    seo_block = f"H1: {meta.h1}\n" f"Meta Title: {meta.meta_title}\n" f"Meta Description: {meta.meta_description}\n"
    requests.append(insert_text(seo_block, cursor))

    return requests


def create_doc(
    keyword: str,
    geo: str,
    successful: list[ScrapedPage],
    failed: list[ScrapedPage],
    meta: GeneratedMeta,
) -> str:
    """Create a Google Doc, populate it, set Commenter access, return share URL."""
    docs_service, drive_service = _get_services()

    doc_title = f"{keyword}-{geo}"
    doc = docs_service.documents().create(body={"title": doc_title}).execute()
    doc_id = doc["documentId"]

    requests = _build_requests(keyword, geo, successful, failed, meta)
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests},
    ).execute()

    # Set "anyone with link" = commenter
    drive_service.permissions().create(
        fileId=doc_id,
        body={"type": "anyone", "role": "commenter"},
    ).execute()

    return f"https://docs.google.com/document/d/{doc_id}/edit"
