from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, NewType, Optional, Tuple, Union

if TYPE_CHECKING:
    from typing_extensions import Literal


_OTTypeAction = NewType('_OTTypeAction', int)

_OTTypeActionNop = _OTTypeAction(0)
_OTTypeActionSkip = _OTTypeAction(1)
_OTTypeActionInsert = _OTTypeAction(2)
_OTTypeActionDelete = _OTTypeAction(3)

_OTType = Tuple[_OTTypeAction, Union[int, str]]

_OTRawInputType = Union[int, str, Dict[str, str], Tuple[int, Union[int, str]]]
_OTRawInputList = Union[List[_OTRawInputType], Tuple[_OTRawInputType]]

_OTRawOutputType = Union[int, str, Dict[str, str]]


def _resolve_ot(ot_raw: _OTRawInputType) -> _OTType:
    if isinstance(ot_raw, int):
        if ot_raw <= 0:
            raise ValueError('invalid OT-Skip')
        return (_OTTypeActionSkip, ot_raw)
    elif isinstance(ot_raw, str):
        if ot_raw == '':
            raise ValueError('invalid OT-Insert')
        return (_OTTypeActionInsert, ot_raw)
    elif isinstance(ot_raw, dict):
        s = ot_raw.get('d')
        if not isinstance(s, str) or s == '':
            raise ValueError('invalid OT-Delete')
        return (_OTTypeActionDelete, s)
    elif isinstance(ot_raw, tuple):
        if len(ot_raw) == 2:
            ot_action, ot_arg = ot_raw
            if ot_action == 1:
                assert isinstance(ot_arg, int)
                if ot_arg <= 0:
                    raise ValueError('invalid OT-Skip')
                return ot_raw  # type: ignore
            elif ot_action == 2:
                assert isinstance(ot_arg, str)
                if ot_arg == '':
                    raise ValueError('invalid OT-Insert')
                return ot_raw  # type: ignore
            elif ot_action == 3:
                assert isinstance(ot_arg, str)
                if ot_arg == '':
                    raise ValueError('invalid OT-Delete')
                return ot_raw  # type: ignore

    raise ValueError('unexpected OT structure')


def _to_ot_raw_list(ots: List[_OTType]) -> List[_OTRawOutputType]:
    ot_raw_list = []
    for ot_action, ot_arg in ots:
        ot_raw: _OTRawOutputType

        if ot_action == _OTTypeActionSkip:
            assert isinstance(ot_arg, int)
            ot_raw = ot_arg

        elif ot_action == _OTTypeActionInsert:
            assert isinstance(ot_arg, str)
            ot_raw = ot_arg

        elif ot_action == _OTTypeActionDelete:
            assert isinstance(ot_arg, str)
            ot_raw = {'d': ot_arg}

        else:
            raise ValueError('unexpected OT')

        ot_raw_list.append(ot_raw)

    return ot_raw_list


class _Appender:
    def __init__(self, ots: List[_OTType]) -> None:
        self.ots = ots

    def append(self, ot: Optional[_OTType]) -> None:
        if ot is None:
            return

        if not self.ots:
            self.ots.append(ot)
            return

        last_ot_action, last_ot_arg = self.ots[-1]
        ot_action, ot_arg = ot

        if last_ot_action == _OTTypeActionSkip and ot_action == _OTTypeActionSkip:
            assert isinstance(last_ot_arg, int)
            assert isinstance(ot_arg, int)
            self.ots[-1] = (_OTTypeActionSkip, last_ot_arg + ot_arg)
        elif last_ot_action == _OTTypeActionInsert and ot_action == _OTTypeActionInsert:
            assert isinstance(last_ot_arg, str)
            assert isinstance(ot_arg, str)
            self.ots[-1] = (_OTTypeActionInsert, last_ot_arg + ot_arg)
        elif last_ot_action == _OTTypeActionDelete and ot_action == _OTTypeActionDelete:
            assert isinstance(last_ot_arg, str)
            assert isinstance(ot_arg, str)
            self.ots[-1] = (_OTTypeActionDelete, last_ot_arg + ot_arg)
        else:
            self.ots.append(ot)


