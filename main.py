import logging
import sys

from ai_client import generate_meta
from config import settings
from docs_client import create_doc
from scraper import collect_affiliate_pages
from serp_client import get_serp_results
from sheets_client import read_rows, write_result_link

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def process_row(row_index: int, keyword: str, geo: str, language: str) -> str:
    log.info("Processing: keyword=%r geo=%s language=%s", keyword, geo, language)

    serp_results = get_serp_results(keyword=keyword, geo=geo)
    log.info("SERP: found %d affiliate candidates", len(serp_results))

    if not serp_results:
        raise RuntimeError(f"No affiliate results found in TOP-{settings.serp_top_n} for {keyword!r} / {geo}")

    successful, failed = collect_affiliate_pages(serp_results, target=settings.target_affiliate_count)
    log.info("Scraped: %d successful, %d failed", len(successful), len(failed))

    if not successful:
        raise RuntimeError(f"All scraped pages failed for {keyword!r} / {geo}")

    meta = generate_meta(keyword=keyword, language=language, pages=successful)
    log.info("Generated meta — title: %r", meta.meta_title)

    doc_url = create_doc(
        keyword=keyword,
        geo=geo,
        successful=successful,
        failed=failed,
        meta=meta,
    )
    log.info("Doc created: %s", doc_url)

    write_result_link(row_index=row_index, doc_url=doc_url)
    log.info("Result written to sheet row %d", row_index)

    return doc_url


def main() -> None:
    rows = read_rows()
    if not rows:
        log.warning("No rows found in the sheet")
        sys.exit(0)

    errors: list[str] = []
    for row in rows:
        if row.result:
            log.info("Row %d already processed, skipping", row.row_index)
            continue
        try:
            doc_url = process_row(
                row_index=row.row_index,
                keyword=row.keyword,
                geo=row.geo,
                language=row.language,
            )
            print(f"Row {row.row_index} [{row.keyword} / {row.geo}] → {doc_url}")
        except Exception as exc:
            msg = f"Row {row.row_index} [{row.keyword} / {row.geo}] FAILED: {exc}"
            log.error(msg)
            errors.append(msg)

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
