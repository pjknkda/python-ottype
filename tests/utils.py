import random
import string
from typing import Callable, List, Tuple, Union

OTRawListType = List[Union[int, str, dict]]


def make_random_doc(amount: int) -> str:
    if amount < 10:
        amount = 10

    return ''.join(random.choices(string.ascii_letters, k=amount))


def make_random_ots(
    normalize: Callable[[OTRawListType], OTRawListType],
    doc: str,
    n: int,
    ids_weights: Tuple[float, float, float] = (0.4, 0.4, 0.2)
) -> OTRawListType:
    offset = 0
    ot_raw_list: List[Union[int, str, dict]] = []
    for _ in range(n):
        if len(doc) - offset == 0:
            action, = random.choices(['i', 'd'], ids_weights[:2], k=1)
        else:
            action, = random.choices(['i', 'd', 's'], ids_weights, k=1)

        if action == 'i':
            amount = random.randint(1, max(1, min(len(doc) - offset, len(doc) // n)))
            ot_raw_list.append(''.join(random.choices(string.ascii_letters, k=amount)))

        elif action == 'd':
            amount = random.randint(1, max(1, min(len(doc) - offset, len(doc) // n)))
            ot_raw_list.append({'d': doc[offset: offset + amount]})
            offset += amount

        elif action == 's':
            amount = random.randint(1, max(1, min(len(doc) - offset, len(doc) // n)))
            ot_raw_list.append(amount)
            offset += amount

    return normalize(ot_raw_list)