class _Taker:
    def __init__(self, ot_raw_list: _OTRawInputList) -> None:
        self.ot_raw_list = ot_raw_list

        self._idx = 0
        self._offset = 0

    def take(self, n: int, indivisable: Optional[Literal['d', 'i']] = None) -> Optional[_OTType]:
        if self._idx == len(self.ot_raw_list):
            if n == -1:
                return None
            return (_OTTypeActionSkip, n)

        ot_action, ot_arg = _resolve_ot(self.ot_raw_list[self._idx])
        ret_ot: Optional[_OTType] = None

        if ot_action == _OTTypeActionSkip:
            assert isinstance(ot_arg, int)
            if n == -1 or ot_arg - self._offset <= n:
                ret_ot = (_OTTypeActionSkip, ot_arg - self._offset)
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = (_OTTypeActionSkip, n)
                self._offset += n

        elif ot_action == _OTTypeActionInsert:
            assert isinstance(ot_arg, str)
            if n == -1 or indivisable == 'i' or len(ot_arg) - self._offset <= n:
                ret_ot = (_OTTypeActionInsert, ot_arg[self._offset:])
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = (_OTTypeActionInsert, ot_arg[self._offset:self._offset + n])
                self._offset += n

        elif ot_action == _OTTypeActionDelete:
            assert isinstance(ot_arg, str)
            if n == -1 or indivisable == 'd' or len(ot_arg) - self._offset <= n:
                ret_ot = (_OTTypeActionDelete, ot_arg[self._offset:])
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = (_OTTypeActionDelete, ot_arg[self._offset:self._offset + n])
                self._offset += n

        return ret_ot

    def peak_action(self) -> _OTTypeAction:
        if 0 <= self._idx < len(self.ot_raw_list):
            return _resolve_ot(self.ot_raw_list[self._idx])[0]
        return _OTTypeActionNop


def _trim(ots: List[_OTType]) -> None:
    '''Trim ots in place

    Discrade trailing OP_SKIPs in ots.
    `ots` must be normalized.
    '''
    if ots and ots[-1][0] == _OTTypeActionSkip:
        ots.pop()


def check(ot_raw_list: _OTRawInputList, *, check_unoptimized: bool = True) -> bool:
    if not isinstance(ot_raw_list, (list, tuple)):
        raise TypeError('`ot_raw_list` must be a list or tuple')

    last_ot_action = _OTTypeActionNop
    try:
        for ot_raw in ot_raw_list:
            ot_action = _resolve_ot(ot_raw)[0]

            if check_unoptimized and last_ot_action == ot_action:
                # un-optimized ots
                return False

            last_ot_action = ot_action

    except (ValueError, TypeError):
        return False

    if check_unoptimized and last_ot_action == _OTTypeActionSkip:
        return False

    return True


def apply(
    doc: str,
    ot_raw_list: _OTRawInputList,
    *,
    check_unoptimized: bool = True,
) -> str:
    '''Apply ots to doc
    '''

    if not isinstance(doc, str):
        raise TypeError('`doc` must be string')

    if not isinstance(ot_raw_list, (list, tuple)):
        raise TypeError('`ot_raw_list` must be a list or tuple')

    if not check(ot_raw_list, check_unoptimized=check_unoptimized):
        raise ValueError('invalid OTs')

    new_doc = []
    pos = 0

    for ot_raw in ot_raw_list:
        ot_action, ot_arg = _resolve_ot(ot_raw)

        if ot_action == _OTTypeActionSkip:
            assert isinstance(ot_arg, int)

            if ot_arg > len(doc) - pos:
                raise ValueError('skip exceeds doc length')

            new_doc.append(doc[pos:pos + ot_arg])
            pos += ot_arg

        elif ot_action == _OTTypeActionInsert:
            assert isinstance(ot_arg, str)

            new_doc.append(ot_arg)

        elif ot_action == _OTTypeActionDelete:
            assert isinstance(ot_arg, str)

            if doc[pos:pos + len(ot_arg)] != ot_arg:
                raise ValueError('inconsistent delete (doc, OT.arg)', doc[pos:pos + len(ot_arg)], ot_arg)
            pos += len(ot_arg)

    new_doc.append(doc[pos:])

    return ''.join(new_doc)


