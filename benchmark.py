import random
import time
from typing import TYPE_CHECKING, Any

from ottype import core
from tests import utils

NUM_ITERATION = 100_000

CORE_IMPL: list[tuple[str, Any]] = [('python', core)]

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
    print('### Bechnmark : `apply` operation')
    print()

    print(
        "| len(doc) | len(ots) | " 
        + " | ".join(f"{name} (op/s)" for name, _ in CORE_IMPL) 
        + " |"
    )
    print("|---:|" +  "---:|" * (1 + len(CORE_IMPL)))

    baseline_perf: dict[str, float] = dict()
    for doc_length in [100, 1_000, 10_000]:
        doc = utils.make_random_doc(doc_length)

        for ot_length in [5, 10, 20, 50, 100]:
            test_config = f"{doc_length:5d} | {ot_length:3d}"

            perfs: list[str] = []
            for _, core_impl in CORE_IMPL:
                if TYPE_CHECKING:
                    from ottype import core as core_impl  # type:ignore

                ots = utils.make_random_ots(core_impl.normalize, doc, ot_length)

                st_time = time.perf_counter_ns()
                for _ in range(NUM_ITERATION):
                    core_impl.apply(doc, ots)
                ed_time = time.perf_counter_ns()

                perf = NUM_ITERATION / ((ed_time - st_time) / 1_000_000)
                if test_config not in baseline_perf:
                    baseline_perf[test_config] = perf

                perfs.append(
                    f"{perf:6.2f} ({perf / baseline_perf[test_config]:5.2f}x)"
                )

            print(f"| {test_config} | " + " | ".join(perfs) + " |")


def benchmark_inverse_apply() -> None:
    print('### Bechnmark : `inverse_apply` operation')
    print()

    print(
        "| len(doc) | len(ots) | " 
        + " | ".join(f"{name} (op/s)" for name, _ in CORE_IMPL) 
        + " |"
    )
    print("|---:|" +  "---:|" * (1 + len(CORE_IMPL)))

    baseline_perf: dict[str, float] = dict()
    for doc_length in [100, 1_000, 10_000]:
        doc = utils.make_random_doc(doc_length)

        for ot_length in [5, 10, 20, 50, 100]:
            test_config = f"{doc_length:5d} | {ot_length:3d}"

            perfs: list[str] = []
            for _, core_impl in CORE_IMPL:
                if TYPE_CHECKING:
                    from ottype import core as core_impl  # type:ignore

                ots = utils.make_random_ots(core_impl.normalize, doc, ot_length)
                new_doc = core_impl.apply(doc, ots)

                st_time = time.perf_counter_ns()
                for _ in range(NUM_ITERATION):
                    core_impl.inverse_apply(new_doc, ots)
                ed_time = time.perf_counter_ns()

                perf = NUM_ITERATION / ((ed_time - st_time) / 1_000_000)
                if test_config not in baseline_perf:
                    baseline_perf[test_config] = perf

                perfs.append(
                    f"{perf:6.2f} ({perf / baseline_perf[test_config]:5.2f}x)"
                )

            print(f"| {test_config} | " + " | ".join(perfs) + " |")

benchmark_apply()
print()
benchmark_inverse_apply()
