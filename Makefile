.PHONY: all
all:

.PHONY: format
format:
	isort ottype/ tests/ benchmark.py
	black ottype/ tests/ benchmark.py
	flake8 ottype/ tests/ benchmark.py
	mypy ottype/ tests/ benchmark.py

.PHONY: check
check:
	black --check ottype/ tests/ benchmark.py
	flake8 ottype/ tests/ benchmark.py
	mypy ottype/ tests/ benchmark.py
	bandit -ll -r ottype/ tests/ benchmark.py

.PHONY: test
test:
	bash docker-run-tests.sh

.PHONY: build_inplace
build_inplace:
	python setup.py build_ext --inplace

.PHONY: build_wheels
build_wheels:
	bash docker-run-build-wheels.sh
