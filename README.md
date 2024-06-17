# Python-OTType

A python library for Operational Transformation (OT). Basic idea follows the spec at https://github.com/ottypes/docs.

Supported Python versions : CPython 3.9 - 3.12, PyPy 3.9 - 3.10


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

### `check(ots: Sequence[OT], *, check_unoptimized: bool = True) -> bool`

Check the sequence if it only contains valid OTs. If `check_unoptimized` is `True`, only normalized sequence of OTs is accepted.

```python
assert check(['a', 4, 'b'])
assert not check(['a', 'b'])  # is not normalized
assert not check([3])  # is not normalized
```

### `apply(doc: str, ots: Sequence[OT], *, check_unoptimized: bool = True) -> str`

Apply a sequence of OTs to a string.

```python
assert apply('abcde', [2, 'qq', {'d': 'c'}, 1, 'w']) == 'abqqdwe'
```

### `inverse_apply(doc: str, ots: Sequence[OT], *, check_unoptimized: bool = True) -> str`

Inversely apply a sequence of OTs to a string.

```python
assert inverse_apply(apply(doc, ots), ots) == doc
```

### `normalize(ots: Sequence[OT]) -> Sequence[OT]`

Normalize a sequence of OTs : merge consecutive OTs and trim the last skip operation.

```python
assert normalize([1, 2, 'as', 'df', {'d': 'qw'}, {'d': 'er'}, 3]) \
        == [3, 'asdf', {'d': 'qwer'}]
```


### `transform(ots1: Sequence[OT], ots2: Sequence[OT]) -> Sequence[OT]`

Transform a sequence of OTs with the property:

```python
assert apply(apply(doc, ots1), transform(ots2, ots1, 'left')) \
        == apply(apply(doc, ots2), transform(ots1, ots2, 'right'))
```

### `compose(ots1: Sequence[OT], ots2: Sequence[OT]) -> Sequence[OT]`

Compose two sequences of OTs with the property:

```python
assert apply(apply(doc, ots1), ots2) == apply(doc, compose(ots1, ots2))
```



## Benchmark (at CPython 3.12.1)

### Benchmark : `apply` operation

| len(doc) | len(ots) | python (Kops/s) | cython (Kops/s) |
|---:|---:|---:|---:|
|   100 |   5 |  289.58 ( 1.00x) |  663.47 ( 2.29x) |
|   100 |  10 |  206.50 ( 1.00x) |  513.00 ( 2.48x) |
|   100 |  20 |  114.52 ( 1.00x) |  298.82 ( 2.61x) |
|   100 |  50 |   48.37 ( 1.00x) |  127.90 ( 2.64x) |
|   100 | 100 |   26.96 ( 1.00x) |   71.84 ( 2.66x) |
|  1000 |   5 |  412.41 ( 1.00x) |  974.43 ( 2.36x) |
|  1000 |  10 |  220.19 ( 1.00x) |  493.53 ( 2.24x) |
|  1000 |  20 |  128.66 ( 1.00x) |  317.18 ( 2.47x) |
|  1000 |  50 |   37.56 ( 1.00x) |   98.56 ( 2.62x) |
|  1000 | 100 |   23.43 ( 1.00x) |   64.25 ( 2.74x) |
| 10000 |   5 |  203.14 ( 1.00x) |  322.31 ( 1.59x) |
| 10000 |  10 |  142.25 ( 1.00x) |  279.79 ( 1.97x) |
| 10000 |  20 |   95.63 ( 1.00x) |  202.97 ( 2.12x) |
| 10000 |  50 |   48.58 ( 1.00x) |  122.09 ( 2.51x) |
| 10000 | 100 |   21.17 ( 1.00x) |   57.59 ( 2.72x) |

### Benchmark : `inverse_apply` operation

| len(doc) | len(ots) | python (Kops/s) | cython (Kops/s) |
|---:|---:|---:|---:|
|   100 |   5 |  194.12 ( 1.00x) |  408.56 ( 2.10x) |
|   100 |  10 |  113.27 ( 1.00x) |  269.10 ( 2.38x) |
|   100 |  20 |   60.99 ( 1.00x) |  150.49 ( 2.47x) |
|   100 |  50 |   26.35 ( 1.00x) |   64.27 ( 2.44x) |
|   100 | 100 |   16.62 ( 1.00x) |   42.87 ( 2.58x) |
|  1000 |   5 |  309.57 ( 1.00x) |  565.47 ( 1.83x) |
|  1000 |  10 |  153.62 ( 1.00x) |  351.55 ( 2.29x) |
|  1000 |  20 |   69.48 ( 1.00x) |  162.52 ( 2.34x) |
|  1000 |  50 |   37.12 ( 1.00x) |   91.88 ( 2.48x) |
|  1000 | 100 |   17.06 ( 1.00x) |   42.51 ( 2.49x) |
| 10000 |   5 |  145.11 ( 1.00x) |  257.81 ( 1.78x) |
| 10000 |  10 |   96.66 ( 1.00x) |  198.97 ( 2.06x) |
| 10000 |  20 |   65.18 ( 1.00x) |  140.90 ( 2.16x) |
| 10000 |  50 |   27.40 ( 1.00x) |   67.74 ( 2.47x) |
| 10000 | 100 |   13.53 ( 1.00x) |   32.23 ( 2.38x) |
