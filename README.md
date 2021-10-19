# Python-OTType

A python library for Operational Transformation (OT). Basic idea follows the spec at https://github.com/ottypes/docs.

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
OT = Union[int, str, Dict[str, str]]
```

### `check(ots: List[OT], *, check_unoptimized: bool = True) -> bool`

Check a list whether it only contains valid OTs. If `check_unoptimized` is `True`, only normalized list of OTs is accepted.

```python
assert check(['a', 4, 'b'])
assert not check(['a', 'b'])  # is not normalized
assert not check([3])  # is not normalized
```

### `apply(doc: str, ots: List[OT], *, check_unoptimized: bool = True) -> str`

Apply a list of OTs to a string.

```python
assert apply('abcde', [2, 'qq', {'d': 'c'}, 1, 'w']) == 'abqqdwe'
```

### `inverse_apply(doc: str, ots: List[OT], *, check_unoptimized: bool = True) -> str`

Inversely apply a list of OTs to a string.

```python
assert inverse_apply(apply(doc, ots), ots) == doc
```

### `normalize(ots: List[OT]) -> List[OT]`

Normalize a list of OTs : merge consecutive OTs and trim the last skip operation.

```python
assert normalize([1, 2, 'as', 'df', {'d': 'qw'}, {'d': 'er'}, 3]) \
        == [3, 'asdf', {'d': 'qwer'}]
```


### `transform(ots1: List[OT], ots2: List[OT]) -> List[OT]`

Transform a list of OTs with the property:

```python
assert apply(apply(doc, ots1), transform(ots2, ots1, 'left')) \
        == apply(apply(doc, ots2), transform(ots1, ots2, 'right'))
