# cython: language_level=3, boundscheck=False
from cpython cimport *


cdef enum OTTypeAction:
    nop = 0, skip = 1, insert = 2, delete = 3

cpdef inline tuple[OTTypeAction, object]  _resolve_ot(object ot_raw):
    if isinstance(ot_raw, int):
        if <int>ot_raw <= 0:
            raise ValueError("invalid OT-Skip")
        return OTTypeAction.skip, ot_raw
    elif isinstance(ot_raw, str):
        if <str>ot_raw == "":
            raise ValueError("invalid OT-Insert")
        return OTTypeAction.insert, ot_raw
    elif isinstance(ot_raw, dict):
        s = ot_raw.get("d")
        if not isinstance(s, str) or <str>s == "":
            raise ValueError("invalid OT-Delete")
        return OTTypeAction.delete, s
    elif isinstance(ot_raw, tuple):
        if len(ot_raw) == 2:
            ot_action, ot_arg = ot_raw
            if ot_action == 1:
                assert isinstance(ot_arg, int)
                if <int>ot_arg <= 0:
                    raise ValueError("invalid OT-Skip")
                return ot_raw
            elif ot_action == 2:
                assert isinstance(ot_arg, str)
                if <str>ot_arg == "":
                    raise ValueError("invalid OT-Insert")
                return ot_raw
            elif ot_action == 3:
                assert isinstance(ot_arg, str)
                if <str>ot_arg == "":
                    raise ValueError("invalid OT-Delete")
                return ot_raw

    raise ValueError("unexpected OT structure")


def _to_ot_raw_list(list ots):
    cdef:
        Py_ssize_t ots_length, i
        OTTypeAction ot_action
        object ot_arg
        object ot_raw

    ots_length = PyList_Size(ots)
    ot_raw_list = PyList_New(ots_length)

    for i in range(ots_length):
        ot_action, ot_arg = <tuple>PyList_GET_ITEM(ots, i)
        if ot_action == OTTypeAction.skip:
            ot_raw = ot_arg
        elif ot_action == OTTypeAction.insert:
            ot_raw = ot_arg
        elif ot_action == OTTypeAction.delete:
            ot_raw = {"d": ot_arg}

        Py_INCREF(ot_raw)
        PyList_SET_ITEM(ot_raw_list, i, ot_raw)

    return ot_raw_list


cdef class _Appender:
    cdef list ots

    def __init__(self, list ots):
        self.ots = ots

    def append(self, tuple ot):
        cdef:
            OTTypeAction last_ot_action
            object last_ot_arg

            OTTypeAction ot_action
            object ot_arg

        if ot is None:
            return
        
        if not self.ots:
            self.ots.append(ot)
            return

        ot_action, ot_arg = ot
        last_ot_action, last_ot_arg = <tuple>self.ots[-1]

        if last_ot_action == OTTypeAction.skip and ot_action == OTTypeAction.skip:
            self.ots[-1] = (OTTypeAction.skip, <int>last_ot_arg + <int>ot_arg)
        elif last_ot_action == OTTypeAction.insert and ot_action == OTTypeAction.insert:
            self.ots[-1] = (OTTypeAction.insert, <str>last_ot_arg + <str>ot_arg)
        elif last_ot_action == OTTypeAction.delete and ot_action == OTTypeAction.delete:
            self.ots[-1] = (OTTypeAction.delete, <str>last_ot_arg + <str>ot_arg)
        else:
            self.ots.append(ot)


