from lxml import etree
import argparse
import re
import sys
import os
from io import StringIO
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
            
            self.instruction.load(instruction)
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
        self.labels = []

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
    
    def unique_arguments(self):
        if len() > len(set(self.arguments)):
            structure_error()

    def load(self, instruction):
        self.opcode = instruction.attrib['opcode']
        self.arguments = []
        instruction = list(instruction)
        instruction.sort(key=lambda arg: arg.tag)
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

    def convert_escaped_ascii(self):
        if self.value:
            self.value = re.sub(r"\\(\d{3})", lambda x: chr(int(x.group()[1:])), self.value)
        else: 
            self.value = ""

    def convert_type(self):
        if self.type == "int":
            try:
                self.value = int(self.value)
            except:
                structure_error()
        elif self.type == "bool":
            if self.value == "true":
                self.value = True
            elif self.value == "false":
                self.value = False
            else:
                structure_error()
        elif self.type == "string":
            self.convert_escaped_ascii()
        elif self.type == "var":
            if re.match("^(LF|GF|TF)@", self.value):
                self.convert_escaped_ascii()
            else:
                structure_error()
        elif self.type == "type":
            if not self.value in ["int", "string", "bool"]:
                structure_error()
        elif self.type == "label":
            self.type = self.type
        elif self.type == "nil":
            self.value = None
        else:
            structure_error()

class Frames:

    def __init__(self):
        self.global_frame = {}
        self.__local_frames = deque([])
        self.tmp_frame = None

    def get_local_frame(self):
        try:
            return self.__local_frames[-1]
        except IndexError:
            return None

    def push_frame(self):
        if self.tmp_frame != None:
            self.__local_frames.append(self.tmp_frame)
            self.tmp_frame = None
        else:
            frame_error()

    def pop_frame(self):
        try:
            self.tmp_frame = self.__local_frames.pop()
        except IndexError:
            frame_error()

    def create_tf(self):
        self.tmp_frame = {}

    def parse_var_string(self, var_string):
        frame, var_name = var_string.split("@")
        
        if frame == "GF":
            actual_frame = self.global_frame
        if frame == "LF":
            actual_frame = self.get_local_frame()
        if frame == "TF":
            actual_frame = self.tmp_frame
        
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
    if len(system.instruction.arguments) != 2:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 1:
        structure_error()
    arg1 = system.instruction.arguments[0]
    
    if arg1.type != "var":
        structure_error()
    system.frames.def_var(arg1.value)

def i_call(system):
    if len(system.instruction.arguments) != 1:
        structure_error()
    arg1 = system.instruction.arguments[0]

    if arg1.type != "label":
        structure_error()
    system.callstack.push(system.program.instruction_ptr)
    system.program.jump_to_label(arg1.value)

def i_return(system):
    system.program.instruction_ptr = system.callstack.pop()

def i_pushs(system):
    if len(system.instruction.arguments) != 1:
        structure_error()
    arg1 = system.instruction.arguments[0]

    system.datastack.push(arg1.type, arg1.value)

def i_pops(system):
    if len(system.instruction.arguments) != 1:
        structure_error()
    arg1 = system.instruction.arguments[0]

    if arg1.type != "var":
        structure_error()
    data = system.datastack.pop()
    system.frames.update_var(arg1.value, data.type, data.value)

def i_add(system):
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 2:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    if arg1.type != "var":
        structure_error()
    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg2.type == "bool":
        result = not arg2.value
        system.frames.update_var(arg1.value, "bool", result)
    else:
        type_error()

def i_int2char(system):
    if len(system.instruction.arguments) != 2:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 2:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    if arg1.type != "var" or arg2.type != "type":
        structure_error()
    data = ProgramData()
    data.type = arg2.value
    if system.program.input:
        try:
            data.value = system.program.input.popleft()
        except IndexError:
            data.type = "nil"
            data.value = None
    else:
        data.value = input()  

    if data.type == "int":
        try:
            data.value = int(data.value)
        except:
            data.type = "nil"
            data.value = None
    elif data.type == "bool":
        if data.value.lower() == "true":
            data.value = True
        else:
            data.value = False
    elif data.type == "string":
        data.convert_escaped_ascii()

    system.frames.update_var(arg1.value, data.type, data.value)

def i_write(system):
    if len(system.instruction.arguments) != 1:
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 2:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
        
    if arg1.type != "var":
        structure_error()
    if arg2.type == "var":
        arg2 = system.frames.get_var(arg1.value)
    if arg2.type == "string":
        result = len(arg2.value)
        system.frames.update_var(arg1.value, "int", result)
    else:
        type_error()
    

