'''Python implementation of Operational Transform(OT) text type

Original:
https://github.com/ottypes/docs
https://github.com/ottypes/text/blob/master/lib/text.js
'''


OP_SKIP = 0
OP_DELETE = 1
OP_INSERT = 2


def _resolve_op(op):
    if isinstance(op, int):
        return (OP_SKIP, op)
    elif isinstance(op, dict):
        return (OP_DELETE, op.get('d', ''))
    elif isinstance(op, str):
        return (OP_INSERT, op)
    return (None, None)


def _make_op(op_type, op_arg):
    if op_type == OP_SKIP:
        return op_arg
    elif op_type == OP_DELETE:
        return {'d': op_arg}
    elif op_type == OP_INSERT:
        return op_arg
    return None


def check(ops):
    if not isinstance(ops, list):
        return False

    last_op_type = None
    op_type = None

    for op in ops:
        resolved_op = _resolve_op(op)
        if resolved_op is None:
            # unknown op
            return False

        op_type, op_arg = resolved_op

        if op_type == OP_SKIP:
            if not isinstance(op_arg, int) or op_arg <= 0:
                # print('no skip', op)
                return False
        elif op_type == OP_DELETE:
            if not isinstance(op_arg, str) or not op_arg:
                # print('wrong delete', op)
                return False
        elif op_type == OP_INSERT:
            if not isinstance(op_arg, str) or not op_arg:
                # print('wrong insert', op)
                return False

        if last_op_type == op_type:
            # un-optimized ops
            # print('dup op')
            return False

        last_op_type = op_type

    return True


def _make_iter_ops(ops):
    for op in ops:
        resolved_op = _resolve_op(op)
        if resolved_op is None:
            break
        yield resolved_op


def make_appender(ops):
    def appender(op):
        if op is None:
            return ops

        op_type, op_arg = _resolve_op(op)

        if ops:
            last_op_type, last_op_arg = _resolve_op(ops[-1])
        else:
            last_op_type, last_op_arg = None, None

        if op_arg == 0 or op_arg == '':
            return ops

        if last_op_type == op_type:
            merged_op_arg = last_op_arg + op_arg
            ops[-1] = _make_op(op_type, merged_op_arg)
        else:
            ops.append(op)

        return ops

    return appender


def make_taker(ops):
    context = [0, 0]

    def inner_taker(n, indivisable=None):
        idx, offset = context

        if idx == len(ops):
            if n == -1:
                return None
            return n

        ret = None
        op_type, op_arg = _resolve_op(ops[idx])

        if op_type == OP_SKIP:
            if n == -1 or op_arg - offset <= n:
                ret = _make_op(OP_SKIP, op_arg - offset)
                idx += 1
                offset = 0
            else:
                ret = _make_op(OP_SKIP, n)
                offset += n

        elif op_type == OP_DELETE:
            if n == -1 or indivisable == OP_DELETE or len(op_arg) - offset <= n:
                ret = _make_op(OP_DELETE, op_arg[offset:])
                offset = 0
                idx += 1
            else:
                ret = _make_op(OP_DELETE, op_arg[offset:offset + n])
                offset += n

        elif op_type == OP_INSERT:
            if n == -1 or indivisable == OP_INSERT or len(op_arg) - offset <= n:
                ret = _make_op(OP_INSERT, op_arg[offset:])
                offset = 0
                idx += 1
            else:
                ret = _make_op(OP_INSERT, op_arg[offset:offset + n])
                offset += n

        context[0] = idx
        context[1] = offset
        return ret

    def inner_peeker():
        idx, _ = context
        if 0 <= idx < len(ops):
            return ops[idx]
        else:
            return None

    return inner_taker, inner_peeker


def trim(normalized_ops):
    '''Trim ops in place

    Discrade trailing OP_SKIPs in ops.
    `normalized_ops` must be normalized.
    '''
    if normalized_ops and _resolve_op(normalized_ops[-1])[0] == OP_SKIP:
        normalized_ops.pop()
    return normalized_ops


def normalize(ops):
    '''Normalize ops

    Merge consecutive operations and trim the result.
    '''
    new_ops = []
    appender = make_appender(new_ops)

    for op in ops:
        appender(op)

    return trim(new_ops)


def apply(doc, ops):
    '''Apply ops to doc
    '''

    if not isinstance(doc, str):
        raise ValueError('doc must be string')

    if not check(ops):
        raise ValueError('invalid ops')

    new_doc = []

    for op_type, op_arg in _make_iter_ops(ops):
        if op_type == OP_SKIP:
            if op_arg > len(doc):
                raise ValueError('the op is too long')

            new_doc.append(doc[:op_arg])
            doc = doc[op_arg:]

        elif op_type == OP_DELETE:
            if doc[:len(op_arg)] != op_arg:
                # race condition : deleting text was changed by others
                raise ValueError('inconsistent delete', doc[:len(op_arg)], op_arg)

            doc = doc[len(op_arg):]

        elif op_type == OP_INSERT:
            new_doc.append(op_arg)

    new_doc.append(doc)

    return ''.join(new_doc)


def inverse_apply(doc, ops):
    '''Inversely apply ops to doc
    '''

    if not isinstance(doc, str):
        raise ValueError('doc must be string')

    if not check(ops):
        raise ValueError('invalid ops')

    last_pos = 0

    for op_type, op_arg in _make_iter_ops(ops):
        if op_type == OP_SKIP:
            last_pos += op_arg

        elif op_type == OP_DELETE:
            pass

        elif op_type == OP_INSERT:
            last_pos += len(op_arg)

    old_doc = [doc[last_pos:]]
    doc = doc[:last_pos]

    for op_type, op_arg in _make_iter_ops(reversed(ops)):
        if op_type == OP_SKIP:
            old_doc.append(doc[-op_arg:])
            doc = doc[:-op_arg]

        elif op_type == OP_DELETE:
            old_doc.append(op_arg)

        elif op_type == OP_INSERT:
            if doc[-len(op_arg):] != op_arg:
                raise ValueError('inconsistent state', doc[-len(op_arg):], op_arg)

            doc = doc[:-len(op_arg)]

    old_doc.append(doc)

    return ''.join(reversed(old_doc))
