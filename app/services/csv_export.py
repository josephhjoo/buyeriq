import csv
import io
from datetime import datetime


def buyers_to_csv(search: dict) -> bytes:
    """Export a buyer list to CSV bytes."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Rank", "Firm", "Type", "Contact Name", "Contact Title",
        "Confidence", "Confidence Reasoning", "Rationale", "Sources"
    ])

    for i, b in enumerate(search.get("buyers", [])):
        writer.writerow([
            i + 1,
            b.get("firm_name", ""),
            (b.get("buyer_type") or "").title(),
            b.get("contact_name") or "Not found",
            b.get("contact_title") or "",
            b.get("confidence", ""),
            b.get("confidence_reasoning", ""),
            b.get("rationale", ""),
            " | ".join(b.get("source_urls", [])),
        ])

    writer.writerow([])
    writer.writerow(["--- Target ---"])
    writer.writerow(["Company", search.get("target_name", "")])
    writer.writerow(["Industry", search.get("industry", "")])
    writer.writerow(["Revenue ($M)", search.get("revenue_m", "")])
    writer.writerow(["Geography", search.get("geography", "")])
    writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M")])

    return output.getvalue().encode("utf-8")
