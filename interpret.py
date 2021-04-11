import xml.etree.ElementTree as ET
import argparse
import re
import sys
import os
from collections import deque

class System:
    
    def __init__(self):
        self.frames = Frames()
        self.datastack = DataStack()
        self.callstack = Stack()
        self.program = Program()
        self.instruction = Instruction()

    def run_interpret(self):
        while self.program.ptr_is_valid():
            instruction = self.program.instructions[self.program.instruction_ptr]
            self.instruction.opcode = instruction.attrib['opcode']
            self.instruction.parse_arguments(instruction)
            
            self.interpret_instruction()

            self.program.instruction_ptr += 1    

    def interpret_instruction(self):
        switcher = {
            "MOVE": i_move,
            "CREATEFRAME": i_createframe,
            "PUSHFRAME": i_pushframe,
            "POPFRAME": i_popframe,
            "DEFVAR": i_defvar,
            "CALL": i_call,
            "RETURN": i_return,
            "PUSHS": i_pushs,
            "POPS": i_pops,
            "ADD": i_add,
            "SUB": i_sub,
            "MUL": i_mul,
            "IDIV": i_idiv,
            "LT": i_lt,
            "GT": i_gt,
            "EQ": i_eq,
            "AND": i_and,
            "OR": i_or,
            "NOT": i_not,
            "INT2CHAR": i_int2char,
            "STRI2INT": i_stri2int,
            "READ": i_read,
            "WRITE": i_write,
            "CONCAT": i_concat,
            "STRLEN": i_strlen,
            "GETCHAR": i_getchar,
            "SETCHAR": i_setchar,
            "TYPE": i_type,
            "LABEL": i_label,
            "JUMP": i_jump,
            "JUMPIFEQ": i_jumpifeq,
            "JUMPIFNEQ": i_jumpifneq,
            "EXIT": i_exit,
            "DPRINT": i_dprint,
            "BREAK": i_break
        }
            
        function = switcher.get(self.instruction.opcode)
        if function:
            function(self)
        else:
            structure_error()

class Program:

    def __init__(self):
        self.instructions = []
        self.instruction_ptr = 0
        self.length = 0
        self.input = ""

    def ptr_is_valid(self):
        return 0 <= self.instruction_ptr < self.length

    def jump_to_label(self, name):
        label_found = False
        for instruction in self.instructions:
            if instruction.attrib["opcode"] == "LABEL":
                arguments = list(instruction)
                label_name = arguments[0].text
                if label_name == name:
                    label_found = True
                    self.instruction_ptr = self.instructions.index(instruction)
                    break
        if label_found == False:
            code_semantic_error()

class Instruction:

    def __init__(self):
        self.opcode = ""
        self.arguments = []

    def parse_arguments(self, instruction):
        self.arguments = []
        for argument in instruction:
            arg = ProgramData()
            arg.type = argument.attrib["type"]
            arg.value = argument.text
            arg.convert_type()
            self.arguments.append(arg)

class ProgramData:

    def __init__(self, data_type="", data_value=""):
        self.type = data_type
        self.value = data_value

    def convert_type(self):
        if self.type == "int":
            try:
                self.value = int(self.value)
            except:
                self.type = "nil"
                self.value = None
        elif self.type == "bool":
            if self.value.lower() == "true":
                self.value = True
            else:
                self.value = False
        elif self.type == "string":
            self.value = re.sub(r"\\(\d{3})", lambda x: chr(int(x.group()[1:])), self.value)
        elif self.type in ["var", "label", "type"]:
            self.type = self.type
        else:
            self.type = "nil"
            self.value = None

class Frames:

    def __init__(self):
        self.__stack = deque([{}])
        self.global_frame = self.__stack[0]
        self.local_frame = self.__stack[-1]
        self.tmp_frame = None

    def push_frame(self):
        self.__stack.append(self.tmp_frame)
        self.tmp_frame = None

    def pop_frame(self):
        try:
            self.tmp_frame = self.__stack.pop()
        except IndexError:
            frame_error()

    def create_tf(sefl):
        self.tmp_frame = {}

    def parse_var_string(self, var_string):
        frame, var_name = var_string.split("@")
        switcher = {
            "GF": self.global_frame,
            "LF": self.local_frame,
            "TF": self.tmp_frame
        }
        actual_frame = switcher.get(frame)
        
        if actual_frame == None:
            frame_error()
        return actual_frame, var_name

    def def_var(self, var_string):
        actual_frame, var_name = self.parse_var_string(var_string)

        if var_name in actual_frame:
            code_semantic_error()
        else:
            actual_frame[var_name] = ProgramData()

    def get_var(self, var_string):
        actual_frame, var_name = self.parse_var_string(var_string)

        if var_name in actual_frame:
            return actual_frame.get(var_name)
        else:
            variable_error()

    def update_var(self, var_string, var_type, var_value):
        actual_frame, var_name = self.parse_var_string(var_string)

        if var_name in actual_frame:
            actual_frame[var_name].type = var_type
            actual_frame[var_name].value = var_value
        else:
            variable_error()

