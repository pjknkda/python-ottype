from __future__ import annotations

from typing import Dict, List, Literal, NewType, Tuple, Union

_OTTypeAction = NewType('_OTTypeAction', int)

_OTType = Tuple[_OTTypeAction, Union[int, str]]

_OTRawType = Union[int, str, Dict[str, str]]


def check(ot_raw_list: List[_OTRawType], *, check_unoptimized: bool = True) -> bool:
    ...


def apply(doc: str, ot_raw_list: List[_OTRawType], *, check_unoptimized: bool = True) -> str:
    ...


def inverse_apply(doc: str, ot_raw_list: List[_OTRawType], *, check_unoptimized: bool = True) -> str:
    ...


def normalize(ot_raw_list: List[_OTRawType]) -> List[_OTRawType]:
    ...


def transform(
    ot_raw_list_1: List[_OTRawType],
    ot_raw_list_2: List[_OTRawType],
    side: Literal['left', 'right'],
) -> List[_OTRawType]:
    ...


def compose(ot_raw_list_1: List[_OTRawType], ot_raw_list_2: List[_OTRawType]) -> List[_OTRawType]:
    ...