def i_getchar(system):
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "var":
        structure_error()
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
        except TypeError:
            type_error()
        system.frames.update_var(arg1.value, "string", arg1_string)
    else:
        type_error()

def i_type(system):
    if len(system.instruction.arguments) != 2:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]

    if arg1.type != "var":
        structure_error()
    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    result = arg2.type
    system.frames.update_var(arg1.value, "type", result)
    
def i_label(system):
    if len(system.instruction.arguments) != 1:
        structure_error()
    arg1 = system.instruction.arguments[0]
 
    if arg1.type != "label":
        structure_error()
    if not arg1.value in system.program.labels:
        system.program.labels.append(arg1.value)
    else:
        code_semantic_error()

def i_jump(system):
    if len(system.instruction.arguments) != 1:
        structure_error()
    arg1 = system.instruction.arguments[0]
        
    if arg1.type != "label":
        structure_error()
    system.program.jump_to_label(arg1.value)

def i_jumpifeq(system):
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "label":
        structure_error()
    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type:
        if arg2.value == arg3.value:
            system.program.jump_to_label(arg1.value)
    else:
        type_error()

def i_jumpifneq(system):
    if len(system.instruction.arguments) != 3:
        structure_error()
    arg1 = system.instruction.arguments[0]
    arg2 = system.instruction.arguments[1]
    arg3 = system.instruction.arguments[2]

    if arg1.type != "label":
        structure_error()
    if arg2.type == "var":
        arg2 = system.frames.get_var(arg2.value)
    if arg3.type == "var":
        arg3 = system.frames.get_var(arg3.value)
    if arg2.type == arg3.type:
        if arg2.value != arg3.value:
            system.program.jump_to_label(arg1.value)
    else:
        type_error()    

def i_exit(system):
    if len(system.instruction.arguments) != 1:
        structure_error()
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
    if len(system.instruction.arguments) != 1:
        structure_error()
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
          "\n\n Local frame:\n", system.frames.get_local_frame(), 
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
                parsed_source = etree.parse(args.source)
            else:
                sys.exit()
        else:
            parsed_source = etree.parse(sys.stdin)
    except SystemExit:
        file_error()
    except:
        parse_error()

    return parsed_source

def validate_source(parsed_source):
    schema = StringIO('''\
    <xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="program">
        <xs:complexType>
        <xs:sequence minOccurs="0">
            <xs:element maxOccurs="unbounded" name="instruction">
            <xs:complexType>
                <xs:all minOccurs="0" maxOccurs="1">
                <xs:element name="arg1">
                    <xs:complexType>
                    <xs:simpleContent>
                        <xs:extension base="xs:string">
                        <xs:attribute name="type" type="xs:string" use="required" />
                        </xs:extension>
                    </xs:simpleContent>
                    </xs:complexType>
                </xs:element>
                <xs:element minOccurs="0" name="arg2">
                    <xs:complexType>
                    <xs:simpleContent>
                        <xs:extension base="xs:string">
                        <xs:attribute name="type" type="xs:string" use="required" />
                        </xs:extension>
                    </xs:simpleContent>
                    </xs:complexType>
                </xs:element>
                <xs:element minOccurs="0" name="arg3">
                    <xs:complexType>
                    <xs:simpleContent>
                        <xs:extension base="xs:string">
                        <xs:attribute name="type" type="xs:string" use="required" />
                        </xs:extension>
                    </xs:simpleContent>
                    </xs:complexType>
                </xs:element>
                </xs:all>
                <xs:attribute name="order" type="xs:positiveInteger" use="required" />
                <xs:attribute name="opcode" type="xs:string" use="required" />
            </xs:complexType>
            </xs:element>
        </xs:sequence>
        <xs:attribute name="language" type="xs:string" use="required" />
        <xs:attribute name="name" type="xs:string" use="optional" />
        <xs:attribute name="description" type="xs:string" use="optional" />
        </xs:complexType>
        <xs:unique name="UniqueOrder">
            <xs:selector xpath="instruction" /> 
            <xs:field xpath="@order" /> 
        </xs:unique>
    </xs:element>
    </xs:schema>
    ''')
    parsed_schema = etree.parse(schema)
    xmlschema = etree.XMLSchema(parsed_schema)
    if not xmlschema.validate(parsed_source):
        print(xmlschema.error_log.last_error, file=sys.stderr)
        structure_error()

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

validate_source(parsed_source)
unsorted_program = parsed_source.getroot()
program = sorted(unsorted_program, key=get_order)


system = System()
system.program.instructions = list(program)
system.program.length = len(program)
system.program.input = program_input
system.run_interpret()
