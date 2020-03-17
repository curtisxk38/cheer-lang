import visit

indent = "  "

class Module:
    def __init__(self):
        self.functions = []

    def to_code(self):
        lines = []
        for func in self.functions:
            lines.extend(func.to_code())
            lines.append("\n")
        return lines

class Function:
    def __init__(self, name, return_type):
        self.name = name
        self.return_type = return_type
        self.basic_blocks = []

    def to_code(self):
        lines = []
        lines.append("define {} @{}() {{".format(self.return_type, self.name))
        for block in self.basic_blocks:
            lines.extend(block.to_code())
        lines.append("}")
        return lines

class BasicBlock:
    def __init__(self, name):
        self.name = name
        self.lines = []

    def to_code(self):
        return self.lines

    def add_instr(self, line):
        self.lines.append(indent + line)

class CodeGenVisitor(visit.DFSVisitor):
    def __init__(self, ast):
        super().__init__(ast)
        self.reg_num = 1
        self.exp_stack = []

        self.main = Function("main", "i32")
        self.block = BasicBlock("entry")
        self.main.basic_blocks.append(self.block)

    def default_in_visit(self, node):
        # override
        pass

    def default_out_visit(self, node):
        # override
        pass

    def get_code(self):
        return "\n".join(self.main.to_code())

    def add_line(self, line):
        self.block.add_instr(line)

    def _out_int_literal(self, node):
        self.add_line("%{} = alloca i32, align 4".format(self.reg_num))
        self.add_line("store i32 {}, i32* %{}".format(node.symbol.value, self.reg_num))
        self.reg_num += 1
        self.add_line("%{} = load i32, i32* %{}, align 4".format(self.reg_num, self.reg_num - 1))
        self.exp_stack.append(self.reg_num)
        self.reg_num += 1

    def _out_plus_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line("%{} = add i32 %{}, %{}".format(self.reg_num, op1, op2))
        self.exp_stack.append(self.reg_num)
        self.reg_num += 1

    def _out_minus_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line("%{} = sub i32 %{}, %{}".format(self.reg_num, op1, op2))
        self.exp_stack.append(self.reg_num)
        self.reg_num += 1

    def _out_times_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line("%{} = mul i32 %{}, %{}".format(self.reg_num, op1, op2))
        self.exp_stack.append(self.reg_num)
        self.reg_num += 1

    def _out_return_exp(self, node):
        self.add_line("ret i32 %{}".format(self.reg_num - 1))

    def _out_input_exp(self, node):
        """
        gets one ASCII char from stdin
        returns ASCII value as i32

        the array allocated is 2 chars wide, so the terminal input enter
         becomes the second character. (if its only one wide, the behavior is weird)

        the get element ptr (GEP) calculates the address we want to load from
         we want to load the address of the 0th index (the actual char, not new line)

        define i32 @main() #0 {
          %1 = alloca [2 x i8], align 1
          %2 = getelementptr inbounds [2 x i8], [2 x i8]* %1, i32 0, i32 0
          %3 = call i32 asm sideeffect "movl $$0x00000000, %edi\0Amovl $$0x00000002, %edx\0Amovl $$0, %eax\0Asyscall\0A", "={ax},{si},~{dirflag},~{fpsr},~{flags}"(i8* %2)
          %5 = load i8, i8* %2, align 1
          %6 = sext i8 %5 to i32
          ret i32 %6
        }
        """
        self.add_line("%{} = alloca [2 x i8], align 1".format(self.reg_num))
        self.reg_num += 1
        self.add_line("%{} = getelementptr inbounds [2 x i8], [2 x i8]* %{}, i32 0, i32 0".format(self.reg_num, self.reg_num - 1))
        self.reg_num += 1
        self.add_line('%{} = call i32 asm sideeffect "movl $$0x00000000, %edi\\0Amovl $$0x00000002, %edx\\0Amovl $$0, %eax\\0Asyscall\\0A", "={{ax}},{{si}},~{{dirflag}},~{{fpsr}},~{{flags}}"(i8* %{})'.format(self.reg_num, self.reg_num - 1))
        self.reg_num += 1
        self.add_line("%{} = load i8, i8* %{}, align 1".format(self.reg_num, self.reg_num - 2))
        self.reg_num += 1
        self.add_line("%{} = sext i8 %{} to i32".format(self.reg_num, self.reg_num - 1))
        self.exp_stack.append(self.reg_num)
        self.reg_num += 1