```

### `compose(ots1: List[OT], ots2: List[OT]) -> List[OT]`

Compose two list of OTs with the property:

```python
assert apply(apply(doc, ots1), ots2) == apply(doc, compose(ots1, ots2))
```



## Benchmark (at Python 3.7)

### `apply` function

```
=== baseline (extra.old_ottype) ===
Doc Length :   100, OT Length :   5, Performance :   5.80 ms/loop (  1.00x )
Doc Length :   100, OT Length :  10, Performance :   8.87 ms/loop (  1.00x )
Doc Length :   100, OT Length :  20, Performance :  16.47 ms/loop (  1.00x )
Doc Length :   100, OT Length :  50, Performance :  39.13 ms/loop (  1.00x )
Doc Length :   100, OT Length : 100, Performance :  73.84 ms/loop (  1.00x )
Doc Length :  1000, OT Length :   5, Performance :   4.70 ms/loop (  1.00x )
Doc Length :  1000, OT Length :  10, Performance :   7.46 ms/loop (  1.00x )
Doc Length :  1000, OT Length :  20, Performance :  14.55 ms/loop (  1.00x )
Doc Length :  1000, OT Length :  50, Performance :  50.22 ms/loop (  1.00x )
Doc Length :  1000, OT Length : 100, Performance :  83.51 ms/loop (  1.00x )
Doc Length : 10000, OT Length :   5, Performance :   7.43 ms/loop (  1.00x )
Doc Length : 10000, OT Length :  10, Performance :  13.05 ms/loop (  1.00x )
Doc Length : 10000, OT Length :  20, Performance :  18.66 ms/loop (  1.00x )
Doc Length : 10000, OT Length :  50, Performance :  41.28 ms/loop (  1.00x )
Doc Length : 10000, OT Length : 100, Performance :  97.67 ms/loop (  1.00x )
=== python ===
Doc Length :   100, OT Length :   5, Performance :   6.77 ms/loop (  0.86x )
Doc Length :   100, OT Length :  10, Performance :  15.48 ms/loop (  0.57x )
Doc Length :   100, OT Length :  20, Performance :  27.14 ms/loop (  0.61x )
Doc Length :   100, OT Length :  50, Performance :  54.14 ms/loop (  0.72x )
Doc Length :   100, OT Length : 100, Performance :  84.28 ms/loop (  0.88x )
Doc Length :  1000, OT Length :   5, Performance :   4.23 ms/loop (  1.11x )
Doc Length :  1000, OT Length :  10, Performance :   8.74 ms/loop (  0.85x )
Doc Length :  1000, OT Length :  20, Performance :  18.65 ms/loop (  0.78x )
Doc Length :  1000, OT Length :  50, Performance :  37.61 ms/loop (  1.34x )
Doc Length :  1000, OT Length : 100, Performance :  82.60 ms/loop (  1.01x )
Doc Length : 10000, OT Length :   5, Performance :   8.86 ms/loop (  0.84x )
Doc Length : 10000, OT Length :  10, Performance :  13.19 ms/loop (  0.99x )
Doc Length : 10000, OT Length :  20, Performance :  20.43 ms/loop (  0.91x )
Doc Length : 10000, OT Length :  50, Performance :  48.91 ms/loop (  0.84x )
Doc Length : 10000, OT Length : 100, Performance : 102.81 ms/loop (  0.95x )
=== cython ===
Doc Length :   100, OT Length :   5, Performance :   0.77 ms/loop (  7.55x )
Doc Length :   100, OT Length :  10, Performance :   1.36 ms/loop (  6.53x )
Doc Length :   100, OT Length :  20, Performance :   2.34 ms/loop (  7.04x )
Doc Length :   100, OT Length :  50, Performance :   4.74 ms/loop (  8.25x )
Doc Length :   100, OT Length : 100, Performance :   9.73 ms/loop (  7.59x )
Doc Length :  1000, OT Length :   5, Performance :   0.70 ms/loop (  6.75x )
Doc Length :  1000, OT Length :  10, Performance :   1.61 ms/loop (  4.64x )
Doc Length :  1000, OT Length :  20, Performance :   2.47 ms/loop (  5.88x )
Doc Length :  1000, OT Length :  50, Performance :   5.52 ms/loop (  9.10x )
Doc Length :  1000, OT Length : 100, Performance :   9.02 ms/loop (  9.26x )
Doc Length : 10000, OT Length :   5, Performance :   2.20 ms/loop (  3.38x )
Doc Length : 10000, OT Length :  10, Performance :   2.57 ms/loop (  5.07x )
Doc Length : 10000, OT Length :  20, Performance :   2.95 ms/loop (  6.33x )
Doc Length : 10000, OT Length :  50, Performance :   5.97 ms/loop (  6.92x )
Doc Length : 10000, OT Length : 100, Performance :  10.92 ms/loop (  8.94x )
```

### `inverse_apply` function

```
=== baseline (extra.old_ottype) ===
Doc Length :   100, OT Length :   5, Performance :   8.26 ms/loop (  1.00x )
Doc Length :   100, OT Length :  10, Performance :  15.00 ms/loop (  1.00x )
Doc Length :   100, OT Length :  20, Performance :  27.50 ms/loop (  1.00x )
Doc Length :   100, OT Length :  50, Performance :  56.86 ms/loop (  1.00x )
Doc Length :   100, OT Length : 100, Performance : 129.10 ms/loop (  1.00x )
Doc Length :  1000, OT Length :   5, Performance :   6.35 ms/loop (  1.00x )
Doc Length :  1000, OT Length :  10, Performance :  16.14 ms/loop (  1.00x )
Doc Length :  1000, OT Length :  20, Performance :  22.65 ms/loop (  1.00x )
Doc Length :  1000, OT Length :  50, Performance :  67.26 ms/loop (  1.00x )
Doc Length :  1000, OT Length : 100, Performance : 113.74 ms/loop (  1.00x )
Doc Length : 10000, OT Length :   5, Performance :   8.79 ms/loop (  1.00x )
Doc Length : 10000, OT Length :  10, Performance :  10.16 ms/loop (  1.00x )
Doc Length : 10000, OT Length :  20, Performance :  22.46 ms/loop (  1.00x )
Doc Length : 10000, OT Length :  50, Performance :  54.26 ms/loop (  1.00x )
Doc Length : 10000, OT Length : 100, Performance : 129.20 ms/loop (  1.00x )
=== python ===
Doc Length :   100, OT Length :   5, Performance :   6.05 ms/loop (  1.37x )
Doc Length :   100, OT Length :  10, Performance :  11.30 ms/loop (  1.33x )
Doc Length :   100, OT Length :  20, Performance :  21.16 ms/loop (  1.30x )
Doc Length :   100, OT Length :  50, Performance :  44.43 ms/loop (  1.28x )
Doc Length :   100, OT Length : 100, Performance : 101.05 ms/loop (  1.28x )
Doc Length :  1000, OT Length :   5, Performance :  10.06 ms/loop (  0.63x )
Doc Length :  1000, OT Length :  10, Performance :  12.38 ms/loop (  1.30x )
Doc Length :  1000, OT Length :  20, Performance :  24.55 ms/loop (  0.92x )
Doc Length :  1000, OT Length :  50, Performance :  42.64 ms/loop (  1.58x )
Doc Length :  1000, OT Length : 100, Performance :  96.43 ms/loop (  1.18x )
Doc Length : 10000, OT Length :   5, Performance :   9.42 ms/loop (  0.93x )
Doc Length : 10000, OT Length :  10, Performance :  11.89 ms/loop (  0.85x )
Doc Length : 10000, OT Length :  20, Performance :  25.74 ms/loop (  0.87x )
Doc Length : 10000, OT Length :  50, Performance :  58.58 ms/loop (  0.93x )
Doc Length : 10000, OT Length : 100, Performance :  97.37 ms/loop (  1.33x )
=== cython ===
Doc Length :   100, OT Length :   5, Performance :   1.12 ms/loop (  7.37x )
Doc Length :   100, OT Length :  10, Performance :   1.69 ms/loop (  8.90x )
Doc Length :   100, OT Length :  20, Performance :   2.80 ms/loop (  9.82x )
Doc Length :   100, OT Length :  50, Performance :   5.49 ms/loop ( 10.35x )
Doc Length :   100, OT Length : 100, Performance :  12.22 ms/loop ( 10.56x )
Doc Length :  1000, OT Length :   5, Performance :   1.36 ms/loop (  4.68x )
Doc Length :  1000, OT Length :  10, Performance :   2.25 ms/loop (  7.19x )
Doc Length :  1000, OT Length :  20, Performance :   2.98 ms/loop (  7.61x )
Doc Length :  1000, OT Length :  50, Performance :   6.26 ms/loop ( 10.75x )
Doc Length :  1000, OT Length : 100, Performance :  11.14 ms/loop ( 10.21x )
Doc Length : 10000, OT Length :   5, Performance :   2.35 ms/loop (  3.75x )
Doc Length : 10000, OT Length :  10, Performance :   3.62 ms/loop (  2.81x )
Doc Length : 10000, OT Length :  20, Performance :   4.50 ms/loop (  4.99x )
Doc Length : 10000, OT Length :  50, Performance :   7.07 ms/loop (  7.68x )
Doc Length : 10000, OT Length : 100, Performance :  14.20 ms/loop (  9.10x )
```