def inverse_apply(
    doc: str,
    ot_raw_list: _OTRawInputList,
    *,
    check_unoptimized: bool = True,
) -> str:
    '''Inversely apply ots to doc
    '''

    if not isinstance(doc, str):
        raise TypeError('`doc` must be string')

    if not isinstance(ot_raw_list, (list, tuple)):
        raise TypeError('`ot_raw_list` must be a list or tuple')

    if not check(ot_raw_list, check_unoptimized=check_unoptimized):
        raise ValueError('invalid OTs')

    last_pos = 0
    for ot_raw in ot_raw_list:
        ot_action, ot_arg = _resolve_ot(ot_raw)

        if ot_action == _OTTypeActionSkip:
            assert isinstance(ot_arg, int)
            last_pos += ot_arg

        elif ot_action == _OTTypeActionInsert:
            assert isinstance(ot_arg, str)
            last_pos += len(ot_arg)

        elif ot_action == _OTTypeActionDelete:
            pass

    if last_pos > len(doc):
        raise ValueError('skip exceeds doc length')

    old_doc = [doc[last_pos:]]

    for ot_raw in reversed(ot_raw_list):
        ot_action, ot_arg = _resolve_ot(ot_raw)

        if ot_action == _OTTypeActionSkip:
            assert isinstance(ot_arg, int)

            old_doc.append(doc[last_pos - ot_arg:last_pos])
            last_pos -= ot_arg

        elif ot_action == _OTTypeActionInsert:
            assert isinstance(ot_arg, str)

            if doc[last_pos - len(ot_arg):last_pos] != ot_arg:
                raise ValueError('inconsistent delete (doc, OT.arg)', doc[last_pos - len(ot_arg):last_pos], ot_arg)
            last_pos -= len(ot_arg)

        elif ot_action == _OTTypeActionDelete:
            assert isinstance(ot_arg, str)

            old_doc.append(ot_arg)

    old_doc.append(doc[:last_pos])

    return ''.join(reversed(old_doc))


def normalize(ot_raw_list: _OTRawInputList) -> List[_OTRawOutputType]:
    '''Normalize ots

    Merge consecutive operations and trim the result.
    '''

    if not isinstance(ot_raw_list, (list, tuple)):
        raise TypeError('`ot_raw_list` must be a list or tuple')

    if not check(ot_raw_list, check_unoptimized=False):
        raise ValueError('invalid OTs')

    new_ots: List[_OTType] = []
    appender = _Appender(new_ots)
    for ot_raw in ot_raw_list:
        appender.append(_resolve_ot(ot_raw))

    _trim(new_ots)

    return _to_ot_raw_list(new_ots)


def transform(
    ot_raw_list_1: _OTRawInputList,
    ot_raw_list_2: _OTRawInputList,
    side: Literal['left', 'right'],
) -> List[_OTRawOutputType]:
    '''Transform `ot_raw_list_1` by `ot_raw_list_2`

    Transform `ot_raw_list_1` to have same meaning when `ot_raw_list_2` is applied
    to the doc before `ot_raw_list_1`.

    `side` is required to break ties, for example, if we assume
    `ot_raw_list_1 = ['a']` and `ot_raw_list_2 = ['b']`, the result can be either
    'ab' or 'ba' depending on the side.

    - `transform(['a'], ['b'], 'left') = [1, "a"]` (left <- right)
    - `transform(['a'], ['b'], 'right') = ["a"]` (left -> right)

    The result of transform satisfies that,
    .. code::
        apply(apply(doc, local_ots), transform(server_ots, local_ots, 'left'))
            == apply(apply(doc, server_ots), transform(local_ots, server_ots, 'right'))
    '''

    if not isinstance(ot_raw_list_1, (list, tuple)):
        raise TypeError('`ot_raw_list_1` must be a list or tuple')

    if not isinstance(ot_raw_list_2, (list, tuple)):
        raise TypeError('`ot_raw_list_2` must be a list or tuple')

    if not isinstance(side, str):
        raise TypeError('`side` must be str')

    if not check(ot_raw_list_1) or not check(ot_raw_list_2):
        raise ValueError('invalid OTs')

    if side not in ['left', 'right']:
        raise ValueError('invalid side')

    new_ots: List[_OTType] = []
    appender = _Appender(new_ots)
    taker = _Taker(ot_raw_list_1)

    for ot_raw in ot_raw_list_2:
        ot_action, ot_arg = _resolve_ot(ot_raw)

        if ot_action == _OTTypeActionSkip:
            assert isinstance(ot_arg, int)

            n = ot_arg
            while 0 < n:
                chunk_ot = taker.take(n, 'i')
                appender.append(chunk_ot)

                if chunk_ot is None:
                    break  # pragma: no cover

                chunk_ot_action, chunk_ot_arg = chunk_ot

                if chunk_ot_action == _OTTypeActionSkip:
                    assert isinstance(chunk_ot_arg, int)
                    n -= chunk_ot_arg
                elif chunk_ot_action == _OTTypeActionInsert:
                    pass
                elif chunk_ot_action == _OTTypeActionDelete:
                    assert isinstance(chunk_ot_arg, str)
                    n -= len(chunk_ot_arg)

        elif ot_action == _OTTypeActionInsert:
            assert isinstance(ot_arg, str)

            n = len(ot_arg)

            if (
                side == 'left'
                and taker.peak_action() == _OTTypeActionInsert
            ):
                appender.append(taker.take(-1))

            appender.append((_OTTypeActionSkip, n))

        elif ot_action == _OTTypeActionDelete:
            assert isinstance(ot_arg, str)

            n = len(ot_arg)
            while 0 < n:
                chunk_ot = taker.take(n, 'i')

                if chunk_ot is None:
                    break  # pragma: no cover

                chunk_ot_action, chunk_ot_arg = chunk_ot

                if chunk_ot_action == _OTTypeActionSkip:
                    assert isinstance(chunk_ot_arg, int)
                    n -= chunk_ot_arg
                elif chunk_ot_action == _OTTypeActionInsert:
                    appender.append(chunk_ot)
                elif chunk_ot_action == _OTTypeActionDelete:
                    assert isinstance(chunk_ot_arg, str)
                    n -= len(chunk_ot_arg)

    while True:
        chunk_ot = taker.take(-1)
        if chunk_ot is None:
            break
        appender.append(chunk_ot)

    _trim(new_ots)

    return _to_ot_raw_list(new_ots)


