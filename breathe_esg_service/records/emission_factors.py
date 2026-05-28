# records/emission_factors.py
#
# All factors are kg CO2e per unit.
# Source: DEFRA 2023 / GHG Protocol defaults.
#
# These are intentionally hardcoded constants — not stored in the database.
# Update this file (and redeploy) when factors change.

ELECTRICITY_FACTORS: dict[str, float] = {
    # country_code → kg CO2e per kWh
    'IN': 0.82,
    'US': 0.386,
    'GB': 0.207,
    'DE': 0.366,
    'DEFAULT': 0.5,
}

TRAVEL_AIR_FACTORS: dict[str, float] = {
    # cabin class → kg CO2e per km per passenger
    'economy':         0.255,
    'premium_economy': 0.359,
    'business':        0.428,
    'first':           0.597,
    'DEFAULT':         0.255,
}

TRAVEL_GROUND_FACTORS: dict[str, float] = {
    # vehicle type → kg CO2e per km
    'car':     0.192,
    'taxi':    0.211,
    'bus':     0.089,
    'DEFAULT': 0.192,
}

TRAVEL_RAIL_FACTORS: dict[str, float] = {
    'DEFAULT': 0.041,   # kg CO2e per km
}

TRAVEL_HOTEL_FACTORS: dict[str, float] = {
    'DEFAULT': 31.0,    # kg CO2e per room-night
}

SAP_MATERIAL_FACTORS: dict[str, float] = {
    # material category → kg CO2e per kg of material
    'diesel':      3.206,
    'petrol':      2.313,
    'natural_gas': 2.042,
    'coal':        2.419,
    'DEFAULT':     0.0,   # unknown materials: no emission assigned
}


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_electricity_factor(country_code: str) -> float:
    """Return kg CO2e per kWh for the given ISO country code."""
    return ELECTRICITY_FACTORS.get(country_code.upper(), ELECTRICITY_FACTORS['DEFAULT'])


def get_travel_factor(travel_type: str, sub_type: str = 'DEFAULT') -> float:
    """
    Return kg CO2e per unit for the given travel type and sub-type.
    travel_type: 'air' | 'hotel' | 'ground' | 'rail'
    sub_type:    cabin class (air), vehicle type (ground), or 'DEFAULT'
    """
    factor_tables: dict[str, dict[str, float]] = {
        'air':    TRAVEL_AIR_FACTORS,
        'hotel':  TRAVEL_HOTEL_FACTORS,
        'ground': TRAVEL_GROUND_FACTORS,
        'rail':   TRAVEL_RAIL_FACTORS,
    }
    table = factor_tables.get(travel_type, {})
    return table.get(sub_type.lower(), table.get('DEFAULT', 0.0))


def get_sap_factor(material_name: str) -> float:
    """Return kg CO2e per kg of material for the given material name."""
    key = material_name.strip().lower()
    return SAP_MATERIAL_FACTORS.get(key, SAP_MATERIAL_FACTORS['DEFAULT'])
