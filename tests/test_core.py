from __future__ import annotations

from typing import TYPE_CHECKING, List

import pytest

from ottype import core

from . import utils

FUZZ_TEST_COUNT = 1_000
FUZZ_TEST_INIT_DOC_LENGTH = 100
FUZZ_TEST_OTS_LENGTH = 20

CORE_IMPL = [core]
try:
    from ottype import core_boost
    CORE_IMPL.append(core_boost)
except ImportError:
    pass


@pytest.fixture(params=CORE_IMPL)
def core_impl(request):  # type:ignore
    return request.param


def OTSkip(arg: int) -> core._OTType:
    return (core._OTTypeActionSkip, arg)


def OTInsert(arg: str) -> core._OTType:
    return (core._OTTypeActionInsert, arg)


def OTDelete(arg: str) -> core._OTType:
    return (core._OTTypeActionDelete, arg)


def test__resolve_ot() -> None:
    from ottype.core import _resolve_ot

    assert _resolve_ot(3) == OTSkip(3)
    with pytest.raises(ValueError):
        _resolve_ot(-3)

    assert _resolve_ot('asdf') == OTInsert('asdf')
    with pytest.raises(ValueError):
        _resolve_ot('')

    assert _resolve_ot({'d': 'asdf'}) == OTDelete('asdf')

    with pytest.raises(ValueError):
        _resolve_ot({'d': ''})
    with pytest.raises(ValueError):
        _resolve_ot({'d': 4})

    with pytest.raises(ValueError):
        _resolve_ot(3.141592)  # type: ignore


def test__make_iter_ots() -> None:
    from ottype.core import _make_iter_ots

    assert list(_make_iter_ots([3, 'asdf', {'d': 'qwer'}])) == \
        [OTSkip(3), OTInsert('asdf'), OTDelete('qwer')]

    assert list(_make_iter_ots([3, 'asdf', -3, {'d': 'qwer'}])) == \
        [OTSkip(3), OTInsert('asdf')]


def test__Appender() -> None:
    from ottype.core import _Appender

    ots_1: List[core._OTType] = []
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
    from ottype.core import _Taker

    ots_1: List[core._OTType] = [OTSkip(3), OTSkip(4)]
    taker_1 = _Taker(ots_1)
    assert taker_1.take(1) == OTSkip(1)
    assert taker_1.take(4) == OTSkip(2)
    assert taker_1.take(-1) == OTSkip(4)
    assert taker_1.take(-1) is None
    assert taker_1.take(5) == OTSkip(5)

    ots_2: List[core._OTType] = [OTInsert('asdf'), OTInsert('qwer'), OTInsert('zxcv')]
    taker_2 = _Taker(ots_2)
    assert taker_2.take(1) == OTInsert('a')
    assert taker_2.take(1) == OTInsert('s')
    assert taker_2.take(5) == OTInsert('df')
    assert taker_2.take(1) == OTInsert('q')
    assert taker_2.take(1, 'd') == OTInsert('w')
    assert taker_2.take(1, 'i') == OTInsert('er')
    assert taker_2.take(-1) == OTInsert('zxcv')

    ots_3: List[core._OTType] = [OTDelete('asdf'), OTDelete('qwer'), OTDelete('zxcv')]
    taker_3 = _Taker(ots_3)
    assert taker_3.take(1) == OTDelete('a')
    assert taker_3.take(1) == OTDelete('s')
    assert taker_3.take(5) == OTDelete('df')
    assert taker_3.take(1) == OTDelete('q')
    assert taker_3.take(1, 'i') == OTDelete('w')
    assert taker_3.take(1, 'd') == OTDelete('er')
    assert taker_3.take(-1) == OTDelete('zxcv')

    ots_4: List[core._OTType] = [OTSkip(3), OTInsert('asdf')]
    taker_4 = _Taker(ots_4)
    assert taker_4.peak_action() == core._OTTypeActionSkip
    taker_4.take(1)
    assert taker_4.peak_action() == core._OTTypeActionSkip
    taker_4.take(5)
    assert taker_4.peak_action() == core._OTTypeActionInsert
    taker_4.take(3)
    assert taker_4.peak_action() == core._OTTypeActionInsert
    taker_4.take(1)
    assert taker_4.peak_action() == core._OTTypeActionNop


def test__trim() -> None:
    from ottype.core import _trim

    ots_1: List[core._OTType] = []
    _trim(ots_1)
    assert ots_1 == []

    ots_2: List[core._OTType] = [OTSkip(4)]
    _trim(ots_2)
    assert ots_2 == []

    ots_3: List[core._OTType] = [OTInsert('asdf'), OTSkip(4)]
    _trim(ots_3)
    assert ots_3 == [OTInsert('asdf')]

    ots_4: List[core._OTType] = [OTSkip(4), OTInsert('asdf')]
    _trim(ots_4)
    assert ots_4 == [OTSkip(4), OTInsert('asdf')]


def test_check(core_impl) -> None:  # type:ignore
    if TYPE_CHECKING:
        from ottype import core as core_impl

    check = core_impl.check

    with pytest.raises(TypeError):
        check(4)  # type: ignore

    assert check([3, 'asdf', {'d': 'qwer'}])
    assert not check([3, object()])  # type: ignore
    assert not check([3, 4])
    assert not check([3])


