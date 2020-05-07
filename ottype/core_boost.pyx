# cython: language_level=3

cdef class OTType:
    pass


cdef class OTSkip(OTType):
    cdef int arg

    def __init__(self, int arg):
        self.arg = arg

    @property
    def raw(self):
        return self.arg


cdef class OTInsert(OTType):
    cdef str arg

    def __init__(self, str arg):
        self.arg = arg

    @property
    def raw(self):
        return self.arg


cdef class OTDelete(OTType):
    cdef str arg

    def __init__(self, str arg):
        self.arg = arg

    @property
    def raw(self):
        return {'d': self.arg}


cdef OTType _resolve_ot(object ot_raw):
    if isinstance(ot_raw, int):
        if ot_raw <= 0:
            raise TypeError()
        return OTSkip(ot_raw)
    elif isinstance(ot_raw, str):
        if ot_raw == '':
            raise TypeError()
        return OTInsert(ot_raw)
    elif isinstance(ot_raw, dict):
        s = ot_raw.get('d', '')
        if not isinstance(s, str) or s == '':
            raise TypeError()
        return OTDelete(s)

    raise TypeError()


cdef list _make_iter_ots(list ot_raw_list):
    cdef list ots = []

    try:
        for ot_raw in ot_raw_list:
            resolved_ot = _resolve_ot(ot_raw)
            ots.append(resolved_ot)
    except TypeError:
        pass
    return ots


cdef class _Appender:
    cdef list ots

    def __init__(self, list ots):
        self.ots = ots

    cdef void append(self, OTType ot):
        cdef OTType last_ot

        if ot is None:
            return
        
        if not self.ots:
            self.ots.append(ot)
            return

        last_ot = self.ots[-1]

        if isinstance(last_ot, OTSkip) and isinstance(ot, OTSkip):
            self.ots[-1] = OTSkip((<OTSkip>last_ot).arg + (<OTSkip>ot).arg)
        elif isinstance(last_ot, OTInsert) and isinstance(ot, OTInsert):
            self.ots[-1] = OTInsert((<OTInsert>last_ot).arg + (<OTInsert>ot).arg)
        elif isinstance(last_ot, OTDelete) and isinstance(ot, OTDelete):
            self.ots[-1] = OTDelete((<OTDelete>last_ot).arg + (<OTDelete>ot).arg)
        else:
            self.ots.append(ot)


cdef class _Taker:
    cdef:
        list ots
        int _idx
        int _offset
    
    def __init__(self, list ots):
        self.ots = ots

        self._idx = 0
        self._offset = 0

    cdef OTType take(self, int n, int indivisable = 0):
        # NOTE : indivisable (0 -> None, 1 -> Insert, 2 -> Delete)
        cdef:
            OTType ret_ot
            OTType ot
            OTSkip ot_skip
            OTInsert ot_insert
            OTDelete ot_delete

        if self._idx == len(self.ots):
            if n == -1:
                return None
            return OTSkip(n)

        ot = self.ots[self._idx]
        ret_ot = None

        if isinstance(ot, OTSkip):
            ot_skip = <OTSkip>ot

            if n == -1 or ot_skip.arg - self._offset <= n:
                ret_ot = OTSkip(ot_skip.arg - self._offset)
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = OTSkip(n)
                self._offset += n

        elif isinstance(ot, OTInsert):
            ot_insert = <OTInsert>ot

            if n == -1 or indivisable == 1 or len(ot_insert.arg) - self._offset <= n:
                ret_ot = OTInsert(ot_insert.arg[self._offset:])
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = OTInsert(ot_insert.arg[self._offset:self._offset + n])
                self._offset += n

        elif isinstance(ot, OTDelete):
            ot_delete = <OTDelete>ot

            if n == -1 or indivisable == 2 or len(ot_delete.arg) - self._offset <= n:
                ret_ot = OTDelete(ot_delete.arg[self._offset:])
                self._idx += 1
                self._offset = 0
            else:
                ret_ot = OTDelete(ot_delete.arg[self._offset:self._offset + n])
                self._offset += n

        return ret_ot

    cdef OTType peak(self):
        if 0 <= self._idx < len(self.ots):
            return self.ots[self._idx]
        return None


cdef void _trim(list ots):
    if ots and isinstance(ots[-1], OTSkip):
        ots.pop()


