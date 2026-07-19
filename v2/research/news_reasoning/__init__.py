"""R03 provider-free news-reasoning research machinery.

This package contains contracts and deterministic algorithms only.  It has no
provider, transport, model-download, or implicit data-access capability.
"""

from .r03_contracts import PLAN_COMMIT, R03_IMPLEMENTATION_STATUS

__all__ = ["PLAN_COMMIT", "R03_IMPLEMENTATION_STATUS"]