def test_apply(core_impl) -> None:  # type:ignore
    if TYPE_CHECKING:
        from ottype import core as core_impl

    apply = core_impl.apply

    with pytest.raises(TypeError):
        apply(None, [])  # type: ignore

    with pytest.raises(TypeError):
        apply('', 12345)  # type: ignore

    with pytest.raises(ValueError):
        apply('', [3, 4])

    assert apply('abcde', [2, 'qq', {'d': 'c'}, 1, 'w']) == 'abqqdwe'

    with pytest.raises(ValueError):
        apply('aa', [3, 'x'])

    with pytest.raises(ValueError):
        apply('aa', [{'d': 'b'}])


def test_apply_fuzz(core_impl) -> None:  # type:ignore
    if TYPE_CHECKING:
        from ottype import core as core_impl

    apply = core_impl.apply
    normalize = core_impl.normalize

    for _ in range(FUZZ_TEST_COUNT):
        doc = utils.make_random_doc(FUZZ_TEST_INIT_DOC_LENGTH)
        random_ot_raw_list = utils.make_random_ots(normalize, doc, FUZZ_TEST_OTS_LENGTH)

        apply(doc, random_ot_raw_list)


def test_inverse_apply(core_impl) -> None:  # type:ignore
    if TYPE_CHECKING:
        from ottype import core as core_impl

    inverse_apply = core_impl.inverse_apply

    with pytest.raises(TypeError):
        inverse_apply(None, [])  # type: ignore

    with pytest.raises(TypeError):
        inverse_apply('', 12345)  # type: ignore

    assert inverse_apply('abqqdwe', [2, 'qq', {'d': 'c'}, 1, 'w']) == 'abcde'

    with pytest.raises(ValueError):
        inverse_apply('', [3, 4])

    with pytest.raises(ValueError):
        inverse_apply('aa', [3, 'x'])

    with pytest.raises(ValueError):
        inverse_apply('aa', ['b'])


def test_inverse_apply_fuzz(core_impl) -> None:  # type:ignore
    if TYPE_CHECKING:
        from ottype import core as core_impl

    apply = core_impl.apply
    inverse_apply = core_impl.inverse_apply
    normalize = core_impl.normalize

    for _ in range(FUZZ_TEST_COUNT):
        doc = utils.make_random_doc(FUZZ_TEST_INIT_DOC_LENGTH)
        random_ot_raw_list = utils.make_random_ots(normalize, doc, FUZZ_TEST_OTS_LENGTH)

        new_doc = apply(doc, random_ot_raw_list)
        assert doc == inverse_apply(new_doc, random_ot_raw_list)


def test_normalize(core_impl) -> None:  # type:ignore
    if TYPE_CHECKING:
        from ottype import core as core_impl

    normalize = core_impl.normalize

    with pytest.raises(TypeError):
        normalize(12345)  # type:ignore

    with pytest.raises(ValueError):
        normalize([-123])

    assert normalize([
        3, 4,
        'as', 'df',
        {'d': 'qw'}, {'d': 'er'},
        5
    ]) == [7, 'asdf', {'d': 'qwer'}]


def test_transform_fuzz(core_impl) -> None:  # type:ignore
    if TYPE_CHECKING:
        from ottype import core as core_impl

    apply = core_impl.apply
    normalize = core_impl.normalize
    transform = core_impl.transform

    with pytest.raises(TypeError):
        transform(1234, [3], 'left')

    with pytest.raises(TypeError):
        transform([4], 1234, 'left')

    with pytest.raises(TypeError):
        transform([3], [4], None)

    with pytest.raises(ValueError):
        transform([3, 4], [], 'left')

    with pytest.raises(ValueError):
        transform([], [3, 4], 'left')

    with pytest.raises(ValueError):
        transform([], [], 'good')  # type: ignore

    for _ in range(FUZZ_TEST_COUNT):
        doc = utils.make_random_doc(FUZZ_TEST_INIT_DOC_LENGTH)
        random_ot_raw_list_1 = utils.make_random_ots(normalize, doc, FUZZ_TEST_OTS_LENGTH)
        random_ot_raw_list_2 = utils.make_random_ots(normalize, doc, FUZZ_TEST_OTS_LENGTH)

        left_first_doc = apply(
            apply(doc, random_ot_raw_list_1),
            transform(random_ot_raw_list_2, random_ot_raw_list_1, 'left')
        )

        right_first_doc = apply(
            apply(doc, random_ot_raw_list_2),
            transform(random_ot_raw_list_1, random_ot_raw_list_2, 'right')
        )

        assert left_first_doc == right_first_doc


def test_compose_fuzz(core_impl) -> None:  # type:ignore
    if TYPE_CHECKING:
        from ottype import core as core_impl

    apply = core_impl.apply
    compose = core_impl.compose
    normalize = core_impl.normalize

    with pytest.raises(TypeError):
        compose(1234, [4])

    with pytest.raises(TypeError):
        compose([3], 1234)

    with pytest.raises(ValueError):
        compose([3, 4], [])

    with pytest.raises(ValueError):
        compose([], [3, 4])

    with pytest.raises(ValueError):
        compose(['asdf'], [{'d': 'qw'}])

    for _ in range(FUZZ_TEST_COUNT):
        doc_1 = utils.make_random_doc(FUZZ_TEST_INIT_DOC_LENGTH)
        random_ot_raw_list_1 = utils.make_random_ots(normalize, doc_1, FUZZ_TEST_OTS_LENGTH)

        doc_2 = apply(doc_1, random_ot_raw_list_1)
        random_ot_raw_list_2 = utils.make_random_ots(normalize, doc_2, FUZZ_TEST_OTS_LENGTH)

        doc_3 = apply(doc_2, random_ot_raw_list_2)

        doc_3_composed = apply(
            doc_1,
            compose(
                random_ot_raw_list_1,
                random_ot_raw_list_2
            )
        )

        assert doc_3 == doc_3_composed
