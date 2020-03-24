# Cheer

This is a compiler from my language Cheer to linux x86-64.

Cheer is inspired by Rust syntax (but doesn't have the ownership system)

## Roadmap / Planned features

- [x] if/else
- [x] local variables
- [ ] while loop
- [ ] functions
- [ ] inline assembly
- [ ] standard library - input, print
- [ ] structs
- [ ] struct methods
- [ ] struct inferfaces/traits
- [ ] standard library - allocate on the heap
- [ ] match statements
- [ ] Some, Ok types
- [ ] compiler backend: create our own llvm ir -> x86 64 instead of using llc
- [ ] standard library - garbage collection allocation
- [ ] optimizations: 
    - [ ] Inline
    - [ ] Unroll (& Vectorize)
    - [ ] CSE
    - [ ] DCE
    - [ ] Code Motion
    - [ ] Constant Fold
    - [ ] Peephole
    - (from `Frances Allen, 1971 - A Catalogue of optimizing transformations`)
- [ ] self hosted compiler

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