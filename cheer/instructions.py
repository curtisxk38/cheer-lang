

class Branch:
    def __init__(self, label):
        # label DOES not start with %
        self.label = label

    def to_llvm_ir(self):
        return f"br label %{self.label}"

class ConditionalBranch:
    def __init__(self, expr, true_label, false_label):
        self.expr = expr # value or register starting with %
        self.true_label = true_label
        self.false_label = false_label

    def to_llvm_ir(self):
        return f"br i1 {self.expr}, label %{self.true_label}, label %{self.false_label}"

class Phi:
    def __init__(self, lhs, type_, op1, bb1, op2, bb2):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.bb1 = bb1
        self.op2 = op2
        self.bb2 = bb2

    def to_llvm_ir(self):
        return f"{self.lhs} = phi {self.type} [{self.op1}, {self.bb1}], \
            [{self.op2, self.bb2}]"

class Return:
    def __init__(self, type_, op):
        self.type = type_
        self.op = op

    def to_llvm_ir(self):
        return f"ret {self.type} {self.op}"

class Compare:
    def __init__(self, lhs, comp_type, type_, op1, op2):
        self.lhs = lhs
        self.comp_type = comp_type
        self.type = type_
        self.op1 = op1
        self.op2 = op2

    def to_llvm_ir(self):
        return f"{self.lhs} = icmp {self.comp_type} {self.type} \
            {self.op1}, {self.op2}"

class Add:
    def __init__(self, lhs, type_, op1, op2):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.op2 = op2

    def to_llvm_ir(self):
        return f"{self.lhs} = add {self.type} {self.op1}, {self.op2}"

class Subtract:
    def __init__(self, lhs, type_, op1, op2):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.op2 = op2

    def to_llvm_ir(self):
        return f"{self.lhs} = sub {self.type} {self.op1}, {self.op2}"

class Multiply:
    def __init__(self, lhs, type_, op1, op2):
        self.lhs = lhs
        self.type = type_
        self.op1 = op1
        self.op2 = op2

    def to_llvm_ir(self):
        return f"{self.lhs} = mul {self.type} {self.op1}, {self.op2}"

class SignExtend:
    def __init__(self, lhs, in_type, op1, out_type):
        self.lhs = lhs
        self.in_type = in_type
        self.op1 = op1
        self.out_type = out_type

    def to_llvm_ir(self):
        return f"{self.lhs} = sext {self.in_type} {self.op1} {self.out_type}"

class Allocate:
    # allocate on the stack frame
    def __init__(self, lhs, type_, align):
        self.lhs = lhs
        self.type = type_
        self.align = align

    def to_llvm_ir(self):
        return f"{self.lhs} = alloca {self.type}, align {self.align}"

class Load:
    def __init__(self):
        pass

class GetElementPtr:
    def __init__(self):
        pass

class CallAsm:
    def __init__(self):
        pass