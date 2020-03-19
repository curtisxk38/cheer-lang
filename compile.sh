#!/usr/bin/env bash

python3 cheer/compile.py -i $1 -o example.ll
llc example.ll -march=x86-64 -o example.s
gcc -c example.s -o example.o
gcc example.o -o a.out
#rm example.s example.o