# Cheer

## Planned features

- [ ] functions
- [ ] type inference

## Compiling

Currently requires `llc` and `gcc`

```
./compile.sh test_input/prog2.ch
```

## Run tests

```
pip install -e .[test]
pytest
flake8
mypy cheer
```