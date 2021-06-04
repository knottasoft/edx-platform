from enum import Enum

class CertificatesDisplayBehaviors(str, Enum):
    EARLY_NO_INFO = "early_no_info"
    END = "end"
    END_WITH_DATE = "end_with_date"

