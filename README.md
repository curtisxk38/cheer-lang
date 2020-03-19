# Cheer

## Planned features

- [ ] functions
- [ ] type inference

## Compiling

```
python3 compile.py example.cl
llc example.ll -march=x86-64 -o example.s
gcc -c example.s -o example.o
gcc example.o -o example.out
```

## Run tests

```
pip install -e .[test]
pytest
flake8
mypy cheer
```