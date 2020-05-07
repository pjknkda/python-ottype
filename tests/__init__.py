from typing import List

import pytest

from . import utils

FUZZY_TEST_COUNT = 1_000
FUZZY_TEST_INIT_DOC_LENGTH = 100
FUZZY_TEST_OTS_LENGTH = 20


def test__resolve_ot() -> None:
    from ottype.core import OTSkip, OTInsert, OTDelete
    from ottype.core import _resolve_ot

    assert _resolve_ot(3) == OTSkip(3)
    assert _resolve_ot(-3) is None

    assert _resolve_ot('asdf') == OTInsert('asdf')
    assert _resolve_ot('') is None

    assert _resolve_ot({'d': 'asdf'}) == OTDelete('asdf')
    assert _resolve_ot({'d': ''}) is None
    assert _resolve_ot({'d': 4}) is None

    assert _resolve_ot(3.141592) is None  # type: ignore


def test__make_iter_ots() -> None:
    from ottype.core import OTSkip, OTInsert, OTDelete
    from ottype.core import _make_iter_ots

    assert list(_make_iter_ots([3, 'asdf', {'d': 'qwer'}])) == \
        [OTSkip(3), OTInsert('asdf'), OTDelete('qwer')]

    assert list(_make_iter_ots([3, 'asdf', -3, {'d': 'qwer'}])) == \
        [OTSkip(3), OTInsert('asdf')]


def test__Appender() -> None:
    from ottype.core import OTSkip, OTInsert, OTDelete, OTType
    from ottype.core import _Appender

    ots_1: List[OTType] = []
    appender_1 = _Appender(ots_1)

    appender_1.append(None)
    assert ots_1 == []

    appender_1.append(OTSkip(4))
    assert ots_1 == [OTSkip(4)]

    appender_1.append(OTSkip(3))
    assert ots_1 == [OTSkip(7)]

    appender_1.append(OTInsert('as'))
    assert ots_1 == [OTSkip(7), OTInsert('as')]

    appender_1.append(OTInsert('df'))
    assert ots_1 == [OTSkip(7), OTInsert('asdf')]

    appender_1.append(OTDelete('qw'))
    assert ots_1 == [OTSkip(7), OTInsert('asdf'), OTDelete('qw')]

    appender_1.append(OTDelete('er'))
    assert ots_1 == [OTSkip(7), OTInsert('asdf'), OTDelete('qwer')]


def test__Taker() -> None:
    from ottype.core import OTSkip, OTInsert, OTDelete, OTType
    from ottype.core import _Taker

    ots_1: List[OTType] = [OTSkip(3), OTSkip(4)]
    taker_1 = _Taker(ots_1)
    assert taker_1.take(1) == OTSkip(1)
    assert taker_1.take(4) == OTSkip(2)
    assert taker_1.take(-1) == OTSkip(4)
    assert taker_1.take(-1) is None
    assert taker_1.take(5) == OTSkip(5)

    ots_2: List[OTType] = [OTInsert('asdf'), OTInsert('qwer'), OTInsert('zxcv')]
    taker_2 = _Taker(ots_2)
    assert taker_2.take(1) == OTInsert('a')
    assert taker_2.take(1) == OTInsert('s')
    assert taker_2.take(5) == OTInsert('df')
    assert taker_2.take(1) == OTInsert('q')
    assert taker_2.take(1, 'd') == OTInsert('w')
    assert taker_2.take(1, 'i') == OTInsert('er')
    assert taker_2.take(-1) == OTInsert('zxcv')

    ots_3: List[OTType] = [OTDelete('asdf'), OTDelete('qwer'), OTDelete('zxcv')]
    taker_3 = _Taker(ots_3)
    assert taker_3.take(1) == OTDelete('a')
    assert taker_3.take(1) == OTDelete('s')
    assert taker_3.take(5) == OTDelete('df')
    assert taker_3.take(1) == OTDelete('q')
    assert taker_3.take(1, 'i') == OTDelete('w')
    assert taker_3.take(1, 'd') == OTDelete('er')
    assert taker_3.take(-1) == OTDelete('zxcv')

    ots_4: List[OTType] = [OTSkip(3), OTSkip(4)]
    taker_4 = _Taker(ots_4)
    assert taker_4.peak() == OTSkip(3)
    taker_4.take(1)
    assert taker_4.peak() == OTSkip(3)
    taker_4.take(5)
    assert taker_4.peak() == OTSkip(4)
    taker_4.take(3)
    assert taker_4.peak() == OTSkip(4)
    taker_4.take(1)
    assert taker_4.peak() is None


