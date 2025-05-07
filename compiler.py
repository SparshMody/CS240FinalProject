#!/usr/bin/env python3
import re, sys

# ─── Globals ────────────────────────────────────────────────────────────────
vars_        = set()
reg_counter  = 0                      # cycle through $t0–$t7

def next_reg():
    global reg_counter
    r = f"$t{reg_counter}"
    reg_counter = (reg_counter + 1) & 7
    return r

# ─── Helper: load constant or variable into a fresh register ───────────────
def load(val):
    r = next_reg()
    if val.isdigit():
        return [f"loadi {r}, {val}"], r
    return [f"loadi {r}, {val}"], r             # treat val as variable name

# ─── Build code for  var = expr  (now supports <<  >>) ─────────────────────
def handle_assignment(var, expr):
    out = []

    # Shift-left  (A << imm)
    m = re.match(r'(.+?)<<(.*)', expr)
    if m:
        left, amt = m.group(1).strip(), m.group(2).strip()
        code_src, r_src = load(left)
        r_dst = next_reg()
        out += code_src + [f"shiftleft {r_dst}, {r_src}, {amt}",
                           f"storei {r_dst}, {var}"]
        return out

    # Shift-right (A >> imm)
    m = re.match(r'(.+?)>>(.*)', expr)
    if m:
        left, amt = m.group(1).strip(), m.group(2).strip()
        code_src, r_src = load(left)
        r_dst = next_reg()
        out += code_src + [f"shiftright {r_dst}, {r_src}, {amt}",
                           f"storei {r_dst}, {var}"]
        return out

    # Arithmetic + - * /
    m = re.match(r'(.+?)([+\-*/])(.+)', expr)
    if m:
        lhs, op, rhs = m.group(1).strip(), m.group(2), m.group(3).strip()
        opmap = {"+":"ADD","-":"SUB","*":"MUL","/":"DIV"}
        c1,r1 = load(lhs)
        c2,r2 = load(rhs)
        r3    = next_reg()
        out += c1 + c2 + [f"{opmap[op]} {r3}, {r1}, {r2}",
                          f"storei {r3}, {var}"]
        return out

    # Immediate or var copy
    c,r = load(expr)
    out += c + [f"storei {r}, {var}"]
    return out

# ─── Very small C subset compiler (for the 2 demo programs) ────────────────
def compile_simple(lines):
    out=[]
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("//"): continue

        # int x = VAL;
        m = re.match(r'int\s+(\w+)\s*=\s*([^;]+);', line)
        if m:
            var, expr = m.groups()
            vars_.add(var)
            out += handle_assignment(var, expr)
            continue

        # int x;
        m = re.match(r'int\s+(\w+)\s*;', line)
        if m:
            vars_.add(m.group(1))
            continue

        # assignment or math / shift
        m = re.match(r'(\w+)\s*=\s*([^;]+);', line)
        if m:
            var, expr = m.groups()
            vars_.add(var)
            out += handle_assignment(var, expr)
            continue

        # print(var);
        m = re.match(r'print\s*\(\s*(\w+)\s*\)\s*;', line)
        if m:
            out.append(f"print {m.group(1)}")
            continue

        # ignore anything else
    return out

# ─── Main entry ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv)>1 else "main.c"
    dst = sys.argv[2] if len(sys.argv)>2 else "output.asm"
    with open(src) as f:
        asm_lines = compile_simple(f.readlines())
    with open(dst,"w") as o:
        o.write("\n".join(asm_lines))
    print("✔ Wrote", dst)
