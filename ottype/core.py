from __future__ import annotations

from typing import (TYPE_CHECKING, Iterable, Iterator, List, NamedTuple,
                    Optional, Union)

if TYPE_CHECKING:
    from typing_extensions import Literal


class OTSkip(NamedTuple):
    arg: int

    @property
    def raw(self) -> int:
        return self.arg


class OTInsert(NamedTuple):
    arg: str

    @property
    def raw(self) -> str:
        return self.arg


class OTDelete(NamedTuple):
    arg: str

    @property
    def raw(self) -> dict:
        return {'d': self.arg}


OTRawType = Union[int, str, dict]

OTType = Union[OTSkip, OTInsert, OTDelete]


def _resolve_ot(ot_raw: OTRawType) -> Optional[OTType]:
    if isinstance(ot_raw, int):
        if ot_raw <= 0:
            return None
        return OTSkip(ot_raw)
    elif isinstance(ot_raw, str):
        if ot_raw == '':
            return None
        return OTInsert(ot_raw)
    elif isinstance(ot_raw, dict):
        s = ot_raw.get('d', '')
        if not isinstance(s, str) or s == '':
            return None
        return OTDelete(s)

    return None


def _make_iter_ots(ot_raw_list: Iterable[OTRawType]) -> Iterator[OTType]:
    for ot_raw in ot_raw_list:
        resolved_ot = _resolve_ot(ot_raw)
        if resolved_ot is None:
            break
        yield resolved_ot


class _Appender:
    def __init__(self, ots: List[OTType]) -> None:
        self.ots = ots

    def append(self, ot: Optional[OTType]) -> None:
        if ot is None:
            return

        if not self.ots:
            self.ots.append(ot)
            return

        last_ot = self.ots[-1]

        if isinstance(last_ot, OTSkip) and isinstance(ot, OTSkip):
            self.ots[-1] = OTSkip(last_ot.arg + ot.arg)
        elif isinstance(last_ot, OTInsert) and isinstance(ot, OTInsert):
            self.ots[-1] = OTInsert(last_ot.arg + ot.arg)
        elif isinstance(last_ot, OTDelete) and isinstance(ot, OTDelete):
            self.ots[-1] = OTDelete(last_ot.arg + ot.arg)
        else:
            self.ots.append(ot)


class _Taker:
    def __init__(self, ots: List[OTType]) -> None:
        self.ots = ots

        self._idx = 0
        self._offset = 0

    def take(self,
             n: int,
             indivisable: Optional[Literal['d', 'i']] = None) -> Optional[OTType]:
        if self._idx == len(self.ots):
            if n == -1:
                return None
            return OTSkip(n)

        ot = self.ots[self._idx]
        ret_ot: Optional[OTType] = None

        if isinstance(ot, OTSkip):
            if n == -1 or ot.arg - self._offset <= n:
                ret_ot = OTSkip(ot.arg - self._offset)
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = OTSkip(n)
                self._offset += n

        elif isinstance(ot, OTInsert):
            if n == -1 or indivisable == 'i' or len(ot.arg) - self._offset <= n:
                ret_ot = OTInsert(ot.arg[self._offset:])
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = OTInsert(ot.arg[self._offset:self._offset + n])
                self._offset += n

        elif isinstance(ot, OTDelete):
            if n == -1 or indivisable == 'd' or len(ot.arg) - self._offset <= n:
                ret_ot = OTDelete(ot.arg[self._offset:])
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = OTDelete(ot.arg[self._offset:self._offset + n])
                self._offset += n

        return ret_ot

    def peak(self) -> Optional[OTType]:
        if 0 <= self._idx < len(self.ots):
            return self.ots[self._idx]
        return None


def _trim(ots: List[OTType]) -> None:
    '''Trim ops in place

    Discrade trailing OP_SKIPs in ops.
    `ots` must be normalized.
    '''
    if ots and isinstance(ots[-1], OTSkip):
        ots.pop()