cdef class _Taker:
    cdef:
        object ot_raw_list
        int ot_raw_list_len
        int _idx
        int _offset
    
    def __init__(self, object ot_raw_list):
        self.ot_raw_list = ot_raw_list
        self.ot_raw_list_len = len(ot_raw_list)

        self._idx = 0
        self._offset = 0

    def take(self, int n, str indivisable = None):
        cdef:
            tuple ret_ot
            OTTypeAction ot_action
            object ot_arg
            int ot_arg_as_int
            str ot_arg_as_str

        if self._idx == self.ot_raw_list_len:
            if n == -1:
                return None
            return (OTTypeAction.skip, n)

        ot_action, ot_arg = _resolve_ot(self.ot_raw_list[self._idx])
        ret_ot = None

        if ot_action == OTTypeAction.skip:
            ot_arg_as_int = <int>ot_arg

            if n == -1 or ot_arg_as_int - self._offset <= n:
                ret_ot = (OTTypeAction.skip, ot_arg_as_int - self._offset)
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = (OTTypeAction.skip, n)
                self._offset += n

        elif ot_action == OTTypeAction.insert:
            ot_arg_as_str = <str>ot_arg

            if n == -1 or indivisable == "i" or len(ot_arg_as_str) - self._offset <= n:
                ret_ot = (OTTypeAction.insert, ot_arg_as_str[self._offset:])
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = (
                    OTTypeAction.insert, ot_arg_as_str[self._offset:self._offset + n]
                )
                self._offset += n

        elif ot_action == OTTypeAction.delete:
            ot_arg_as_str = <str>ot_arg

            if n == -1 or indivisable == "d" or len(ot_arg_as_str) - self._offset <= n:
                ret_ot = (OTTypeAction.delete, ot_arg_as_str[self._offset:])
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = (
                    OTTypeAction.delete, ot_arg_as_str[self._offset:self._offset + n]
                )
                self._offset += n

        return ret_ot

    def peak_action(self):
        if 0 <= self._idx < self.ot_raw_list_len:
            return _resolve_ot(self.ot_raw_list[self._idx])[0]
        return OTTypeAction.nop


def _trim(list ots not None):
    if ots and ots[-1][0] == OTTypeAction.skip:
        ots.pop()


def check(object ot_raw_list not None, *, bool check_unoptimized not None = True):
    cdef:
        OTTypeAction last_ot_action
        OTTypeAction ot_action

    if not isinstance(ot_raw_list, (list, tuple)):
        raise TypeError("`ot_raw_list` must be a list or tuple")

    last_ot_action = OTTypeAction.nop
    try:
        for ot_raw in ot_raw_list:
            ot_action = _resolve_ot(ot_raw)[0]

            if check_unoptimized and last_ot_action == ot_action:
                return False

            last_ot_action = ot_action

    except (ValueError, TypeError):
        return False

    if check_unoptimized and last_ot_action == OTTypeAction.skip:
        return False

    return True


def apply(
    str doc not None,
    object ot_raw_list not None,
    *,
    bool check_unoptimized not None = True,
):
    cdef:
        list new_doc
        int pos

        OTTypeAction ot_action
        object ot_arg
        int ot_arg_as_int
        str ot_arg_as_str

    if not isinstance(ot_raw_list, (list, tuple)):
        raise TypeError("`ot_raw_list` must be a list or tuple")

    if not check(ot_raw_list, check_unoptimized=check_unoptimized):
        raise ValueError("invalid OTs")

    new_doc = []
    pos = 0

    for ot_raw in ot_raw_list:
        ot_action, ot_arg = _resolve_ot(ot_raw)

        if ot_action == OTTypeAction.skip:
            ot_arg_as_int = <int>ot_arg

            if ot_arg_as_int > len(doc) - pos:
                raise ValueError("skip exceeds doc length")

            new_doc.append(doc[pos:pos + ot_arg_as_int])
            pos += ot_arg_as_int

        elif ot_action == OTTypeAction.insert:
            ot_arg_as_str = <str>ot_arg

            new_doc.append(ot_arg_as_str)

        elif ot_action == OTTypeAction.delete:
            ot_arg_as_str = <str>ot_arg

            if doc[pos:pos + len(ot_arg_as_str)] != ot_arg_as_str:
                raise ValueError(
                    "inconsistent delete (doc, OT.arg)",
                    doc[pos:pos + len(ot_arg_as_str)],
                    ot_arg_as_str,
                )
            pos += len(ot_arg_as_str)

    new_doc.append(doc[pos:])

    return "".join(new_doc)


