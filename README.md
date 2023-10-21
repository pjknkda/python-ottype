# Python-OTType

A python library for Operational Transformation (OT). Basic idea follows the spec at https://github.com/ottypes/docs.

Supported Python versions : CPython 3.8 - 3.11


## Installation

```sh
pip install python-ottype
```

Basic usage:

```python
import ottype

assert ottype.apply('asdf', [3, '123', {'d':'f'}]) == 'asd123'
```


## OT Operations

### Skip

Object type : `int`

Skip `n` characters from the current position is represented as `n`

```python
assert apply('asdf', [3]) == 'asdf'
```

### Insert

Object type : `str`

Insert a string `s` at the current position is represented as `s`

```python
assert apply('asdf', ['qwer']) == 'qwerasdf'
assert apply('asdf', [2, 'qwer']) == 'asqwerdf'
```

### Delete

Object type : `dict`

Delete a string `s` at the current position is represented as `{'d': s}`

```python
assert apply('asdf', [{'d': 'as'}]) == 'df'
assert apply('asdf', [1, {'d': 'sd'}]) == 'af'
```

## Supported Functions

```python
OT = int | str | dict[str, str]
```

### `check(ots: list[OT], *, check_unoptimized: bool = True) -> bool`

Check a list whether it only contains valid OTs. If `check_unoptimized` is `True`, only normalized list of OTs is accepted.

```python
assert check(['a', 4, 'b'])
assert not check(['a', 'b'])  # is not normalized
assert not check([3])  # is not normalized
```

### `apply(doc: str, ots: list[OT], *, check_unoptimized: bool = True) -> str`

Apply a list of OTs to a string.

```python
assert apply('abcde', [2, 'qq', {'d': 'c'}, 1, 'w']) == 'abqqdwe'
```

### `inverse_apply(doc: str, ots: list[OT], *, check_unoptimized: bool = True) -> str`

Inversely apply a list of OTs to a string.

```python
assert inverse_apply(apply(doc, ots), ots) == doc
```

### `normalize(ots: list[OT]) -> list[OT]`

Normalize a list of OTs : merge consecutive OTs and trim the last skip operation.

```python
assert normalize([1, 2, 'as', 'df', {'d': 'qw'}, {'d': 'er'}, 3]) \
        == [3, 'asdf', {'d': 'qwer'}]
```


### `transform(ots1: list[OT], ots2: list[OT]) -> list[OT]`

Transform a list of OTs with the property:

```python
assert apply(apply(doc, ots1), transform(ots2, ots1, 'left')) \
        == apply(apply(doc, ots2), transform(ots1, ots2, 'right'))
```

### `compose(ots1: list[OT], ots2: list[OT]) -> list[OT]`

Compose two list of OTs with the property:

```python
assert apply(apply(doc, ots1), ots2) == apply(doc, compose(ots1, ots2))
```



## Benchmark (at Python 3.11)

### Bechnmark : `apply` operation

| len(doc) | len(ots) | baseline (op/s) | python (op/s) | cython (op/s) |
|---:|---:|---:|---:|---:|
|   100 |   5 | 310.38 ( 1.00x) | 415.91 ( 1.34x) | 590.83 ( 1.90x) |
|   100 |  10 | 213.27 ( 1.00x) | 204.82 ( 0.96x) | 469.43 ( 2.20x) |
|   100 |  20 |  94.72 ( 1.00x) | 112.82 ( 1.19x) | 457.64 ( 4.83x) |
|   100 |  50 |  52.70 ( 1.00x) |  49.87 ( 0.95x) | 126.20 ( 2.39x) |
|   100 | 100 |  21.74 ( 1.00x) |  29.78 ( 1.37x) |  78.39 ( 3.61x) |
|  1000 |   5 | 493.57 ( 1.00x) | 322.84 ( 0.65x) | 638.34 ( 1.29x) |
|  1000 |  10 | 181.16 ( 1.00x) | 171.70 ( 0.95x) | 438.26 ( 2.42x) |
|  1000 |  20 |  92.83 ( 1.00x) | 121.60 ( 1.31x) | 331.89 ( 3.58x) |
|  1000 |  50 |  43.47 ( 1.00x) |  60.56 ( 1.39x) | 121.90 ( 2.80x) |
|  1000 | 100 |  20.67 ( 1.00x) |  22.46 ( 1.09x) |  77.43 ( 3.75x) |
| 10000 |   5 | 355.19 ( 1.00x) | 511.89 ( 1.44x) | 360.03 ( 1.01x) |
| 10000 |  10 | 125.78 ( 1.00x) | 174.76 ( 1.39x) | 313.41 ( 2.49x) |
| 10000 |  20 |  77.23 ( 1.00x) |  98.21 ( 1.27x) | 246.25 ( 3.19x) |
| 10000 |  50 |  32.63 ( 1.00x) |  42.51 ( 1.30x) | 114.60 ( 3.51x) |
| 10000 | 100 |  18.12 ( 1.00x) |  23.37 ( 1.29x) |  64.85 ( 3.58x) |


### Bechnmark : `inverse_apply` operation

| len(doc) | len(ots) | baseline (op/s) | python (op/s) | cython (op/s) |
|---:|---:|---:|---:|---:|
|   100 |   5 | 222.70 ( 1.00x) | 217.16 ( 0.98x) | 600.39 ( 2.70x) |
|   100 |  10 |  98.34 ( 1.00x) | 154.64 ( 1.57x) | 391.55 ( 3.98x) |
|   100 |  20 |  82.22 ( 1.00x) |  76.66 ( 0.93x) | 174.17 ( 2.12x) |
|   100 |  50 |  35.24 ( 1.00x) |  35.82 ( 1.02x) |  92.70 ( 2.63x) |
|   100 | 100 |  17.57 ( 1.00x) |  19.50 ( 1.11x) |  48.85 ( 2.78x) |
|  1000 |   5 | 282.72 ( 1.00x) | 270.60 ( 0.96x) | 443.24 ( 1.57x) |
|  1000 |  10 | 168.26 ( 1.00x) | 119.19 ( 0.71x) | 357.90 ( 2.13x) |
|  1000 |  20 |  60.79 ( 1.00x) |  64.79 ( 1.07x) | 293.46 ( 4.83x) |
|  1000 |  50 |  26.98 ( 1.00x) |  29.60 ( 1.10x) |  93.06 ( 3.45x) |
|  1000 | 100 |  14.38 ( 1.00x) |  18.09 ( 1.26x) |  53.81 ( 3.74x) |
| 10000 |   5 | 172.21 ( 1.00x) | 178.69 ( 1.04x) | 318.69 ( 1.85x) |
| 10000 |  10 | 143.82 ( 1.00x) | 120.42 ( 0.84x) | 257.91 ( 1.79x) |
| 10000 |  20 |  55.85 ( 1.00x) |  99.49 ( 1.78x) | 181.88 ( 3.26x) |
| 10000 |  50 |  33.09 ( 1.00x) |  31.53 ( 0.95x) |  76.12 ( 2.30x) |
| 10000 | 100 |  16.76 ( 1.00x) |  17.02 ( 1.02x) |  43.02 ( 2.57x) |
