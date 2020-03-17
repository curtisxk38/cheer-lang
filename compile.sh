llc $1 -march=x86-64 -o example.s
gcc -c example.s -o example.o
gcc example.o -o a.out
#rm example.s example.o