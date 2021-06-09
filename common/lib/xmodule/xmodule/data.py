"""
Public data structures for this app.

See OEP-49 for details
"""
class CertificatesDisplayBehaviors(str, Enum):
    END = "end"
    EARLY_NO_INFO = "early_no_info"
    EARLY_WITH_INFO = "early_with_info"
