import random
import time
from typing import TYPE_CHECKING, Any, List

from ottype import core
from tests import utils

NUM_ITERATION = 100_000

CORE_IMPL: List[Any] = [('python', core)]

try:
    from ottype import core_boost
    CORE_IMPL.append(('cython', core_boost))
except ImportError:
    pass

try:
    from extra import old_ottype
    CORE_IMPL.insert(0, ('baseline', old_ottype))
except ImportError:
    pass

random.seed(457700)


def benchmark_apply() -> None:
    print('Target: apply')

    prev_record = dict()

    for core_imple_name, core_impl in CORE_IMPL:
        print(f'=== {core_imple_name} ===')

        if TYPE_CHECKING:
            from ottype import core as core_impl  # type:ignore

        for doc_length in [100, 1_000, 10_000]:
            doc = utils.make_random_doc(doc_length)

            for ot_length in [5, 10, 20, 50, 100]:
                exp_ident = (doc_length, ot_length)

                ots = utils.make_random_ots(core_impl.normalize, doc, ot_length)

                st_time = time.perf_counter_ns()
                for _ in range(NUM_ITERATION):
                    core_impl.apply(doc, ots)
                ed_time = time.perf_counter_ns()

                perf = (ed_time - st_time) / 1_000 / NUM_ITERATION
                if exp_ident not in prev_record:
                    prev_record[exp_ident] = perf

                print('len(doc) : %5d, len(OTs) : %3d, Performance : %6.2lf ms/loop ( %5.2lfx )' % (
                    doc_length, ot_length, perf, 1 / (perf / prev_record[exp_ident])
                ))


def benchmark_inverse_apply() -> None:
    print('Target: inverse_apply')

    prev_record = dict()

    for core_imple_name, core_impl in CORE_IMPL:
        print(f'=== {core_imple_name} ===')

        if TYPE_CHECKING:
            from ottype import core as core_impl  # type:ignore

        for doc_length in [100, 1_000, 10_000]:
            doc = utils.make_random_doc(doc_length)

            for ot_length in [5, 10, 20, 50, 100]:
                exp_ident = (doc_length, ot_length)

                ots = utils.make_random_ots(core_impl.normalize, doc, ot_length)
                new_doc = core_impl.apply(doc, ots)

                st_time = time.perf_counter_ns()
                for _ in range(NUM_ITERATION):
                    core_impl.inverse_apply(new_doc, ots)
                ed_time = time.perf_counter_ns()

                perf = (ed_time - st_time) / 1_000 / NUM_ITERATION
                if exp_ident not in prev_record:
                    prev_record[exp_ident] = perf

                print('len(doc) : %5d, len(OTs) : %3d, Performance : %6.2lf ms/loop ( %5.2lfx )' % (
                    doc_length, ot_length, perf, 1 / (perf / prev_record[exp_ident])
                ))


benchmark_apply()
print()
benchmark_inverse_apply()