def check(ot_raw_list: List[OTRawType]) -> bool:
    if not isinstance(ot_raw_list, list):
        return False

    last_ot = None
    for ot_raw in ot_raw_list:
        resolved_ot = _resolve_ot(ot_raw)
        if resolved_ot is None:
            # unknown op
            return False

        if type(last_ot) is type(resolved_ot):
            # un-optimized ops
            return False

        last_ot = resolved_ot

    return True


def apply(doc: str, ot_raw_list: List[OTRawType]) -> str:
    '''Apply ops to doc
    '''

    if not isinstance(doc, str):
        raise ValueError('doc must be string')

    if not check(ot_raw_list):
        raise ValueError('invalid OTs')

    new_doc = []
    pos = 0

    for ot in _make_iter_ots(ot_raw_list):
        if isinstance(ot, OTSkip):
            if ot.arg > len(doc) - pos:
                raise ValueError('skip exceeds doc length')

            new_doc.append(doc[pos:pos + ot.arg])
            pos += ot.arg

        elif isinstance(ot, OTInsert):
            new_doc.append(ot.arg)

        elif isinstance(ot, OTDelete):
            if doc[pos:pos + len(ot.arg)] != ot.arg:
                raise ValueError('inconsistent delete (doc, OT.arg)',
                                 doc[pos:pos + len(ot.arg)],
                                 ot.arg)
            pos += len(ot.arg)

    new_doc.append(doc[pos:])

    return ''.join(new_doc)


def inverse_apply(doc: str, ot_raw_list: List[OTRawType]) -> str:
    '''Inversely apply ops to doc
    '''

    if not isinstance(doc, str):
        raise ValueError('doc must be string')

    if not check(ot_raw_list):
        raise ValueError('invalid OTs')

    last_pos = 0
    for ot in _make_iter_ots(ot_raw_list):
        if isinstance(ot, OTSkip):
            last_pos += ot.arg

        elif isinstance(ot, OTInsert):
            last_pos += len(ot.arg)

        elif isinstance(ot, OTDelete):
            pass

    if last_pos > len(doc):
        raise ValueError('skip exceeds doc length')

    old_doc = [doc[last_pos:]]

    for ot in _make_iter_ots(reversed(ot_raw_list)):
        if isinstance(ot, OTSkip):
            old_doc.append(doc[last_pos - ot.arg:last_pos])
            last_pos -= ot.arg

        elif isinstance(ot, OTInsert):
            if doc[last_pos - len(ot.arg):last_pos] != ot.arg:
                raise ValueError('inconsistent delete (doc, OT.arg)',
                                 doc[last_pos - len(ot.arg):last_pos],
                                 ot.arg)
            last_pos -= len(ot.arg)

        elif isinstance(ot, OTDelete):
            old_doc.append(ot.arg)

    old_doc.append(doc[:last_pos])

    return ''.join(reversed(old_doc))


def normalize(ot_raw_list: List[OTRawType]) -> List[OTRawType]:
    '''Normalize ops

    Merge consecutive operations and trim the result.
    '''

    new_ots: List[OTType] = []
    appender = _Appender(new_ots)
    for ot in _make_iter_ots(ot_raw_list):
        appender.append(ot)

    _trim(new_ots)

    return [ot.raw for ot in new_ots]


