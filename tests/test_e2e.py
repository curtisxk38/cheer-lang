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
    try:
        subprocess.run(shlex.split('llc example.ll -march=x86-64 -o example.s'), check=True)
        subprocess.run(shlex.split('gcc -c example.s -o example.o'), check=True)
        subprocess.run(shlex.split('gcc example.o -o a.out'), check=True)
    except subprocess.CalledProcessError:
        # failed to compile
        return False
    return True


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
    ),
    ProgramConfig(
        '''
        fn main() {
            if (5 == 3) {
                return 5 + 4;
            } else {
                return 3 - 2;
            }
        }''', returns=1
    ),
    ProgramConfig(
    '''
    fn main() {
        let x = 4;
        let y = x + 1;
        y = y + y;
        if (y - 4 == 0) {
            return 5 + 4;
        } else {
            return 3 - 2;
        }
    }
    ''', returns=1
    ),
    ProgramConfig(
    '''
    fn main() {
        let y = 0;
        if (true) {
            y = 2;
        } else {
            let x = 0;
        }
        y = y + 4;
        return y;
    }
    ''', returns=6,
    ),
    ProgramConfig(
    '''
    fn main() {
        let y = 0;
        if (false) {
            y = 2;
        } else {
            return 1;
        }
        y = y + 4;
        return y;
    }
    ''', returns=1,
    ),
    ProgramConfig(
    '''
    fn main() {
        let y = 4;
        if (false) {
            y = 1;
        }
        return y;
    }
    ''', returns=4,
    ),
    ProgramConfig(
    '''
    fn main() {
        let y = 4;
        if (true) {
            y = 1;
        }
        return y;
    }
    ''', returns=1,
    ),
    ProgramConfig(
    '''
    fn main() {
        let y = 4;
        if (true) {
            y = 1;
            return y;
        }
        return y;
    }
    ''', returns=1,
    ),
    ProgramConfig(
    '''
    fn main() {
        let y = 0;
        if (true) {
            y = 2;
            return y;
        } else {
            y = 3;
        }
        return y;
    }
    ''', returns=2,
    ),
    ProgramConfig(
    '''
    fn main() {
        let y = 0;
        if (false) {
            y = 2;
        }
        else {
            y = y + 1;
        }
        y = y + 4;
        return y;
    }
    ''', returns=5,
    ),
    ProgramConfig(
    '''
    fn main() {
        let y = 5;
        let x = 10;
        while(y < x) {
            y = y + 1;
        }
        return 4;
    }
    ''', returns=4,
    )

]


@pytest.mark.parametrize("test_config", tests)
def test_e2e_program(test_config):
    lines = test_config.prog.split('\n')
    code = compile.compile(FakeOptions(), lines)
    assert compile_backend(code), test_config.prog
    proc = subprocess.Popen('./a.out',
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, errs = proc.communicate(input=test_config.input)
    assert proc.returncode == test_config.returns, test_config.prog