def inverse_apply(
    str doc not None,
    object ot_raw_list not None,
    *,
    bool check_unoptimized not None = True,
):
    cdef:
        list ot_list

        int last_pos
        list old_doc

        OTTypeAction ot_action
        object ot_arg
        int ot_arg_as_int
        str ot_arg_as_str

    if not isinstance(ot_raw_list, (list, tuple)):
        raise TypeError("`ot_raw_list` must be a list or tuple")

    if not check(ot_raw_list, check_unoptimized=check_unoptimized):
        raise ValueError("invalid OTs")

    last_pos = 0

    for ot_raw in ot_raw_list:
        ot_action, ot_arg = _resolve_ot(ot_raw)

        if ot_action == OTTypeAction.skip:
            last_pos += <int>ot_arg

        elif ot_action == OTTypeAction.insert:
            last_pos += len(<str>ot_arg)

        elif ot_action == OTTypeAction.delete:
            pass

    if last_pos > len(doc):
        raise ValueError("skip exceeds doc length")

    old_doc = [doc[last_pos:]]

    for ot_raw in reversed(ot_raw_list):
        ot_action, ot_arg = _resolve_ot(ot_raw)

        if ot_action == OTTypeAction.skip:
            ot_arg_as_int = <int>ot_arg

            old_doc.append(doc[last_pos - ot_arg_as_int:last_pos])
            last_pos -= ot_arg_as_int

        elif ot_action == OTTypeAction.insert:
            ot_arg_as_str = <str>ot_arg

            if doc[last_pos - len(ot_arg_as_str):last_pos] != ot_arg_as_str:
                raise ValueError(
                    "inconsistent delete (doc, OT.arg)",
                    doc[last_pos - len(ot_arg_as_str):last_pos],
                    ot_arg_as_str,
                )
            last_pos -= len(ot_arg_as_str)

        elif ot_action == OTTypeAction.delete:
            ot_arg_as_str = <str>ot_arg

            old_doc.append(ot_arg_as_str)

    old_doc.append(doc[:last_pos])

    return "".join(reversed(old_doc))


def normalize(object ot_raw_list not None):
    cdef:
        list new_ots

    if not isinstance(ot_raw_list, (list, tuple)):
        raise TypeError("`ot_raw_list` must be a list or tuple")

    if not check(ot_raw_list, check_unoptimized=False):
        raise ValueError("invalid OTs")

    new_ots = []
    appender = _Appender(new_ots)
    for ot_raw in ot_raw_list:
        appender.append(_resolve_ot(ot_raw))

    _trim(new_ots)

    return _to_ot_raw_list(new_ots)


def transform(
    object ot_raw_list_1 not None,
    object ot_raw_list_2 not None,
    str side not None,
):
    cdef:
        list new_ots
        _Appender appender
        _Taker taker

        OTTypeAction ot_action
        object ot_arg
        int n

        tuple chunk_ot
        OTTypeAction chunk_ot_action
        object chunk_ot_arg

    if not isinstance(ot_raw_list_1, (list, tuple)):
        raise TypeError("`ot_raw_list_1` must be a list or tuple")

    if not isinstance(ot_raw_list_2, (list, tuple)):
        raise TypeError("`ot_raw_list_2` must be a list or tuple")

    if not check(ot_raw_list_1) or not check(ot_raw_list_2):
        raise ValueError("invalid OTs")

    if side not in ["left", "right"]:
        raise ValueError("invalid side")

    new_ots = []
    appender = _Appender(new_ots)
    taker = _Taker(ot_raw_list_1)

    for ot_raw in ot_raw_list_2:
        ot_action, ot_arg = _resolve_ot(ot_raw)

        if ot_action == OTTypeAction.skip:
            n = <int>ot_arg

            while 0 < n:
                chunk_ot = taker.take(n, "i")
                appender.append(chunk_ot)

                if chunk_ot is None:
                    break

                chunk_ot_action, chunk_ot_arg = chunk_ot

                if chunk_ot_action == OTTypeAction.skip:
                    n -= <int>chunk_ot_arg
                elif chunk_ot_action == OTTypeAction.insert:
                    pass
                elif chunk_ot_action == OTTypeAction.delete:
                    n -= len(<str>chunk_ot_arg)

        elif ot_action == OTTypeAction.insert:
            n = len(<str>ot_arg)

            if (
                side == "left"
                and taker.peak_action() == OTTypeAction.insert
            ):
                appender.append(taker.take(-1))

            appender.append((OTTypeAction.skip, n))

        elif ot_action == OTTypeAction.delete:
            n = len(<str>ot_arg)

            while 0 < n:
                chunk_ot = taker.take(n, "i")
                chunk_ot_action, chunk_ot_arg = chunk_ot

                if chunk_ot_action == OTTypeAction.skip:
                    n -= <int>chunk_ot_arg
                elif chunk_ot_action == OTTypeAction.insert:
                    appender.append(chunk_ot)
                elif chunk_ot_action == OTTypeAction.delete:
                    n -= len(<str>chunk_ot_arg)

    while True:
        chunk_ot = taker.take(-1)
        if chunk_ot is None:
            break
        appender.append(chunk_ot)

    _trim(new_ots)

    return _to_ot_raw_list(new_ots)


