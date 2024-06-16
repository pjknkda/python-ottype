import random
import timeit
from typing import TYPE_CHECKING

from ottype import core_boost  # type: ignore
from ottype import core
from tests import utils

NUM_ITERATION = 100_000

CORE_IMPL = [("python", core), ("cython", core_boost)]

random.seed(457700)


def benchmark_apply() -> None:
    print("### Benchmark : `apply` operation")
    print()

    print(
        "| len(doc) | len(ots) | "
        + " | ".join(f"{name} (Kops/s)" for name, _ in CORE_IMPL)
        + " |"
    )
    print("|---:|" + "---:|" * (1 + len(CORE_IMPL)))

    baseline_perf: dict[str, float] = dict()
    for doc_length in [100, 1_000, 10_000]:
        doc = utils.make_random_doc(doc_length)

        for ot_length in [5, 10, 20, 50, 100]:
            test_config = f"{doc_length:5d} | {ot_length:3d}"
            ots = utils.make_random_ots(doc, ot_length)

            perfs: list[str] = []
            for _, core_impl in CORE_IMPL:
                if TYPE_CHECKING:
                    from ottype import core as core_impl

                normalized_ots = core_impl.normalize(ots)

                duration = timeit.timeit(
                    "core_impl.apply(doc, normalized_ots)",
                    number=NUM_ITERATION,
                    globals={
                        "core_impl": core_impl,
                        "doc": doc,
                        "normalized_ots": normalized_ots,
                    },
                )

                perf = NUM_ITERATION / duration / 1000
                if test_config not in baseline_perf:
                    baseline_perf[test_config] = perf

                perfs.append(f"{perf:7.2f} ({perf / baseline_perf[test_config]:5.2f}x)")

            print(f"| {test_config} | " + " | ".join(perfs) + " |")


def benchmark_inverse_apply() -> None:
    print("### Benchmark : `inverse_apply` operation")
    print()

    print(
        "| len(doc) | len(ots) | "
        + " | ".join(f"{name} (Kops/s)" for name, _ in CORE_IMPL)
        + " |"
    )
    print("|---:|" + "---:|" * (1 + len(CORE_IMPL)))

    baseline_perf: dict[str, float] = dict()
    for doc_length in [100, 1_000, 10_000]:
        doc = utils.make_random_doc(doc_length)

        for ot_length in [5, 10, 20, 50, 100]:
            test_config = f"{doc_length:5d} | {ot_length:3d}"

            ots = utils.make_random_ots(doc, ot_length)

            perfs: list[str] = []
            for _, core_impl in CORE_IMPL:
                if TYPE_CHECKING:
                    from ottype import core as core_impl

                normalized_ots = core_impl.normalize(ots)

                new_doc = core_impl.apply(doc, normalized_ots)

                duration = timeit.timeit(
                    "core_impl.inverse_apply(new_doc, normalized_ots)",
                    number=NUM_ITERATION,
                    globals={
                        "core_impl": core_impl,
                        "new_doc": new_doc,
                        "normalized_ots": normalized_ots,
                    },
                )

                perf = NUM_ITERATION / duration / 1000
                if test_config not in baseline_perf:
                    baseline_perf[test_config] = perf

                perfs.append(f"{perf:7.2f} ({perf / baseline_perf[test_config]:5.2f}x)")

            print(f"| {test_config} | " + " | ".join(perfs) + " |")


benchmark_apply()
print()
benchmark_inverse_apply()
