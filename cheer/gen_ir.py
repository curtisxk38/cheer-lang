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
        self.returns = False
        self.predecessors = set()

    def to_code(self):
        return self.lines

    def add_instr(self, line):
        if not self.terminated:
            self.lines.append(indent + line)
            if line.startswith("ret"):
                self.terminated = True
                self.returns = True
            if line.startswith("br"):
                self.terminated = True
        else:
            print(f"ignoring line: {line}, basic block already terminated")

    def __repr__(self):
        return f"BB<{self.name}>"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


class Var:
    def __init__(self, name, t):
        self.name = name
        self.type = t


class Phi:
    def __init__(self):
        self.map: Dict[str, symbol_table.STE] = {}

    def __repr__(self):
        return str(self.map)


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
        self.recent_scope = None # scope that was just left

        self.phi_stack = []

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
        self.recent_scope = self.scope_stack.pop()

    def _visit_if_statement(self, node):
        # set up basic blocks
        if_body = BasicBlock(f"if_taken{self.bb_num}")    
        if_else_end = BasicBlock(f"if_else_end{self.bb_num}")

        # set up Phi statement for assignments in condition body(ies)
        self.phi_stack.append(Phi())

        # keep track
        start_basic_block = self.main.basic_blocks[-1]

        if_body.predecessors.add(start_basic_block)
        
        # first gen code for the condition
        self.visit_node(node.children[0])
        # gen code conditional branch
        condition = self.exp_stack.pop()
        if len(node.children) == 3:
            else_body = BasicBlock(f"else_taken{self.bb_num}")
            else_body.predecessors.add(start_basic_block)
            self.add_line(f"br i1 %{condition.name}, label %{if_body.name}, label %{else_body.name}")
        else:
            if_else_end.predecessors.add(start_basic_block)
            self.add_line(f"br i1 %{condition.name}, label %{if_body.name}, label %{if_else_end.name}")

        # needed so future if statement BBs to have unique names
        self.bb_num += 1

        # gen code for if taken body
        self.main.basic_blocks.append(if_body)
        self.visit_node(node.children[1])
        # if the if body contains a return statement
        #  then we don't need to end the basic block with a br
        if not if_body.returns:
            # gen last line of if_body basic block, to jump to next basic block
            self.add_line(f"br label %{if_else_end.name}")
            if_else_end.predecessors.add(if_body)

        # gen code for else
        if len(node.children) == 3:
            self.bb_num += 1

            # gen code for else taken body
            self.main.basic_blocks.append(else_body)
            self.visit_node(node.children[2])
            if not else_body.returns:
                # gen last line of else body bb, to jump to next bb
                self.add_line(f"br label %{if_else_end.name}")
                if_else_end.predecessors.add(else_body)

        # if the if body and else body
        # ex:
        # fn main() {
        #   if (true) { return true; }
        #   else { return false; }
        # }
        # we don't want another basic block after the else one

        # is there any code needed after the if-else statement?
        nothing_after_if_else = len(node.children) == 3 \
            and if_body.returns and else_body.returns

        if not nothing_after_if_else:
            self.main.basic_blocks.append(if_else_end)
            # lets deal with the phi
            phi = self.phi_stack.pop()
            for lexeme, ste in phi.map.items():
                recent_bb, recent_ir_name = ste.ir_names.pop()
                if ste.ir_names[-1][0] == if_body:
                    _, next_ir_name = ste.ir_names.pop()
                else:
                    _, next_ir_name = ste.ir_names[-1]
                
                # need to gen phi code
                if len(if_else_end.predecessors) > 1:
                    # some weird shit to figure out which basic block
                    #  should be in the phi statement
                    # (based on the previously set predecessors)
                    predecessors = if_else_end.predecessors.copy()
                    predecessors.remove(recent_bb)
                    predecessors = list(predecessors)
                    if len(predecessors) > 1:
                        raise ValueError(f"predecessors should be 2")
                    next_bb = predecessors[0]

                    phi_code = "%{} = phi {} [%{}, %{}], [%{}, %{}]".format(
                            self.reg_num,
                            ste.node.type,
                            recent_ir_name, recent_bb.name,
                            next_ir_name, next_bb.name
                        )

                    self.add_line(phi_code)
                    ste.assign_to_lexeme(self.main.basic_blocks[-1], self.reg_num)
                    self.reg_num += 1
                elif len(if_else_end.predecessors) == 1:
                    # need to update the ir name for this variable to
                    #  always be the ir var assigned to in the 1 predecessor
                    predecessor = list(if_else_end.predecessors)[0]
                    actual_ir_name = recent_ir_name if recent_bb == predecessor else next_ir_name
                    ste.assign_to_lexeme(predecessor, actual_ir_name)

    def _out_return(self, node):
        op1 = self.exp_stack.pop()
        self.add_line(f"ret {op1.type} %{op1.name}")

    def _out_var_decl_assign(self, node):
        ste = self.symbol_table.get(node, self.scope_stack)
        ste.assign_to_lexeme(self.main.basic_blocks[-1], self.exp_stack[-1].name)

    def _visit_assignment(self, node):
        # visit rhs (expression)
        self.visit_node(node.children[1])
        # ste for lhs
        ste = self.symbol_table.get(node.children[0], self.scope_stack)
        op1 = self.exp_stack[-1]

        # figure out if we're assigning to variable declared in a parent scope
        # we can guarantee that child scope has higher scope_num than parent scope
        if ste.declared_scope < self.scope_stack[-1]:
            # if so, need to generate phi statement
            # since we are in a conditional scope (if/else) and assigning
            phi = self.phi_stack[-1]
            phi.map[ste.node.symbol.lexeme] = ste
            ste.assign_to_lexeme(self.main.basic_blocks[-1], op1.name)
        # assign to var declared in same scope
        elif ste.declared_scope == self.scope_stack[-1]:
            ste.assign_to_lexeme(self.main.basic_blocks[-1], op1.name)
        # ???
        else:
            raise ValueError("shouldn't be assigning to var declared in younger scope")

    def _out_var(self, node):
        ste = self.symbol_table.get(node, self.scope_stack)
        if self.main.basic_blocks[-1] == ste.ir_names[-1][0]:
            ir_name_to_use = ste.ir_names[-1][1]
        else:
            for basic_block, ir_name in ste.ir_names:
                if basic_block in self.main.basic_blocks[-1].predecessors:
                    ir_name_to_use = ir_name
                    break
        try:
            self.exp_stack.append(Var(ir_name_to_use, node.type))
        except UnboundLocalError as e:
            print(node.symbol)
            print(ste.ir_names)
            print(self.main.basic_blocks)
            print(self.main.basic_blocks[-1].predecessors)

            raise e

    ###### EXPRESSIONS #######

    def _out_int_literal(self, node):
        self.add_line("%{} = alloca i32, align 4".format(self.reg_num))
        self.add_line("store i32 {}, i32* %{}".format(node.symbol.value, self.reg_num))
        self.reg_num += 1
        self.add_line("%{} = load i32, i32* %{}, align 4".format(self.reg_num, self.reg_num - 1))
        self.exp_stack.append(Var(self.reg_num, "i32"))
        self.reg_num += 1

    def _out_bool_literal(self, node):
        bool_value = 1 if node.symbol.value else 0
        self.add_line("%{} = alloca i1, align 4".format(self.reg_num))
        self.add_line("store i1 {}, i1* %{}".format(bool_value, self.reg_num))
        self.reg_num += 1
        self.add_line("%{} = load i1, i1* %{}, align 4".format(self.reg_num, self.reg_num - 1))
        self.exp_stack.append(Var(self.reg_num, "i1"))
        self.reg_num += 1

    def _out_equality_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line(f"%{self.reg_num} = icmp eq i32 %{op1.name}, %{op2.name}")
        self.exp_stack.append(Var(self.reg_num, "i1"))
        self.reg_num += 1

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