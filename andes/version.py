"""Package version information for ANDES."""

__version__ = "0.1.0"


def parse_version_info(version_str: str):
    """Parse a PEP-440-ish ``X.Y.Z[rcN]`` string into a tuple of components."""
    info = []
    for part in version_str.split("."):
        if part.isdigit():
            info.append(int(part))
        elif "rc" in part:
            major, rc = part.split("rc")
            info.append(int(major))
            info.append(f"rc{rc}")
    return tuple(info)


version_info = parse_version_info(__version__)