def check(object ot_raw_list):
    cdef OTType last_ot

    if not isinstance(ot_raw_list, list):
        return False

    last_ot = None
    for ot_raw in ot_raw_list:
        try:
            resolved_ot = _resolve_ot(ot_raw)
        except TypeError:
            return False

        if type(last_ot) is type(resolved_ot):
            return False

        last_ot = resolved_ot

    return True


def apply(str doc, object ot_raw_list):
    cdef:
        list new_doc
        int pos

        OTType ot
        OTSkip ot_skip
        OTInsert ot_insert
        OTDelete ot_delete

    if not isinstance(doc, str):
        raise ValueError('doc must be string')

    if not check(ot_raw_list):
        raise ValueError('invalid OTs')

    new_doc = []
    pos = 0

    for ot in _make_iter_ots(ot_raw_list):
        if isinstance(ot, OTSkip):
            ot_skip = <OTSkip>ot

            if ot_skip.arg > len(doc) - pos:
                raise ValueError('skip exceeds doc length')

            new_doc.append(doc[pos:pos + ot_skip.arg])
            pos += ot_skip.arg

        elif isinstance(ot, OTInsert):
            ot_insert = <OTInsert>ot

            new_doc.append(ot_insert.arg)

        elif isinstance(ot, OTDelete):
            ot_delete = <OTDelete>ot

            if doc[pos:pos + len(ot_delete.arg)] != ot_delete.arg:
                raise ValueError('inconsistent delete (doc, OT.arg)',
                                 doc[pos:pos + len(ot_delete.arg)],
                                 ot_delete.arg)
            pos += len(ot_delete.arg)

    new_doc.append(doc[pos:])

    return ''.join(new_doc)


def inverse_apply(str doc: str, object ot_raw_list):
    cdef:
        int last_pos
        list old_doc

        OTType ot
        OTSkip ot_skip
        OTInsert ot_insert
        OTDelete ot_delete

    if not isinstance(doc, str):
        raise ValueError('doc must be string')

    if not check(ot_raw_list):
        raise ValueError('invalid OTs')

    last_pos = 0
    for ot in _make_iter_ots(ot_raw_list):
        if isinstance(ot, OTSkip):
            last_pos += (<OTSkip>ot).arg

        elif isinstance(ot, OTInsert):
            last_pos += len((<OTInsert>ot).arg)

        elif isinstance(ot, OTDelete):
            pass

    if last_pos > len(doc):
        raise ValueError('skip exceeds doc length')

    old_doc = [doc[last_pos:]]

    for ot in reversed(_make_iter_ots(ot_raw_list)):
        if isinstance(ot, OTSkip):
            ot_skip = <OTSkip>ot

            old_doc.append(doc[last_pos - ot_skip.arg:last_pos])
            last_pos -= ot_skip.arg

        elif isinstance(ot, OTInsert):
            ot_insert = <OTInsert>ot

            if doc[last_pos - len(ot_insert.arg):last_pos] != ot_insert.arg:
                raise ValueError('inconsistent delete (doc, OT.arg)',
                                 doc[last_pos - len(ot_insert.arg):last_pos],
                                 ot_insert.arg)
            last_pos -= len(ot_insert.arg)

        elif isinstance(ot, OTDelete):
            ot_delete = <OTDelete>ot

            old_doc.append(ot_delete.arg)

    old_doc.append(doc[:last_pos])

    return ''.join(reversed(old_doc))


def normalize(object ot_raw_list):
    cdef:
        list new_ots
        list new_ot_raw_list

    new_ots = []
    appender = _Appender(new_ots)
    for ot in _make_iter_ots(ot_raw_list):
        appender.append(ot)

    _trim(new_ots)

    new_ot_raw_list = [None] * len(new_ots)    
    for i in range(len(new_ots)):
        new_ot_raw_list[i] = new_ots[i].raw

    return new_ot_raw_list


