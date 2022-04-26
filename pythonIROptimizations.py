from pythonConstantFolding import ConstantFolding

class IROptimizer(object):

    def __init__(self, IR_lst, st):
        self.constantFoldingOptimizer = ConstantFolding(IR_lst, st)

    def do_constant_folding(self):
        return self.constantFoldingOptimizer.do_constant_folding()
