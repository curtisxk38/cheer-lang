from cheer import visit


class TCVisitor(visit.DFSVisitor):
    def __init__(self, ast):
        super().__init__(ast)
        self.symbol_table = []

    def type_check(self):
        self.accept()

    def default_in_visit(self, node):
        # override
        pass

    def default_out_visit(self, node):
        # override
        pass