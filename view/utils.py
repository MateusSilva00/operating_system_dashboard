def kb_to_gb(kilobytes, decimals=2):
    """Convert kilobytes to gigabytes."""
    gb = kilobytes / (1024 * 1024)
    return round(gb, decimals)


def format_memory_size(kilobytes, decimals=2):
    if kilobytes >= 1024 * 1024:  # >= 1 GB
        gb = kilobytes / (1024 * 1024)
        return f"{gb:.{decimals}f} GB"
    elif kilobytes >= 1024:  # >= 1 MB
        mb = kilobytes / 1024
        return f"{mb:.{decimals}f} MB"
    else:  # < 1 MB
        return f"{kilobytes:,.0f} kB"


def format_memory_value_only(kilobytes, decimals=2):
    if kilobytes >= 1024 * 1024:  # >= 1 GB
        return round(kilobytes / (1024 * 1024), decimals)
    elif kilobytes >= 1024:  # >= 1 MB
        return round(kilobytes / 1024, decimals)
    else:  # < 1 MB
        return int(kilobytes)


def get_memory_unit(kilobytes):
    if kilobytes >= 1024 * 1024:  # >= 1 GB
        return "GB"
    elif kilobytes >= 1024:  # >= 1 MB
        return "MB"
    else:  # < 1 MB
        return "kB"