def compose(
    ot_raw_list_1: _OTRawInputList,
    ot_raw_list_2: _OTRawInputList,
) -> List[_OTRawOutputType]:
    '''Compose `ot_raw_list_1` and `ot_raw_list_2`

    The result of compose satisfies
    .. code::
        apply(apply(doc, ot_raw_list_1), ot_raw_list_2) == apply(doc, compose(ot_raw_list_1, ot_raw_list_2))
    '''

    if not isinstance(ot_raw_list_1, (list, tuple)):
        raise TypeError('`ot_raw_list_1` must be a list or tuple')

    if not isinstance(ot_raw_list_2, (list, tuple)):
        raise TypeError('`ot_raw_list_2` must be a list or tuple')

    if not check(ot_raw_list_1) or not check(ot_raw_list_2):
        raise ValueError('invalid OTs')

    new_ots: List[_OTType] = []
    appender = _Appender(new_ots)
    taker = _Taker(ot_raw_list_1)

    for ot_raw in ot_raw_list_2:
        ot_action, ot_arg = ot = _resolve_ot(ot_raw)

        if ot_action == _OTTypeActionSkip:
            assert isinstance(ot_arg, int)

            n = ot_arg
            while 0 < n:
                chunk_ot = taker.take(n, 'd')
                appender.append(chunk_ot)

                if chunk_ot is None:
                    break  # pragma: no cover

                chunk_ot_action, chunk_ot_arg = chunk_ot

                if chunk_ot_action == _OTTypeActionSkip:
                    assert isinstance(chunk_ot_arg, int)
                    n -= chunk_ot_arg
                elif chunk_ot_action == _OTTypeActionInsert:
                    assert isinstance(chunk_ot_arg, str)
                    n -= len(chunk_ot_arg)
                elif chunk_ot_action == _OTTypeActionDelete:
                    pass

        elif ot_action == _OTTypeActionInsert:
            appender.append(ot)

        elif ot_action == _OTTypeActionDelete:
            assert isinstance(ot_arg, str)

            offset = 0
            n = len(ot_arg)

            while 0 < n:
                chunk_ot = taker.take(n, 'd')

                if chunk_ot is None:
                    break  # pragma: no cover

                chunk_ot_action, chunk_ot_arg = chunk_ot

                if chunk_ot_action == _OTTypeActionSkip:
                    assert isinstance(chunk_ot_arg, int)

                    appender.append((_OTTypeActionDelete, ot_arg[offset:offset + chunk_ot_arg]))
                    offset += chunk_ot_arg
                    n -= chunk_ot_arg

                elif chunk_ot_action == _OTTypeActionInsert:
                    assert isinstance(chunk_ot_arg, str)

                    if chunk_ot_arg != ot_arg[offset:offset + len(chunk_ot_arg)]:
                        raise ValueError(
                            'inconsistent delete in the seconds OTs (doc, OT.arg)',
                            chunk_ot_arg,
                            ot_arg[offset:offset + len(chunk_ot_arg)],
                        )
                    offset += len(chunk_ot_arg)
                    n -= len(chunk_ot_arg)

                elif chunk_ot_action == _OTTypeActionDelete:
                    appender.append(chunk_ot)

    while True:
        chunk_ot = taker.take(-1)
        if chunk_ot is None:
            break
        appender.append(chunk_ot)

    _trim(new_ots)

    return _to_ot_raw_list(new_ots)
