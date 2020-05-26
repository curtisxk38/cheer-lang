from cheer import ir_helpers


class Branch:
    def __init__(self, bb: 'ir_helpers.BasicBlock'):
        self.bb = bb

    def to_llvm_ir(self):
        return f"br label %{self.bb.name}"

class ConditionalBranch:
    def __init__(self, expr: 'ir_helpers.Expr', true_bb: 'ir_helpers.BasicBlock', false_bb: 'ir_helpers.BasicBlock'):
        self.expr = expr # value or register starting with %
        self.true_bb = true_bb
        self.false_bb = false_bb

    def to_llvm_ir(self):
        return f"br i1 {self.expr.get_name_or_value()}, label %{self.true_bb.name}, label %{self.false_bb.name}"

class Phi:
    def __init__(self, lhs, type_, op1: 'ir_helpers.Expr', bb1: 'ir_helpers.BasicBlock', op2: 'ir_helpers.Expr', bb2: 'ir_helpers.BasicBlock'):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.bb1 = bb1
        self.op2 = op2
        self.bb2 = bb2

    def to_llvm_ir(self):
        return f"%{self.lhs} = phi {self.type} [{self.op1.get_name_or_value()}, {self.bb1.name}], \
            [{self.op2, self.bb2.name.get_name_or_value()}]"

class Return:
    def __init__(self, type_, op: 'ir_helpers.Expr'):
        self.type = type_
        self.op = op

    def to_llvm_ir(self):
        return f"ret {self.type} {self.op.get_name_or_value()}"

class Compare:
    def __init__(self, lhs, comp_type, type_, op1: 'ir_helpers.Expr', op2: 'ir_helpers.Expr'):
        self.lhs = lhs
        self.comp_type = comp_type
        self.type = type_
        self.op1 = op1
        self.op2 = op2

    def to_llvm_ir(self):
        return f"%{self.lhs} = icmp {self.comp_type} {self.type} \
            {self.op1.get_name_or_value()}, {self.op2.get_name_or_value()}"

class Add:
    def __init__(self, lhs, type_, op1: 'ir_helpers.Expr', op2: 'ir_helpers.Expr'):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.op2 = op2

    def to_llvm_ir(self):
        return f"%{self.lhs} = add {self.type} {self.op1.get_name_or_value()}, {self.op2.get_name_or_value()}"

class Subtract:
    def __init__(self, lhs, type_, op1: 'ir_helpers.Expr', op2: 'ir_helpers.Expr'):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.op2 = op2

    def to_llvm_ir(self):
        return f"%{self.lhs} = sub {self.type} {self.op1.get_name_or_value()}, {self.op2.get_name_or_value()}"

class Multiply:
    def __init__(self, lhs, type_, op1: 'ir_helpers.Expr', op2: 'ir_helpers.Expr'):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.op2 = op2

    def to_llvm_ir(self):
        return f"%{self.lhs} = mul {self.type} {self.op1.get_name_or_value()}, {self.op2.get_name_or_value()}"

class SignExtend:
    def __init__(self, lhs, in_type, op1, out_type):
        self.lhs = lhs
        self.in_type = in_type
        self.op1 = op1
        self.out_type = out_type

    def to_llvm_ir(self):
        return f"%{self.lhs} = sext {self.in_type} %{self.op1} to {self.out_type}"

class Allocate:
    # allocate on the stack frame
    def __init__(self, lhs, type_, align):
        self.lhs = lhs
        self.type = type_
        self.align = align

    def to_llvm_ir(self):
        return f"%{self.lhs} = alloca {self.type}, align {self.align}"

class Load:
    def __init__(self, lhs, type_, op1, align):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.align = align

    def to_llvm_ir(self):
        return f"%{self.lhs} = load {self.type}, {self.type}* %{self.op1}, align {self.align}"

class GetElementPtr:
    '''
    ----------
    struct munger_struct {
      int f1;
      int f2;
    };
    void munge(struct munger_struct *P) {
      P[0].f1 = P[1].f1 + P[2].f2;
    }
    ...
    struct munger_struct Array[3];
    ...
    munge(Array);
    ----------
    generates:
    ----------
    define void @munge(%struct.munger_struct* %P) {
    entry:
      %tmp = getelementptr %struct.munger_struct, %struct.munger_struct* %P, i32 1, i32 0
      ; tmp1 = P[1].f1
      %tmp1 = load i32, i32* %tmp
      %tmp2 = getelementptr %struct.munger_struct, %struct.munger_struct* %P, i32 2, i32 1
      ; tmp3 = P[2].f2
      %tmp3 = load i32, i32* %tmp2
      %tmp4 = add i32 %tmp3, %tmp1
      %tmp5 = getelementptr %struct.munger_struct, %struct.munger_struct* %P, i32 0, i32 0
      store i32 %tmp4, i32* %tmp5
      ret void
    }
    ----------
    see: https://www.llvm.org/docs/GetElementPtr.html
    '''
    # <result> = getelementptr inbounds <ty>, <ty>* <ptrval>{, [inrange] <ty> <idx>}*
    def __init__(self, lhs, type_, op1, index1, index2):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.index1 = index1
        self.index2 = index2

    def to_llvm_ir(self):
        return f"%{self.lhs} = getelementptr inbounds {self.type}, {self.type}* %{self.op1}, i32 {self.index1}, i32, {self.index2}"

class CallAsm:
    # not generic at the moment
    # hard coded for what we need for input
    def __init__(self, lhs, return_type, rhs):
        self.lhs = lhs
        self.return_type = return_type
        self.rhs = rhs

    def to_llvm_ir(self):
        return '{} = call i32 asm sideeffect "movl $$0x00000000, %edi\\0Amovl $$0x00000002, %edx\\0Amovl $$0, %eax\\0Asyscall\\0A", "={{ax}},{{si}},~{{dirflag}},~{{fpsr}},~{{flags}}"(i8* {})'.format(self.lhs, self.rhs)