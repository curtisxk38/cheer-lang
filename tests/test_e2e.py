import subprocess
import shlex
import pytest

from cheer import compile


class FakeOptions:
    def __init__(self):
        self.verbose = False


class ProgramConfig:
    def __init__(self, prog, returns=0, input=None, output=None):
        self.prog = prog
        self.returns = returns
        self.input = input
        self.output = output


def compile_backend(code):
    with open('example.ll', 'w') as f:
        f.write(code)
    subprocess.run(shlex.split('llc example.ll -march=x86-64 -o example.s'))
    subprocess.run(shlex.split('gcc -c example.s -o example.o'))
    subprocess.run(shlex.split('gcc example.o -o a.out'))


tests = [
    ProgramConfig(
        '''
        fn main() {
            return 5 + 5 * (6 - 4) + 4;
        }
        ''', returns=19
    ),
    ProgramConfig(
        '''
        fn main() {
            return 1 + input();
        }
        ''', returns=52, input=b'3\n' # 3 is ascii 51
    ),
    ProgramConfig(
        '''
        fn main() {
            if (5 == 3) {
                return 5 + 4;
            }
            return 1;
        }''', returns=1
    )
]


@pytest.mark.parametrize("test_config", tests)
def test_e2e_program(test_config):
    lines = test_config.prog.split('\n')
    code = compile.compile(FakeOptions(), lines)
    compile_backend(code)
    proc = subprocess.Popen('./a.out',
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, errs = proc.communicate(input=test_config.input)
    assert proc.returncode == test_config.returns