def transform(list ot_raw_list_1, list ot_raw_list_2, str side):
    cdef:
        list new_ots
        _Appender appender
        _Taker taker

        OTType ot
        int n
        OTType chunk_ot

        list new_ot_raw_list
        int i

    if not check(ot_raw_list_1) or not check(ot_raw_list_2):
        raise ValueError('invalid OTs')

    if side not in ['left', 'right']:
        raise ValueError('invalid side')

    new_ots = []
    appender = _Appender(new_ots)
    taker = _Taker(list(_make_iter_ots(ot_raw_list_1)))

    for ot in _make_iter_ots(ot_raw_list_2):
        if isinstance(ot, OTSkip):
            n = (<OTSkip>ot).arg

            while 0 < n:
                chunk_ot = taker.take(n, 1)
                appender.append(chunk_ot)

                if isinstance(chunk_ot, OTSkip):
                    n -= (<OTSkip>chunk_ot).arg
                elif isinstance(chunk_ot, OTInsert):
                    pass
                elif isinstance(chunk_ot, OTDelete):
                    n -= len((<OTDelete>chunk_ot).arg)

        elif isinstance(ot, OTInsert):
            if (side == 'left'
                    and isinstance(taker.peak(), OTInsert)):
                appender.append(taker.take(-1))

            appender.append(OTSkip(len((<OTInsert>ot).arg)))

        elif isinstance(ot, OTDelete):
            n = len((<OTDelete>ot).arg)

            while 0 < n:
                chunk_ot = taker.take(n, 1)

                if isinstance(chunk_ot, OTSkip):
                    n -= (<OTSkip>chunk_ot).arg
                elif isinstance(chunk_ot, OTInsert):
                    appender.append(chunk_ot)
                elif isinstance(chunk_ot, OTDelete):
                    n -= len((<OTDelete>chunk_ot).arg)

    while True:
        chunk_ot = taker.take(-1)
        if chunk_ot is None:
            break
        appender.append(chunk_ot)

    _trim(new_ots)

    new_ot_raw_list = [None] * len(new_ots)    
    for i in range(len(new_ots)):
        new_ot_raw_list[i] = new_ots[i].raw

    return new_ot_raw_list


def compose(list ot_raw_list_1, list ot_raw_list_2):
    cdef:
        list new_ots
        _Appender appender
        _Taker taker

        OTType ot
        OTDelete ot_delete
        int n
        OTType chunk_ot
        OTSkip chunk_ot_skip
        OTInsert chunk_ot_insert

        list new_ot_raw_list
        int i

    if not check(ot_raw_list_1) or not check(ot_raw_list_2):
        raise ValueError('invalid OTs')

    new_ots = []
    appender = _Appender(new_ots)
    taker = _Taker(list(_make_iter_ots(ot_raw_list_1)))

    for ot in _make_iter_ots(ot_raw_list_2):
        if isinstance(ot, OTSkip):
            n = (<OTSkip>ot).arg

            while 0 < n:
                chunk_ot = taker.take(n, 2)
                appender.append(chunk_ot)

                if isinstance(chunk_ot, OTSkip):
                    n -= (<OTSkip>chunk_ot).arg
                elif isinstance(chunk_ot, OTInsert):
                    n -= len((<OTInsert>chunk_ot).arg)
                elif isinstance(chunk_ot, OTDelete):
                    pass

        elif isinstance(ot, OTInsert):
            appender.append(ot)

        elif isinstance(ot, OTDelete):
            ot_delete = <OTDelete>ot

            offset = 0
            n = len((<OTDelete>ot).arg)

            while 0 < n:
                chunk_ot = taker.take(n, 2)

                if isinstance(chunk_ot, OTSkip):
                    chunk_ot_skip = <OTSkip>chunk_ot

                    appender.append(OTDelete(ot_delete.arg[offset:offset + chunk_ot_skip.arg]))
                    offset += chunk_ot_skip.arg
                    n -= chunk_ot_skip.arg

                elif isinstance(chunk_ot, OTInsert):
                    chunk_ot_insert = <OTSkip>chunk_ot

                    if chunk_ot_insert.arg != ot_delete.arg[offset:offset + len(chunk_ot_insert.arg)]:
                        raise ValueError('inconsistent delete in the seconds OTs (doc, OT.arg)',
                                         chunk_ot_insert.arg,
                                         ot_delete.arg[offset:offset + len(chunk_ot_insert.arg)])
                    offset += len(chunk_ot_insert.arg)
                    n -= len(chunk_ot_insert.arg)

                elif isinstance(chunk_ot, OTDelete):
                    appender.append(chunk_ot)

    while True:
        chunk_ot = taker.take(-1)
        if chunk_ot is None:
            break
        appender.append(chunk_ot)

    _trim(new_ots)

    new_ot_raw_list = [None] * len(new_ots)    
    for i in range(len(new_ots)):
        new_ot_raw_list[i] = new_ots[i].raw

    return new_ot_raw_list
