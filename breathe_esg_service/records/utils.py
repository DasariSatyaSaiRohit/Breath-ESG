from decimal import Decimal


def normalize_energy(value: str, unit: str) -> tuple:
    """Returns (Decimal, 'kWh'). Handles kWh, MWh, GWh."""
    unit = unit.strip().lower()
    val = Decimal(str(value).replace(',', ''))
    if unit in ('kwh', 'kw\u00b7h'):
        return (val, 'kWh')
    elif unit == 'mwh':
        return (val * 1000, 'kWh')
    elif unit == 'gwh':
        return (val * 1000000, 'kWh')
    raise ValueError(f"Unrecognized energy unit: {unit}")


def parse_flexible_date(date_str: str):
    """Tries multiple date formats, returns date object."""
    from datetime import datetime
    formats = [
        '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y',
        '%d-%m-%Y', '%d-%b-%y', '%d-%b-%Y',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: '{date_str}'")


def get_columns_from_records(records: list) -> list:
    """
    Union of raw_data keys across all records on the current page.
    Sorted alphabetically for stable column order across pages.
    Rows missing a key will render as '—' in the UI.
    No schema profiles or hardcoded lists — the keys in raw_data
    are the columns, exactly as they came from the source.
    """
    seen = set()
    for record in records:
        for key in (record.raw_data or {}).keys():
            seen.add(key)
    return sorted(seen)


def parse_prefixed_id(prefixed_id: str) -> tuple:
    """
    Parses 'utility_42' → ('utility', 42)
    Parses 'travel_7'   → ('travel', 7)
    Raises ValueError on bad format.
    """
    parts = prefixed_id.split('_', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid prefixed ID: '{prefixed_id}'")
    source_type, record_id = parts[0], parts[1]
    if source_type not in ('utility', 'travel'):
        raise ValueError(f"Unknown source type: '{source_type}'")
    try:
        return source_type, int(record_id)
    except ValueError:
        raise ValueError(f"Invalid record ID: '{record_id}'")


def get_record_by_prefixed_id(prefixed_id: str, tenant):
    """
    Fetches UtilityRecord or TravelRecord by prefixed ID.
    Always filters by tenant — never fetch cross-tenant.
    Returns (record, source_type) tuple.
    Raises Http404 if not found.
    """
    from django.http import Http404
    from .models import UtilityRecord, TravelRecord
    source_type, record_id = parse_prefixed_id(prefixed_id)
    model = {'utility': UtilityRecord, 'travel': TravelRecord}[source_type]
    try:
        return model.objects.get(id=record_id, tenant=tenant), source_type
    except model.DoesNotExist:
        raise Http404


def apply_flag_rules(record_data: dict, source_type: str,
                     travel_type: str = None):
    """
    Returns flag_reason string if a rule triggers, else None.
    Call after normalization, before saving the record.
    """
    normalized_value = record_data.get('normalized_value')

    if source_type == 'utility':
        if normalized_value and normalized_value > 1000000:
            return "Usage over 1,000,000 kWh — possible unit error"
        start = record_data.get('billing_period_start')
        end = record_data.get('billing_period_end')
        if start and end:
            days = (end - start).days
            if days > 45 or days < 20:
                return "Unusual billing period duration"

    if source_type == 'travel':
        if travel_type == 'air' and normalized_value is None:
            return "Distance not computed — airport pair needs lookup"
        if travel_type == 'hotel' and normalized_value and normalized_value > 30:
            return "Hotel stay over 30 nights — verify"
        if travel_type in ('car', 'rail') and normalized_value is None:
            return "Distance not provided by source"

    if normalized_value is not None and normalized_value <= 0:
        return "Zero or negative normalized value"

    return None


def write_audit_log(user, tenant, action, record,
                    source_type, old_value=None, new_value=None,
                    job=None, ip_address=None):
    """
    Writes one AuditLog entry.
    record is a UtilityRecord or TravelRecord instance (or None for bulk ops).
    source_type is 'utility' or 'travel' (or None for bulk ops).
    """
    from audit.models import AuditLog
    AuditLog.objects.create(
        tenant=tenant,
        user=user,
        action=action,
        record_source_type=source_type,
        record_id=record.id if record else None,
        job=job,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )


def get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0]
    return request.META.get('REMOTE_ADDR')
