tRegister = 0
vars = {}

def getNextTRegister():
    global tRegister
    reg = f"$t{tRegister}"
    tRegister = (tRegister + 1) % 8
    return reg

def setVariableRegister(varName, reg):
    vars[varName] = reg

def getVariableRegister(varName):
    return vars.get(varName, "ERROR")

def getDeclarationLine(varName):
    reg = getNextTRegister()
    setVariableRegister(varName, reg)
    return f"# reserve {varName} in {reg}"


def getAssignment(val, varName):
    reg = getVariableRegister(varName)
    if val.isdigit():
        return f"loadi {reg}, {val}\nstorei {reg}, {varName}"
    elif "%" in val:
        a, b = val.split("%")
        a = a.strip()
        b = b.strip()
        r1 = getNextTRegister()
        r2 = getNextTRegister()
        r3 = getVariableRegister(varName)
        return (
            f"loadi {r1}, {a}\n"
            f"loadi {r2}, {b}\n"
            f"MOD {r3}, {r1}, {r2}\n"
            f"storei {r3}, {varName}"
        )
    else:
        src = getVariableRegister(val)
        temp = getNextTRegister()
        return f"loadi {temp}, {val}\nstorei {temp}, {varName}"

def parse_condition(expr):
    # Supported: a % b == 0, a == b, a != b, a < b, a > b
    tokens = expr.replace("(", "").replace(")", "").split()
    if "%" in expr:
        # example: i % 3 == 0
        a, _, b, op, c = tokens
        r1 = getNextTRegister()
        r2 = getNextTRegister()
        r3 = getNextTRegister()
        code = [
            f"loadi {r1}, {a}",
            f"loadi {r2}, {b}",
            f"MOD {r3}, {r1}, {r2}"
        ]
        if op == "==":
            code.append(f"BNE {r3}, $zero, SKIP")
        elif op == "!=":
            code.append(f"BEQ {r3}, $zero, SKIP")
        return code
    elif len(tokens) == 3:
        a, op, b = tokens
        r1 = getNextTRegister()
        r2 = getNextTRegister()
        r3 = getNextTRegister()
        code = [
            f"loadi {r1}, {a}",
            f"loadi {r2}, {b}"
        ]
        if op == "==":
            code += [f"SUB {r3}, {r1}, {r2}", f"BNE {r3}, $zero, SKIP"]
        elif op == "!=":
            code += [f"SUB {r3}, {r1}, {r2}", f"BEQ {r3}, $zero, SKIP"]
        elif op == "<":
            code += [f"LT {r3}, {r1}, {r2}", f"BEQ {r3}, $zero, SKIP"]
        elif op == ">":
            code += [f"GT {r3}, {r1}, {r2}", f"BEQ {r3}, $zero, SKIP"]
        return code
    else:
        return [f"# Unsupported condition: {expr}"]

# Main logic
with open("main.c", "r") as f:
    lines = [line.strip() for line in f.readlines()]

outputText = ""
i = 0
loop_id = 0
while i < len(lines):
    line = lines[i]

    if line.startswith("int "):
        line = line.replace("int", "").replace(";", "").strip()
        if "=" in line:
            varName, val = [v.strip() for v in line.split("=")]

            # Handle immediate shifts: 2 << 2, 4 >> 1
            if "<<" in val:
                lhs, rhs = [v.strip() for v in val.split("<<")]
                reg1 = getNextTRegister()
                reg2 = getNextTRegister()
                dest = getNextTRegister()
                setVariableRegister(varName, dest)
                outputText += (
                    f"loadi {reg1}, {lhs}\n"
                    f"shiftleft {reg2}, {reg1}, {rhs}\n"
                    f"storei {reg2}, {varName}\n"
                )
            elif ">>" in val:
                lhs, rhs = [v.strip() for v in val.split(">>")]
                reg1 = getNextTRegister()
                reg2 = getNextTRegister()
                dest = getNextTRegister()
                setVariableRegister(varName, dest)
                outputText += (
                    f"loadi {reg1}, {lhs}\n"
                    f"shiftright {reg2}, {reg1}, {rhs}\n"
                    f"storei {reg2}, {varName}\n"
                )
            elif val.isdigit():
                reg = getNextTRegister()
                setVariableRegister(varName, reg)
                outputText += f"loadi {reg}, {val}\nstorei {reg}, {varName}\n"

    elif "=" in line and not line.startswith("for"):
        parts = line.strip(";").split("=")
        varName = parts[0].strip()
        val = parts[1].strip()
        if "<<" in val:
            lhs, amt = [v.strip() for v in val.split("<<")]
            src_reg = getVariableRegister(lhs)
            dst_reg = getVariableRegister(varName)
            outputText += f"shiftleft {dst_reg}, {src_reg}, {amt}\nstorei {dst_reg}, {varName}\n"
        elif ">>" in val:
            lhs, amt = [v.strip() for v in val.split(">>")]
            src_reg = getVariableRegister(lhs)
            dst_reg = getVariableRegister(varName)
            outputText += f"shiftright {dst_reg}, {src_reg}, {amt}\nstorei {dst_reg}, {varName}\n"
        elif val.isdigit():
            outputText += getAssignment(val, varName) + "\n"
        else:
            outputText += getAssignment(val, varName) + "\n"
        outputText += getAssignment(val, var) + "\n"
        outputText += label + ":\n"
        outputText += "\n".join(parse_condition(cond.strip())) + "\n"

    elif line.startswith("if"):
        expr = line[2:].strip("() {")
        outputText += "\n".join(parse_condition(expr.strip())) + "\n"

    elif line.startswith("else if"):
        outputText += "SKIP:\n"
        expr = line[8:].strip("() {")
        outputText += "\n".join(parse_condition(expr.strip())) + "\n"

    elif line.startswith("else"):
        outputText += "SKIP:\n"

    elif "printf(" in line:
        content = line.strip(";").split("printf(")[1].rstrip(")")
        if '"' in content:
            text = content.replace('"', '').strip()
            outputText += f"print {text}\n"
        else:
            outputText += f"print {content.strip()}\n"

    elif line.startswith("}"):
        outputText += "JUMP " + label + "\n"
        outputText += "SKIP:\n"
        outputText += end_label + ":\n"

    i += 1

# Write output
with open("output.asm", "w") as f:
    f.write(outputText)

print("✔ Wrote output.asm")