def compose(object ot_raw_list_1 not None, object ot_raw_list_2 not None):
    cdef:
        list new_ots
        _Appender appender
        _Taker taker

        tuple ot
        OTTypeAction ot_action
        object ot_arg
        str ot_arg_as_str

        int n
        int offset

        tuple chunk_ot
        OTTypeAction chunk_ot_action
        object chunk_ot_arg
        int chunk_ot_arg_as_int
        str chunk_ot_arg_as_str

    if not isinstance(ot_raw_list_1, (list, tuple)):
        raise TypeError("`ot_raw_list_1` must be a list or tuple")

    if not isinstance(ot_raw_list_2, (list, tuple)):
        raise TypeError("`ot_raw_list_2` must be a list or tuple")

    if not check(ot_raw_list_1) or not check(ot_raw_list_2):
        raise ValueError("invalid OTs")

    new_ots = []
    appender = _Appender(new_ots)
    taker = _Taker(ot_raw_list_1)

    for ot_raw in ot_raw_list_2:
        ot_action, ot_arg = ot = _resolve_ot(ot_raw)

        if ot_action == OTTypeAction.skip:
            n = <int>ot_arg

            while 0 < n:
                chunk_ot = taker.take(n, "d")
                appender.append(chunk_ot)

                chunk_ot_action, chunk_ot_arg = chunk_ot

                if chunk_ot_action == OTTypeAction.skip:
                    n -= <int>chunk_ot_arg
                elif chunk_ot_action == OTTypeAction.insert:
                    n -= len(<str>chunk_ot_arg)
                elif chunk_ot_action == OTTypeAction.delete:
                    pass

        elif ot_action == OTTypeAction.insert:
            appender.append(ot)

        elif ot_action == OTTypeAction.delete:
            ot_arg_as_str = <str>ot_arg

            offset = 0
            n = len(ot_arg)

            while 0 < n:
                chunk_ot = taker.take(n, "d")
                chunk_ot_action, chunk_ot_arg = chunk_ot

                if chunk_ot_action == OTTypeAction.skip:
                    chunk_ot_arg_as_int = <int>chunk_ot_arg

                    appender.append(
                        (
                            OTTypeAction.delete,
                            ot_arg_as_str[offset:offset + chunk_ot_arg_as_int],
                        )
                    )
                    offset += chunk_ot_arg_as_int
                    n -= chunk_ot_arg_as_int

                elif chunk_ot_action == OTTypeAction.insert:
                    chunk_ot_arg_as_str = <str>chunk_ot_arg

                    if chunk_ot_arg_as_str != ot_arg_as_str[
                        offset:offset + len(chunk_ot_arg_as_str)
                    ]:
                        raise ValueError(
                            "inconsistent delete in the seconds OTs (doc, OT.arg)",
                            chunk_ot_arg_as_str,
                            ot_arg_as_str[offset:offset + len(chunk_ot_arg_as_str)],
                        )
                    offset += len(chunk_ot_arg_as_str)
                    n -= len(chunk_ot_arg_as_str)

                elif chunk_ot_action == OTTypeAction.delete:
                    appender.append(chunk_ot)

    while True:
        chunk_ot = taker.take(-1)
        if chunk_ot is None:
            break
        appender.append(chunk_ot)

    _trim(new_ots)

    return _to_ot_raw_list(new_ots)
