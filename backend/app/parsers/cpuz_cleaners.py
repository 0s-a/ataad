import re
from typing import Optional

IGNORED_STRINGS = {
    "to be filled by o.e.m.",
    "to be filled by o.e.m",
    "default string",
    "system serial number",
    "none",
    "n/a",
    "not specified",
    "chassis serial number",
    "base board serial number",
}

def clean_text(val: Optional[str]) -> Optional[str]:
    """Trims whitespace and normalizes text."""
    if val is None:
        return None
    val = val.strip()
    return val if val else None

def clean_oem_string(val: Optional[str]) -> Optional[str]:
    """Cleans placeholder strings commonly injected by OEMs."""
    val = clean_text(val)
    if not val:
        return None
    if val.lower() in IGNORED_STRINGS:
        return None
    return val

def clean_uuid(val: Optional[str]) -> Optional[str]:
    """Normalizes UUID string by removing braces and lowercasing."""
    val = clean_oem_string(val)
    if not val:
        return None
    cleaned = val.replace("{", "").replace("}", "").strip().lower()
    return cleaned if len(cleaned) >= 32 else None

def extract_number(val: Optional[str]) -> Optional[float]:
    """Extracts the first floating point or integer number from a string."""
    if not val:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", val.replace(",", ""))
    if match:
        try:
            num = float(match.group(0))
            return int(num) if num.is_integer() else num
        except ValueError:
            return None
    return None

def clean_manufacturer(val: Optional[str]) -> Optional[str]:
    """Extracts clean manufacturer name, stripping hex vendor IDs in parentheses."""
    val = clean_oem_string(val)
    if not val:
        return None
    # e.g., "Samsung (CE00000000000000000000)" -> "Samsung"
    cleaned = re.sub(r"\s*\([0-9a-fA-F]+\)\s*", "", val).strip()
    return cleaned if cleaned else val

def normalize_chassis_type(val: Optional[str]) -> str:
    """Normalizes chassis type into standardized subtypes."""
    if not val:
        return "laptop"
    v = val.lower()
    if any(k in v for k in ["notebook", "laptop", "sub notebook"]):
        return "laptop"
    if any(k in v for k in ["desktop", "tower"]):
        return "desktop_tower"
    if any(k in v for k in ["low profile", "sff", "small form factor"]):
        return "sff"
    if any(k in v for k in ["server", "rack", "blade"]):
        return "server_rack"
    if any(k in v for k in ["mini pc", "mini", "nuc"]):
        return "mini_pc"
    return "other"

