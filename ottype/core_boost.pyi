from __future__ import annotations

from typing import Dict, List, Literal, NewType, Tuple, Union

_OTTypeAction = NewType('_OTTypeAction', int)

_OTType = Tuple[_OTTypeAction, Union[int, str]]

_OTRawInputType = Union[int, str, Dict[str, str], Tuple[int, Union[int, str]]]
_OTRawInputList = Union[List[_OTRawInputType], Tuple[_OTRawInputType]]

_OTRawOutputType = Union[int, str, Dict[str, str]]


def check(ot_raw_list: _OTRawInputList, *, check_unoptimized: bool = True) -> bool:
    ...


def apply(doc: str, ot_raw_list: _OTRawInputList, *, check_unoptimized: bool = True) -> str:
    ...


def inverse_apply(doc: str, ot_raw_list: _OTRawInputList, *, check_unoptimized: bool = True) -> str:
    ...


def normalize(ot_raw_list: _OTRawInputList) -> List[_OTRawOutputType]:
    ...


def transform(
    ot_raw_list_1: _OTRawInputList,
    ot_raw_list_2: _OTRawInputList,
    side: Literal['left', 'right'],
) -> List[_OTRawOutputType]:
    ...


def compose(ot_raw_list_1: _OTRawInputList, ot_raw_list_2: _OTRawInputList) -> List[_OTRawOutputType]:
    ...
