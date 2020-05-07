import os

from .core import apply as _apply_py
from .core import check as _check_py
from .core import compose as _compose_py
from .core import inverse_apply as _inverse_apply_py
from .core import normalize as _normalize_py
from .core import transform as _transform_py

__version__ = '20.5.0'

NO_EXTENSIONS = bool(os.environ.get('OTTYPE_NO_EXTENSIONS'))


apply = _apply_py
check = _check_py
compose = _compose_py
inverse_apply = _inverse_apply_py
normalize = _normalize_py
transform = _transform_py

try:
    if not NO_EXTENSIONS:
        from .core_boost import apply as _apply_c
        from .core_boost import check as _check_c
        from .core_boost import compose as _compose_c
        from .core_boost import inverse_apply as _inverse_apply_c
        from .core_boost import normalize as _normalize_c
        from .core_boost import transform as _transform_c

        apply = _apply_c
        check = _check_c
        compose = _compose_c
        inverse_apply = _inverse_apply_c
        normalize = _normalize_c
        transform = _transform_c

except ImportError:  # pragma: no cover
    pass
