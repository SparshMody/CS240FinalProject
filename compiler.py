memoryAddress = 5000
tRegister = 0
vars = dict()

def getInstructionLine(varName):
    global memoryAddress, tRegister
    tRegisterName = f"$t{tRegister}"
    setVariableRegister(varName, tRegisterName)
    result = f"addi {tRegisterName}, $zero, {memoryAddress}"
    tRegister += 1
    memoryAddress += 4
    return result

def setVariableRegister(varName, tRegister):
    global vars
    vars[varName] = tRegister

def getVariableRegister(varName):
    global vars
    return vars.get(varName, "ERROR")

def getAssignmentLinesImmediateValue(val, varName):
    global tRegister
    return f"""addi $t{tRegister}, $zero, {val}
sw $t{tRegister}, 0({getVariableRegister(varName)})""" + "\n"

def getAssignmentLinesVariable(varSource, varDest):
    global tRegister
    registerSource = getVariableRegister(varSource)
    registerDest = getVariableRegister(varDest)
    return f"""lw $t{tRegister}, 0({registerSource})
sw $t{tRegister}, 0({registerDest})""" + "\n"

def getArithmeticAssignment(line):
    global tRegister
    varName, _, expr = line.partition("=")
    varName = varName.strip()
    expr = expr.strip().strip(";")
    
    if "+" in expr:
        left, right = expr.split("+")
        op = "add"
    elif "-" in expr:
        left, right = expr.split("-")
        op = "sub"
    elif "*" in expr:
        left, right = expr.split("*")
        op = "mul"
    elif "/" in expr:
        left, right = expr.split("/")
        op = "div"
    else:
        return ""

    left, right = left.strip(), right.strip()

    code = ""
    code += f"lw $t{tRegister}, 0({getVariableRegister(left)})\n"
    code += f"lw $t{tRegister+1}, 0({getVariableRegister(right)})\n"
    code += f"{op} $t{tRegister+2}, $t{tRegister}, $t{tRegister+1}\n"
    code += f"sw $t{tRegister+2}, 0({getVariableRegister(varName)})\n"
    tRegister += 3
    return code

def getIfStatement(expr):
    global tRegister
    expr = expr.strip("(){")
    if "<" in expr:
        left, right = expr.split("<")
        op = "slt"
    elif ">" in expr:
        left, right = expr.split(">")
        op = "sgt"
    elif "==" in expr:
        left, right = expr.split("==")
        op = "seq"
    else:
        return "// Unsupported if"

    left, right = left.strip(), right.strip()
    code = ""
    code += f"lw $t{tRegister}, 0({getVariableRegister(left)})\n"
    code += f"lw $t{tRegister+1}, 0({getVariableRegister(right)})\n"
    code += f"{op} $t{tRegister+2}, $t{tRegister}, $t{tRegister+1}\n"
    code += f"beq $t{tRegister+2}, $zero, AFTER\n"
    tRegister += 3
    return code

def compile_c_to_asm(filename):
    global tRegister
    with open(filename, "r") as f:
        lines = f.readlines()

    output = ""

    for line in lines:
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("int "):
            _, var = line.split()
            var = var.strip(";")
            output += getInstructionLine(var) + "\n"
        elif line.startswith("if "):
            output += getIfStatement(line) + "\n"
        elif "=" in line:
            varName, _, expr = line.partition("=")
            varName = varName.strip()
            expr = expr.strip().strip(";")
            if any(op in expr for op in "+-*/"):
                output += getArithmeticAssignment(line)
            elif expr.isdigit():
                output += getAssignmentLinesImmediateValue(expr, varName)
                tRegister += 1
            else:
                output += getAssignmentLinesVariable(expr, varName)
        elif line.startswith("}"):
            output += "AFTER:\n"
        else:
            pass

    with open("output.asm", "w") as out:
        out.write(output)

if __name__ == "__main__":
    compile_c_to_asm("program.c")
