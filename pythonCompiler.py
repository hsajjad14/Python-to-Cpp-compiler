import argparse
from pythonParser import pythonParser
from pythonAST import Node, visit
from pythonST import first_pass, second_pass
from pythonTypeChecker import TypeChecker
from pythonTAC import IRGen
from pythonTargetCodeGenerator import TargetCodeGenerator
from pythonIROptimizations import IROptimizer


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description='Take in the python source code and compile it')
    argparser.add_argument('FILE', help="Input file")
    argparser.add_argument('-a', '--print-ast', action='store_true', help="Print AST Nodes")
    argparser.add_argument('-p', '--parse-only', action='store_true', help="Stop after scanning and parsing the input")
    argparser.add_argument('-t', '--typecheck-only', action='store_true', help="Stop after typechecking")
    argparser.add_argument('-v', '--verbose', action='store_true', help="Provides additional output")
    args = argparser.parse_args()

    # Prints additional output if the flag is set
    if args.verbose:
        print("* Reading file " + args.FILE + "...")

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()

    if args.verbose:
        print("* Scanning and Parsing...")

    # Build and runs the parser to get AST
    parser = pythonParser()
    parser.build()
    result = parser.parse(data)


    # Use the default visitor (from W5) to go through the AST and print them
    # if the user provdes '--print-ast' flag
    if args.print_ast:
        print("======= AST START =======")
        visit(result)
        print("======= AST END =======\n")

    # If user asks to quit after parsing, do so.
    if args.parse_only:
        quit()

    if args.verbose:
        print("* Typechecking...")


    print("======= BUILD SYMBOL TABLE =======")
    st = first_pass(result)
    second_pass(result, [st])
    print(st)
    print("======= BUILD SYMBOL TABLE =======\n")

    print("======= AST WITH TYPES =======")
    visit(result)
    print("======= AST WITH TYPES =======\n")


    print("======= TypeChecking =======")
    typechecker = TypeChecker()
    tc = typechecker.typecheck(result, st)
    # print("Final typechecking = ", tc)
    print("======= TypeChecking =======")

    print("============ IR ============")
    ir_gen = IRGen()
    ir_gen.generate(result)
    ir_gen.print_ir()
    print("============ IR ============")

    print("============ IR Optimizations ============")
    ir_optimizer = IROptimizer(ir_gen.IR_lst, st)
    new_IR_lst = ir_optimizer.do_constant_folding()
    for line in new_IR_lst:
        print(line.value)
    print("============ IR Optimizations ============")


    print("============ TARGET CODE ============")
    cpp_generator = TargetCodeGenerator(new_IR_lst, st, result)
    cpp_generator.generate()
    cpp_generator.printTargetCode()
    print("============ TARGET CODE ============")