def test__trim() -> None:
    from ottype.core import OTSkip, OTInsert, OTType
    from ottype.core import _trim

    ots_1: List[OTType] = []
    _trim(ots_1)
    assert ots_1 == []

    ots_2: List[OTType] = [OTSkip(4)]
    _trim(ots_2)
    assert ots_2 == []

    ots_3: List[OTType] = [OTInsert('asdf'), OTSkip(4)]
    _trim(ots_3)
    assert ots_3 == [OTInsert('asdf')]

    ots_4: List[OTType] = [OTSkip(4), OTInsert('asdf')]
    _trim(ots_4)
    assert ots_4 == [OTSkip(4), OTInsert('asdf')]


def test_check() -> None:
    from ottype.core import check

    assert check([3, 'asdf', {'d': 'qwer'}])
    assert not check([3, object()])  # type: ignore
    assert not check([3, 4])
    assert not check(4)  # type: ignore


def test_apply() -> None:
    from ottype.core import apply

    with pytest.raises(ValueError):
        apply(None, [])  # type: ignore

    with pytest.raises(ValueError):
        apply('', [3, 4])

    assert apply('aaaaa', [2, 'bb', {'d': 'a'}, 1, 'c']) == 'aabbaca'

    with pytest.raises(ValueError):
        apply('aa', [3])

    with pytest.raises(ValueError):
        apply('aa', [{'d': 'b'}])

    # fuzzy test to catch unexpected exception
    for _ in range(FUZZY_TEST_COUNT):
        doc = utils.make_random_doc(FUZZY_TEST_INIT_DOC_LENGTH)
        random_ot_raw_list = utils.make_random_ots(doc, FUZZY_TEST_OTS_LENGTH)

        apply(doc, random_ot_raw_list)


def test_inverse_apply() -> None:
    from ottype.core import inverse_apply, apply

    with pytest.raises(ValueError):
        inverse_apply(None, [])  # type: ignore

    with pytest.raises(ValueError):
        inverse_apply('', [3, 4])

    with pytest.raises(ValueError):
        inverse_apply('aa', [3])

    with pytest.raises(ValueError):
        inverse_apply('aa', ['b'])

    for _ in range(FUZZY_TEST_COUNT):
        doc = utils.make_random_doc(FUZZY_TEST_INIT_DOC_LENGTH)
        random_ot_raw_list = utils.make_random_ots(doc, FUZZY_TEST_OTS_LENGTH)

        new_doc = apply(doc, random_ot_raw_list)
        assert doc == inverse_apply(new_doc, random_ot_raw_list)


def test_normalize() -> None:
    from ottype.core import normalize

    assert normalize([
        3, 4,
        'as', 'df',
        {'d': 'qw'}, {'d': 'er'},
        5
    ]) == [7, 'asdf', {'d': 'qwer'}]


def test_transform() -> None:
    from ottype.core import apply, transform

    with pytest.raises(ValueError):
        transform([3, 4], [], 'left')

    with pytest.raises(ValueError):
        transform([], [3, 4], 'left')

    with pytest.raises(ValueError):
        transform([], [], 'good')  # type: ignore

    for _ in range(FUZZY_TEST_COUNT):
        doc = utils.make_random_doc(FUZZY_TEST_INIT_DOC_LENGTH)
        random_ot_raw_list_1 = utils.make_random_ots(doc, FUZZY_TEST_OTS_LENGTH)
        random_ot_raw_list_2 = utils.make_random_ots(doc, FUZZY_TEST_OTS_LENGTH)

        left_first_doc = apply(
            apply(doc, random_ot_raw_list_1),
            transform(random_ot_raw_list_2, random_ot_raw_list_1, 'left')
        )

        right_first_doc = apply(
            apply(doc, random_ot_raw_list_2),
            transform(random_ot_raw_list_1, random_ot_raw_list_2, 'right')
        )

        assert left_first_doc == right_first_doc


def test_compose() -> None:
    from ottype.core import apply, compose

    with pytest.raises(ValueError):
        compose([3, 4], [])

    with pytest.raises(ValueError):
        compose([], [3, 4])

    with pytest.raises(ValueError):
        compose(['asdf'], [{'d': 'qw'}])

    for _ in range(FUZZY_TEST_COUNT):
        doc_1 = utils.make_random_doc(FUZZY_TEST_INIT_DOC_LENGTH)
        random_ot_raw_list_1 = utils.make_random_ots(doc_1, FUZZY_TEST_OTS_LENGTH)

        doc_2 = apply(doc_1, random_ot_raw_list_1)
        random_ot_raw_list_2 = utils.make_random_ots(doc_2, FUZZY_TEST_OTS_LENGTH)

        doc_3 = apply(doc_2, random_ot_raw_list_2)

        doc_3_composed = apply(
            doc_1,
            compose(
                random_ot_raw_list_1,
                random_ot_raw_list_2
            )
        )

        assert doc_3 == doc_3_composed
