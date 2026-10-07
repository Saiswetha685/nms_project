import io
import csv
from typing import List, Dict, Any

def export_items_to_csv(headers: List[str], rows: List[List[Any]]) -> str:
    """Exports structured data into RFC 4180 CSV text"""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()
