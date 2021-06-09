"""
Public data structures for this app.

See OEP-49 for details
"""
class CertificatesDisplayBehaviors(str, Enum):
    END = "end"
    END_WITH_DATE = "end_with_date"
    EARLY_NO_INFO = "early_no_info"
