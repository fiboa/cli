def repair_cp1257(value):
    """Repair Baltic text whose CP1257 bytes were decoded as Latin-1 (`Þieminiai` -> `Žieminiai`).

    Text that is already correct cannot be encoded as Latin-1 (š, ž, ė lie outside it) and is
    returned unchanged, as is plain ASCII and anything that is not a string.
    """
    if not isinstance(value, str):
        return value
    try:
        return value.encode("latin-1").decode("cp1257")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
