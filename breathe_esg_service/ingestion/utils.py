# Utility functions for ingestion are now in records/utils.py
# This module is retained as a thin re-export for any legacy references.
from records.utils import (
    normalize_energy,
    parse_flexible_date,
    apply_flag_rules,
    write_audit_log,
    get_ip,
)