class Stack:

    def __init__(self):
        self.stack = deque()

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        try:
            return self.stack.pop()
        except IndexError:
            missing_value_error()

class DataStack(Stack):

    def push(self, data_type, data_value):
        self.stack.append(ProgramData(data_type, data_value))

# instruction methods

def i_move(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    
    if arg2.type == "var":
        variable = system.frames.get_var(arg2.value)
        system.frames.update_var(arg1.value, variable.type, variable.value)
    else:
        system.frames.update_var(arg1.value, arg2.type, arg2.value)

def i_createframe(system):
    system.frames.create_tf()

def i_pushframe(system):
    system.frames.push_frame()

def i_popframe(system):
    system.frames.pop_frame()

def i_defvar(system):
    arg1 = system.instruction.arguments[0]
    system.frames.def_var(arg1.value)

def i_call(system):
    arg1 = system.instruction.arguments[0]
    
    system.callstack.push(system.program.instruction_ptr)
    system.program.jump_to_label(arg1.value)

def i_return(system):
    system.program.instruction_ptr = system.callstack.pop()

def i_pushs(system):
    arg1 = system.instruction.arguments[0]

    system.datastack.push(arg1.type, arg1.value)

def i_pops(system):
    arg1 = system.instruction.arguments[0]

    data = system.datastack.pop()
    system.frames.update_var(arg1, data.type, data.value)

def i_add(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]
    
    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == "int" and arg3.type == "int":
        result = arg2.value + arg3.value
        system.frames.update_var(arg1.value, "int", result)
    else:
        type_error()

def i_sub(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]
    
    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == "int" and arg3.type == "int":
        result = arg2.value - arg3.value
        system.frames.update_var(arg1.value, "int", result)
    else:
        type_error()

def i_mul(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == "int" and arg3.type == "int":
        result = arg2.value * arg3.value
        system.frames.update_var(arg1.value, "int", result)
    else:
        type_error()

def i_idiv(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == "int" and arg3.type == "int":
        try:    
            result = arg2.value // arg3.value
        except ZeroDivisionError:
            wrong_operand_error()
        system.frames.update_var(arg1.value, "int", result)
    else:
        type_error()

def i_lt(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type:
        try:
            result = arg2.value < arg3.value
        except TypeError:
            type_error()
        system.frames.update_var(arg1.value, "bool", result)
    else:
        type_error()

def i_gt(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type:
        try:
            result = arg2.value > arg3.value
        except TypeError:
            type_error()
        system.frames.update_var(arg1.value, "bool", result)
    else:
        type_error()

def i_eq(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type:
        try:
            result = arg2.value == arg3.value
        except TypeError:
            type_error()
        system.frames.update_var(arg1.value, "bool", result)
    else:
        type_error()

def i_and(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type == "bool":
        result = arg2.value and arg3.value
        system.frames.update_var(arg1.value, "bool", result)
    else:
        type_error()

def i_or(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type == "bool":
        result = arg2.value or arg3.value
        system.frames.update_var(arg1.value, "bool", result)
    else:
        type_error()

def i_not(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg2.type == "bool":
        result = not arg2.value
        system.frames.update_var(arg1.value, "bool", result)
    else:
        type_error()

def i_int2char(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg2.type == "int":
        try:
            result = chr(arg2.value)
        except ValueError:
            string_error()
        system.frames.update_var(arg1.value, "string", result)
    else:
        type_error()

def i_stri2int(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == "string" and arg3.type == "int":
        try:
            result = ord(arg2.value[arg3.value])
        except IndexError:
            string_error()
        system.frames.update_var(arg1.value, "int", result)
    else:
        type_error()

def i_read(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    data = ProgramData()
    data.type = arg2
    if system.program.input:
        try:
            data.value = system.program.input.popleft()
        except IndexError:
            data.type = "nil"
            data.value = "nil"
    else:
        data.value = input()  
    
    data.convert_type()
    system.frames.update_var(arg1.value, data.type, data.value)

def i_write(system):
    arg1 = system.instruction.arguments[0]

    if arg1.type == "var":
        arg1 = system.frames.get_var(arg1.value)
    if arg1.type == "bool":
        if arg1.value:
            print("true", end='')
        else:
            print("false", end='')
    elif arg1.type == "nil":
        print("", end='')
    else:
        print(arg1.value, end='')

def i_concat(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == "string" and arg3.type == "string":   
        result = arg2.value + arg3.value
        system.frames.update_var(arg1.value, "string", result)
    else:
        type_error()

def i_strlen(system):
    arg1 = system.instruction.arguments[0]

    if arg1.type == "var":
        arg1 = system.frames.get_var(arg1.value)
    if arg1.type == "string":
        result = len(arg1.value)
        system.frames.update_var(arg1.value, "int", result)
    else:
        type_error()
    

def i_getchar(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == "string" and arg3.type == "int":
        try:
            result = arg2.value[arg3.value]
        except IndexError:
            string_error()
        system.frames.update_var(arg1.value, "int", result)
    else:
        type_error()

def i_setchar(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == "int" and arg3.type == "string":
        arg1_string = system.frames.get_var(arg1.value).value
        try:
            arg1_string = list(arg1_string)
            arg1_string[arg2.value] = arg3.value[0]
            arg1_string = "".join(arg1_string)
        except IndexError:
            string_error()
        system.frames.update_var(arg1.value, "string", arg1_string)
    else:
        type_error()

def i_type(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    result = arg2.type
    system.frames.update_var(arg1.value, "bool", result)
    
def i_label(system):
    arg1 = system.instruction.arguments[0]

def i_jump(system):
    arg1 = system.instruction.arguments[0]

    system.program.jump_to_label(arg1.value)

def i_jumpifeq(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type:
        if arg2.value == arg3.value:
            jump_to_label(arg1.value)
    else:
        type_error()

def i_jumpifneq(system):
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type:
        if arg2.value != arg3.value:
            jump_to_label(arg1.value)
    else:
        type_error()    

def i_exit(system):
    
    arg1 = system.instruction.arguments[0]

    if arg1.type == "var":
        arg1 = system.frames.get_var(arg1.value)
    if arg1.type == "int":
        if 0 <= arg1.value <= 49:
            sys.exit(arg1.value)
        else:
            wrong_operand_error()
    else:
        type_error()

def i_dprint(system):
    arg1 = system.instruction.arguments[0]

    if arg1.type == "var":
        arg1 = system.frames.get_var(arg1.value)
    if arg1.type == "bool":
        if arg1.value:
            print("true", end='', file=sys.stderr)
        else:
            print("false", end='', file=sys.stderr)
    elif arg1.type == "nil":
        print("", end='', file=sys.stderr)
    else:
        print(arg1.value, end='', file=sys.stderr)

def i_break(system):
    actual_instruction = system.program.instructions[system.program.instruction_ptr]
    print("\n\nActual instruction number:", actual_instruction.attrib["order"], file=sys.stderr)
    print("Actual instruciton name:", actual_instruction.attrib["opcode"], file=sys.stderr)
    print("Actual content in frames:",
          "\n Global frame:\n", system.frames.global_frame,
          "\n\n Local frame:\n", system.frames.local_frame,
          "\n\n Temporary frame:\n", system.frames.tmp_frame,
          "\n", file=sys.stderr)

# error methods

def handle_get_error(opcode):
    print(f"get error {opcode}", file=sys.stderr)
    sys.exit(345)

def code_semantic_error():
    print("ERROR: semantic error in IPPcode", file=sys.stderr)
    sys.exit(52)

def type_error():
    print("ERROR: wrong type", file=sys.stderr)
    sys.exit(53)

def variable_error():
    print("ERROR: variabe not found", file=sys.stderr)
    sys.exit(54)

def frame_error():
    print("ERROR: frame doesn't exist", file=sys.stderr)
    sys.exit(55)

def missing_value_error():
    print("ERROR: value doesn't exist (or stack is empty)", file=sys.stderr)
    sys.exit(56)

def wrong_operand_error():
    print("ERROR: wrong operand (or zero division)", file=sys.stderr)
    sys.exit(57)    

def string_error():
    print("ERROR: invalid operation with string", file=sys.stderr)
    sys.exit(58)      

def parse_error():
    print("ERROR: invalid XML format", file=sys.stderr)
    sys.exit(31)

def structure_error():
    print("ERROR: invalid XML structure", file=sys.stderr)
    sys.exit(32)
    
def argument_error():
    print("ERROR: invalid file", file=sys.stderr)
    sys.exit(10)

def file_error():
    print("ERROR: invalid file", file=sys.stderr)
    sys.exit(11)

# script methods

def get_order(instruction):
    return int(instruction.attrib['order'])

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source=", dest="source")
    parser.add_argument("--input=", dest="input")
    args = parser.parse_args(sys.argv[1:])

    if not (args.source or args.input):
        argument_error()
    else:
        return args

def parse_souce(source_path):
    parsed_source = []
    
    try:
        if args.source:
            if os.path.isfile(args.source):
                parsed_source = ET.parse(args.source)
            else:
                sys.exit()
        else:
            parsed_source = ET.parse(sys.stdin)
    except SystemExit:
        file_error()
    except:
        parse_error()

    return parsed_source

def get_input(input_path):

    if args.input:
        try:
            f = open(args.input, "r")
            program_input = deque(f.read().splitlines())
            f.close()
        except OSError:
            file_error()
    else:
        program_input = None

    return program_input

# script

args = parse_arguments()
parsed_source = parse_souce(args.source)
program_input = get_input(args.input)

unsorted_program = parsed_source.getroot()
program = sorted(unsorted_program, key=get_order)


system = System()
system.program.instructions = list(program)
system.program.length = len(program)
system.program.input = program_input
system.run_interpret()