def transform(ot_raw_list_1: List[OTRawType],
              ot_raw_list_2: List[OTRawType],
              side: Literal['left', 'right']) -> List[OTRawType]:
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
        apply(apply(doc, local_ops), transform(server_ops, local_ops, 'left'))
            == apply(apply(doc, server_ops), transform(local_ops, server_ops, 'right'))
    '''

    if not check(ot_raw_list_1) or not check(ot_raw_list_2):
        raise ValueError('invalid OTs')

    if side not in ['left', 'right']:
        raise ValueError('invalid side')

    new_ots: List[OTType] = []
    appender = _Appender(new_ots)
    taker = _Taker(list(_make_iter_ots(ot_raw_list_1)))

    for ot in _make_iter_ots(ot_raw_list_2):
        if isinstance(ot, OTSkip):
            n = ot.arg

            while 0 < n:
                chunk_ot = taker.take(n, 'i')
                appender.append(chunk_ot)

                if isinstance(chunk_ot, OTSkip):
                    n -= chunk_ot.arg
                elif isinstance(chunk_ot, OTInsert):
                    pass
                elif isinstance(chunk_ot, OTDelete):
                    n -= len(chunk_ot.arg)

        elif isinstance(ot, OTInsert):
            if (side == 'left'
                    and isinstance(taker.peak(), OTInsert)):
                appender.append(taker.take(-1))

            appender.append(OTSkip(len(ot.arg)))

        elif isinstance(ot, OTDelete):
            n = len(ot.arg)

            while 0 < n:
                chunk_ot = taker.take(n, 'i')

                if isinstance(chunk_ot, OTSkip):
                    n -= chunk_ot.arg
                elif isinstance(chunk_ot, OTInsert):
                    appender.append(chunk_ot)
                elif isinstance(chunk_ot, OTDelete):
                    n -= len(chunk_ot.arg)

    while True:
        chunk_ot = taker.take(-1)
        if chunk_ot is None:
            break
        appender.append(chunk_ot)

    _trim(new_ots)

    return [ot.raw for ot in new_ots]


def compose(ot_raw_list_1: List[OTRawType],
            ot_raw_list_2: List[OTRawType]) -> List[OTRawType]:
    '''Compose `ot_raw_list_1` and `ot_raw_list_2`

    The result of compose satisfies
    .. code::
        apply(apply(doc, ot_raw_list_1), ot_raw_list_2) == apply(doc, compose(ot_raw_list_1, ot_raw_list_2))
    '''

    if not check(ot_raw_list_1) or not check(ot_raw_list_2):
        raise ValueError('invalid OTs')

    new_ots: List[OTType] = []
    appender = _Appender(new_ots)
    taker = _Taker(list(_make_iter_ots(ot_raw_list_1)))

    for ot in _make_iter_ots(ot_raw_list_2):
        if isinstance(ot, OTSkip):
            n = ot.arg

            while 0 < n:
                chunk_ot = taker.take(n, 'd')
                appender.append(chunk_ot)

                if isinstance(chunk_ot, OTSkip):
                    n -= chunk_ot.arg
                elif isinstance(chunk_ot, OTInsert):
                    n -= len(chunk_ot.arg)
                elif isinstance(chunk_ot, OTDelete):
                    pass

        elif isinstance(ot, OTInsert):
            appender.append(ot)

        elif isinstance(ot, OTDelete):
            offset = 0
            n = len(ot.arg)

            while 0 < n:
                chunk_ot = taker.take(n, 'd')

                if isinstance(chunk_ot, OTSkip):
                    appender.append(OTDelete(ot.arg[offset:offset + chunk_ot.arg]))
                    offset += chunk_ot.arg
                    n -= chunk_ot.arg
                elif isinstance(chunk_ot, OTInsert):
                    if chunk_ot.arg != ot.arg[offset:offset + len(chunk_ot.arg)]:
                        raise ValueError('inconsistent delete in the seconds OTs (doc, OT.arg)',
                                         chunk_ot.arg,
                                         ot.arg[offset:offset + len(chunk_ot.arg)])
                    offset += len(chunk_ot.arg)
                    n -= len(chunk_ot.arg)
                elif isinstance(chunk_ot, OTDelete):
                    appender.append(chunk_ot)

    while True:
        chunk_ot = taker.take(-1)
        if chunk_ot is None:
            break
        appender.append(chunk_ot)

    _trim(new_ots)

    return [ot.raw for ot in new_ots]
