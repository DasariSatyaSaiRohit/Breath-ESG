"""
records/parsers/sap_csv.py

Parses raw SAP procurement CSV bytes into a list of normalised dicts.
Column headers are matched case-insensitively and remapped to canonical names.
Unknown columns are preserved verbatim so no source data is lost.
"""
import csv
import io
from typing import Dict, List

# Canonical mapping: lowercase stripped source header → canonical key name
SAP_COLUMN_MAP: Dict[str, str] = {
    'plant code':     'Plant_Code',
    'material':       'Material',
    'quantity':       'Quantity',
    'unit':           'Unit',
    'vendor':         'Vendor',
    'document date':  'Document_Date',
    'purchase order': 'Purchase_Order',
    'cost center':    'Cost_Center',
    'gl account':     'GL_Account',
    'company code':   'Company_Code',
}


def parse_sap_csv(file_bytes: bytes) -> List[Dict[str, str]]:
    """
    Accept raw CSV bytes (UTF-8 or UTF-8-BOM).
    Return a list of dicts with normalised key names.

    Raises ValueError if:
      - file is empty / has no data rows
      - no recognisable SAP columns are found in the header

    Unknown columns are preserved as-is (pass-through) so that raw_data
    always contains everything the source file had.
    """
    text = file_bytes.decode('utf-8-sig')   # strip BOM if present
    reader = csv.DictReader(io.StringIO(text))

    rows: List[Dict[str, str]] = []
    recognised_columns: set[str] = set()

    for row in reader:
        mapped: Dict[str, str] = {}
        for raw_key, value in row.items():
            if raw_key is None:
                continue
            normalised_key = raw_key.strip().lower()
            canonical = SAP_COLUMN_MAP.get(normalised_key)
            if canonical:
                recognised_columns.add(canonical)
                mapped[canonical] = (value or '').strip()
            else:
                # Preserve unknown columns under their original (stripped) name
                mapped[raw_key.strip()] = (value or '').strip()
        rows.append(mapped)

    if not rows:
        raise ValueError("SAP CSV is empty — no data rows found.")

    if not recognised_columns:
        raise ValueError(
            "SAP CSV does not contain any recognised columns. "
            f"Expected at least one of: {', '.join(SAP_COLUMN_MAP.values())}."
        )

    return rows
