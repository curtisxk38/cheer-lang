from typing import List

from cheer import visit, symbol_table, ir_helpers

from cheer import instructions as instr

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
        self.exp_stack: List[ir_helpers.Expr] = []
        self.symbol_table = st

        self.main = Function("main", "i32")
        bb = ir_helpers.BasicBlock("entry")
        self.main.basic_blocks.append(bb)

        self.scope_num = 0
        self.scope_stack: List[symbol_table.Scope] = []
        self.recent_scope = None # scope that was just left

        self.phi_stack: List[Phi] = []
        self.vars_used_in_while: List[symbol_table.STE] = None

    def default_in_visit(self, node):
        # override
        pass

    def default_out_visit(self, node):
        # override
        pass

    def get_code(self):
        return "\n".join(self.main.to_code())

    def add_line(self, instruction):
        self.main.basic_blocks[-1].add_instr(instruction)

    ###### STATEMENTS #######

    def _in_statement_list(self, node):
        new_scope = symbol_table.Scope(self.scope_num)
        self.scope_num += 1
        self.scope_stack.append(new_scope)

    def _out_statement_list(self, node):
        self.recent_scope = self.scope_stack.pop()

    def _visit_if_statement(self, node):
        # set up basic blocks
        if_body = ir_helpers.BasicBlock(f"if_taken{self.bb_num}")    
        if_else_end = ir_helpers.BasicBlock(f"if_else_end{self.bb_num}")

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
            else_body = ir_helpers.BasicBlock(f"else_taken{self.bb_num}")
            else_body.predecessors.add(start_basic_block)
            self.add_line(instr.ConditionalBranch(condition, if_body, else_body))
        else:
            if_else_end.predecessors.add(start_basic_block)
            self.add_line(instr.ConditionalBranch(condition, if_body, if_else_end))

        # needed so future if statement BBs to have unique names
        self.bb_num += 1

        # gen code for if taken body
        self.main.basic_blocks.append(if_body)
        self.visit_node(node.children[1])
        # if the if body contains a return statement
        #  then we don't need to end the basic block with a br
        if not if_body.returns:
            # gen last line of if_body basic block, to jump to next basic block
            self.add_line(instr.Branch(if_else_end))
            if_else_end.predecessors.add(if_body)

        # gen code for else
        if len(node.children) == 3:
            self.bb_num += 1

            # gen code for else taken body
            self.main.basic_blocks.append(else_body)
            self.visit_node(node.children[2])
            if not else_body.returns:
                # gen last line of else body bb, to jump to next bb
                self.add_line(instr.Branch(if_else_end))
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
                print(ste.ir_names)
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

                    self.add_line(instr.Phi(
                        self.reg_num, ste.node.type,
                        recent_ir_name, recent_bb,
                        next_ir_name, next_bb
                    ))
                    ste.assign_to_lexeme(self.main.basic_blocks[-1], self.reg_num)
                    self.reg_num += 1
                elif len(if_else_end.predecessors) == 1:
                    # need to update the ir name for this variable to
                    #  always be the ir var assigned to in the 1 predecessor
                    predecessor = list(if_else_end.predecessors)[0]
                    actual_ir_name = recent_ir_name if recent_bb == predecessor else next_ir_name
                    ste.assign_to_lexeme(predecessor, actual_ir_name)

    def _visit_while_statement(self, node):
        while_condition = ir_helpers.BasicBlock(f"while_con{self.bb_num}")    
        while_body = ir_helpers.BasicBlock(f"while_body{self.bb_num}")
        while_end = ir_helpers.BasicBlock(f"while_end{self.bb_num}")
        self.bb_num += 1

        # set up predecessors
        while_condition.predecessors.add(while_body)
        while_condition.predecessors.add(self.main.basic_blocks[-1])
        while_body.predecessors.add(while_condition)
        while_end.predecessors.add(while_condition)

        self.add_line(instr.Branch(while_condition))

        # gen code for while body
        # set up Phi statement for assignments in while body
        self.phi_stack.append(Phi())
        self.main.basic_blocks.append(while_body)
        self.visit_node(node.children[1])
        # jump to condition bb
        self.add_line(instr.Branch(while_condition))

        # gen code of while condition
        self.vars_used_in_while = []
        self.main.basic_blocks.append(while_condition)
        phi = self.phi_stack.pop()
        for lexeme, ste in phi.map.items():
            body_bb, body_ir = ste.ir_names.pop()
            entry_bb, entry_ir = ste.ir_names[-1]

            self.add_line(instr.Phi(
                        self.reg_num, ste.node.type,
                        entry_ir, entry_bb,
                        body_ir, body_bb
                    ))

            ste.assign_to_lexeme(self.main.basic_blocks[-1], self.reg_num)
            self.reg_num += 1

        self.visit_node(node.children[0])
        # condition expression var
        con_exp = self.exp_stack.pop()
        self.add_line(instr.ConditionalBranch(con_exp, while_body, while_end))
        
        self.vars_used_in_while = None

        # gen code for while end
        self.main.basic_blocks.append(while_end)


    def _out_return(self, node):
        op1 = self.exp_stack.pop()
        self.add_line(instr.Return(op1.type, op1))

    def _out_var_decl_assign(self, node):
        ste = self.symbol_table.get(node, self.scope_stack)
        op1 = self.exp_stack.pop()
        if op1.name is not None:
            ste.assign_to_lexeme(self.main.basic_blocks[-1], op1.name)
        else:
            # TODO fix this bs lol
            self.add_line(instr.Add(self.reg_num, op1.type, ir_helpers.Expr(None, "i32", 0), op1))
            ste.assign_to_lexeme(self.main.basic_blocks[-1], self.reg_num)
            self.reg_num += 1

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
        # assign to var declared in same scope
        elif ste.declared_scope == self.scope_stack[-1]:
            pass
        # ???
        else:
            raise ValueError("shouldn't be assigning to var declared in younger scope")

        if op1.name is not None:
            ste.assign_to_lexeme(self.main.basic_blocks[-1], op1.name)
        else:
            # TODO fix this bs lol
            self.add_line(instr.Add(self.reg_num, op1.type, ir_helpers.Expr(None, "i32", 0), op1))
            ste.assign_to_lexeme(self.main.basic_blocks[-1], self.reg_num)
            self.reg_num += 1

    def _out_var(self, node):
        ste = self.symbol_table.get(node, self.scope_stack)
        if self.main.basic_blocks[-1] == ste.ir_names[-1][0]:
            ir_name_to_use = ste.ir_names[-1][1]
        else:
            ir_name_to_use = None
            looking_at = self.main.basic_blocks[-1]
            while True:
                for basic_block, ir_name in ste.ir_names:
                    if basic_block in looking_at.predecessors:
                        ir_name_to_use = ir_name
                        break # break out of for
                if ir_name_to_use is not None:
                    break # break out of while
                # idk about this code
                # if looking_at doesn't have an entry in ir_names that matches it
                # which predecessor we go to next shouldn't matter
                # ex. looking_at has two predecessors. if either of those assigned to this ste,
                #  then looking_at would have had a phi statement and would have had an entry in ir_names
                looking_at = list(looking_at.predecessors)[0]

        try:
            self.exp_stack.append(ir_helpers.Expr(ir_name_to_use, node.type))
        except UnboundLocalError as e:
            print(node.symbol)
            print(ste.ir_names)
            print(self.main.basic_blocks)
            print(self.main.basic_blocks[-1].predecessors)

            raise e

        if self.vars_used_in_while is not None:
            self.vars_used_in_while.append(ste)

    ###### EXPRESSIONS #######

    def _out_int_literal(self, node):
        #self.add_line("%{} = alloca i32, align 4".format(self.reg_num))
        #self.add_line("store i32 {}, i32* %{}".format(node.symbol.value, self.reg_num))
        #self.reg_num += 1
        #self.add_line("%{} = load i32, i32* %{}, align 4".format(self.reg_num, self.reg_num - 1))
        self.exp_stack.append(ir_helpers.Expr(None, "i32", node.symbol.value))
        #self.reg_num += 1

    def _out_bool_literal(self, node):
        bool_value = 1 if node.symbol.value else 0
        #self.add_line("%{} = alloca i1, align 4".format(self.reg_num))
        #self.add_line("store i1 {}, i1* %{}".format(bool_value, self.reg_num))
        #self.reg_num += 1
        #self.add_line("%{} = load i1, i1* %{}, align 4".format(self.reg_num, self.reg_num - 1))
        self.exp_stack.append(ir_helpers.Expr(None, "i1", bool_value))
        #self.reg_num += 1

    def _out_equality_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line(instr.Compare(self.reg_num, "eq", op1, op2))
        self.exp_stack.append(ir_helpers.Expr(self.reg_num, "i1"))
        self.reg_num += 1

    def _out_less_than_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line(instr.Compare(self.reg_num, "slt", op1, op2))
        self.exp_stack.append(ir_helpers.Expr(self.reg_num, "i1"))
        self.reg_num += 1

    def _out_greater_than_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line(instr.Compare(self.reg_num, "sgt", op1, op2))
        self.exp_stack.append(ir_helpers.Expr(self.reg_num, "i1"))
        self.reg_num += 1

    def _out_plus_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line(instr.Add(self.reg_num, "i32", op1, op2))
        self.exp_stack.append(ir_helpers.Expr(self.reg_num, "i32"))
        self.reg_num += 1

    def _out_minus_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line(instr.Subtract(self.reg_num, "i32", op1, op2))
        self.exp_stack.append(ir_helpers.Expr(self.reg_num, "i32"))
        self.reg_num += 1

    def _out_times_exp(self, node):
        op2 = self.exp_stack.pop()
        op1 = self.exp_stack.pop()
        self.add_line(instr.Multiply(self.reg_num, "i32", op1, op2))
        self.exp_stack.append(ir_helpers.Expr(self.reg_num, "i32"))
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
        self.add_line(instr.Allocate(self.reg_num, "[2 x i8]", 1))
        self.reg_num += 1
        self.add_line(instr.GetElementPtr(reg_num, "[2 x i8]", self.reg_num - 1, 0, 0))
        self.reg_num += 1
        self.add_line(instr.CallAsm(self.reg_num, "i32", self.reg_num - 1))
        self.reg_num += 1
        self.add_line(instr.Load(self.reg_num, "i8", self.reg_num - 2, 1))
        self.reg_num += 1
        self.add_line(instr.SignExtend(self.reg_num, "i8", self.reg_num - 1, "i32"))
        self.exp_stack.append(ir_helpers.Expr(self.reg_num, "i32"))
        self.reg_num += 1