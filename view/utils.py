def kb_to_gb(kilobytes, decimals=2):
    """Convert kilobytes to gigabytes."""
    gb = kilobytes / (1024 * 1024)
    return round(gb, decimals)
