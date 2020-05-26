from cheer import instructions as instr


class BasicBlock:
    def __init__(self, name):
        self.name = name
        self.lines = []
        self.terminated = False
        self.returns = False
        self.predecessors = set()

    def to_code(self):
        label = f"{self.name}:"
        return [label] + [line.to_llvm_ir() for line in self.lines]

    def add_instr(self, line):
        if not self.terminated:
            self.lines.append(indent + line)
            if instanceof(line, instr.Return):
                self.terminated = True
                self.returns = True
            if instanceof(line, instr.Branch) or instanceof(line, instr.ConditionalBranch):
                self.terminated = True
        else:
            print(f"ignoring line: {line}, basic block already terminated")

    def __repr__(self):
        return f"BB<{self.name}>"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name




class Expr:
    def __init__(self, name, t, const_value=None):
        self.name = name
        self.type = t
        self.const_value = const_value

    def get_name_or_value(self):
        if self.name is not None:
            return "%" + str(self.name)
        return str(self.const_value)

    def __repr__(self):
        if self.name is not None:
            return f"%{self.name}: {self.type}"
        return f"_: {self.type} = {self.const_value}"

