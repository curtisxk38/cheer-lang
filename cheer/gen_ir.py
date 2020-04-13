from typing import List

from cheer import visit, symbol_table

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
        for index, block in enumerate(self.basic_blocks):
            lines.extend(block.to_code())
            if index < len(self.basic_blocks) - 1:
                lines.append("")
        lines.append("}")
        return lines


class BasicBlock:
    def __init__(self, name):
        self.name = name
        self.lines = []
        self.lines.append(f"{name}:")
        self.terminated = False

    def to_code(self):
        return self.lines

    def add_instr(self, line):
        if not self.terminated:
            self.lines.append(indent + line)
            if line.startswith("ret") or line.startswith("br"):
                self.terminated = True
        else:
            print(f"ignoring line: {line}, basic block already terminated")


class Var:
    def __init__(self, name, t):
        self.name = name
        self.type = t


class CodeGenVisitor(visit.DFSVisitor):
    def __init__(self, ast, st):
        super().__init__(ast)
        self.reg_num = 0
        self.bb_num = 1
        self.exp_stack: List[Var] = []
        self.symbol_table = st

        self.main = Function("main", "i32")
        bb = BasicBlock("entry")
        self.main.basic_blocks.append(bb)

        self.scope_num = 0
        self.scope_stack: List[symbol_table.Scope] = []

    def default_in_visit(self, node):
        # override
        pass

    def default_out_visit(self, node):
        # override
        pass

    def get_code(self):
        return "\n".join(self.main.to_code())

    def add_line(self, line):
        self.main.basic_blocks[-1].add_instr(line)

    ###### STATEMENTS #######

    def _in_statement_list(self, node):
        new_scope = symbol_table.Scope(self.scope_num)
        self.scope_num += 1
        self.scope_stack.append(new_scope)

    def _out_statement_list(self, node):
        self.scope_stack.pop()

    def _visit_if_statement(self, node):
        # set up basic blocks
        if_body = BasicBlock(f"if_taken{self.bb_num}")    
        self.bb_num += 1
        if_else_end = BasicBlock(f"if_else_end{self.bb_num}")
        self.bb_num += 1
        
        # first gen code for the condition
        self.visit_node(node.children[0])
        # gen code conditional branch
        condition = self.exp_stack.pop()
        if len(node.children) == 3:
            else_body = BasicBlock(f"else_taken{self.bb_num}")
            block_after_if_body = else_body
        else:
            block_after_if_body = if_else_end
        self.add_line(f"br i1 %{condition.name}, label %{if_body.name}, label %{block_after_if_body.name}")

        # gen code for if taken body
        self.main.basic_blocks.append(if_body)
        self.visit_node(node.children[1])
        # gen last line of if_body basic block, to jump to next basic block
        self.add_line(f"br label %{if_else_end.name}")

        # gen code for else
        if len(node.children) == 3:
            self.bb_num += 1

            # gen code for else taken body
            self.main.basic_blocks.append(else_body)
            self.visit_node(node.children[2])
            # gen last line of else body bb, to jump to next bb
            self.add_line(f"br label %{if_else_end.name}")

        # is this if-else statment the last in a statement list?
        last_statement = node.parent.ntype == "statement_list" and \
            node.parent.children[-1] is node
        if not last_statement:
            self.main.basic_blocks.append(if_else_end)

    def _out_return(self, node):
        op1 = self.exp_stack.pop()
        self.add_line(f"ret {op1.type} %{op1.name}")

    def _out_var_decl_assign(self, node):
        ste = self.symbol_table.get(node, self.scope_stack)
        op1 = self.exp_stack.pop()
        ste.ir_name = op1.name
        self.exp_stack.append(op1)

    def _visit_assignment(self, node):
        # visit rhs (expression)
        self.visit_node(node.children[1])
        # ste for lhs
        ste = self.symbol_table.get(node.children[0], self.scope_stack)
        op1 = self.exp_stack.pop()
        ste.ir_name = op1.name
        self.exp_stack.append(op1)

    def _out_var(self, node):
        ste = self.symbol_table.get(node, self.scope_stack)
        self.exp_stack.append(Var(ste.ir_name, node.type))

    ###### EXPRESSIONS #######

    def _out_int_literal(self, node):
        self.add_line("%{} = alloca i32, align 4".format(self.reg_num))
        self.add_line("store i32 {}, i32* %{}".format(node.symbol.value, self.reg_num))
        self.reg_num += 1
        self.add_line("%{} = load i32, i32* %{}, align 4".format(self.reg_num, self.reg_num - 1))
        self.exp_stack.append(Var(self.reg_num, "i32"))
        self.reg_num += 1

    def _out_equality_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line(f"%{self.reg_num} = icmp eq i32 %{op1.name}, %{op2.name}")
        self.exp_stack.append(Var(self.reg_num, "i1"))
        self.reg_num += 1
        #self.add_line(f"%{self.reg_num} = zext i1 %{self.reg_num - 1} to i32")
        
        #self.reg_num += 1

    def _out_plus_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line("%{} = add i32 %{}, %{}".format(self.reg_num, op1.name, op2.name))
        self.exp_stack.append(Var(self.reg_num, "i32"))
        self.reg_num += 1

    def _out_minus_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line("%{} = sub i32 %{}, %{}".format(self.reg_num, op1.name, op2.name))
        self.exp_stack.append(Var(self.reg_num, "i32"))
        self.reg_num += 1

    def _out_times_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line("%{} = mul i32 %{}, %{}".format(self.reg_num, op1.name, op2.name))
        self.exp_stack.append(Var(self.reg_num, "i32"))
        self.reg_num += 1

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
        self.exp_stack.append(Var(self.reg_num, "i32"))
        self.reg_num += 1