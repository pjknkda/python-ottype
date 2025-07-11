import os
from typing import TYPE_CHECKING

from .core import apply as _apply_py
from .core import check as _check_py
from .core import compose as _compose_py
from .core import diff as _diff_py
from .core import inverse_apply as _inverse_apply_py
from .core import normalize as _normalize_py
from .core import transform as _transform_py

try:
    from setuptools_scm import get_version

    __version__ = get_version(root="..", relative_to=__file__)
except (LookupError, ModuleNotFoundError):
    try:
        from ._version import version

        __version__ = version
    except ModuleNotFoundError:
        raise RuntimeError("Cannot determine version")

NO_EXTENSIONS = bool(os.environ.get("OTTYPE_NO_EXTENSIONS"))


apply = _apply_py
check = _check_py
compose = _compose_py
diff = _diff_py
inverse_apply = _inverse_apply_py
normalize = _normalize_py
transform = _transform_py


try:
    if not TYPE_CHECKING and not NO_EXTENSIONS:
        from .core_boost import apply as _apply_c
        from .core_boost import check as _check_c
        from .core_boost import compose as _compose_c
        from .core_boost import inverse_apply as _inverse_apply_c
        from .core_boost import normalize as _normalize_c
        from .core_boost import transform as _transform_c

        apply = _apply_c
        check = _check_c
        compose = _compose_c
        diff = _diff_py  # does not support boost yet
        inverse_apply = _inverse_apply_c
        normalize = _normalize_c
        transform = _transform_c

except ImportError:
    pass
