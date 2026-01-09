"""Actions package."""

# Keep package-level exports minimal and avoid importing submodules at package import time
# to prevent importing optional dependencies (like linux_parsers) during test collection.
__all__ = [
    "FSAction",
    "PSAction",
    "NETAction",
    "ENVAction",
    "SYSAction",
    "ServiceAction",
    "DeviceAction",
]
