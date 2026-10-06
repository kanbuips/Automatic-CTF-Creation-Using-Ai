"""Shared constants for the pipeline stages."""
import re

PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|TBC|XXX|FIXME)\b|\?\?+", re.IGNORECASE)

VALID_DIRECTIONS = {"X", "Y", "Z", "XY", "XZ", "YZ", "XYZ"}
DIRECTION_CODES = {"X": 1, "Y": 2, "Z": 3, "XY": 4, "XZ": 5, "YZ": 6, "XYZ": 7}

KNOWN_UNITS = {"mm", "deg", "degree", "degrees", "um", "in"}

SEVERITIES = ("critical", "error", "warning", "info")
