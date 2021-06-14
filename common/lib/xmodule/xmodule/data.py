"""
Public data structures for this app.

See OEP-49 for details
"""
from enum import Enum, EnumMeta

class CertificatesDisplayBehaviors(str, Enum):
    END = "end"
    END_WITH_DATE = "end_with_date"
    EARLY_NO_INFO = "early_no_info"

    @classmethod
    def includes_value(cls, value):
        return value in set(item.value for item in cls)
