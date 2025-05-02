import sys

# Reverse lookup for standard and creative opcodes
op_codes = {
    "000000": "add",
    "000001": "sub",
    "000010": "and",
    "000011": "or",
    "000100": "slt",
    "100011": "lw",
    "101011": "sw",
    "000101": "beq",
    "000110": "jump",
    "000111": "mov",
    "001000": "xor",
    "001001": "load",
    "001010": "store",
}

fun_opcodes = {
    "0100000000000000": "clap",
    "0100000100000000": "incz",
    "0100011000000000": "dump",
    "0100011100000000": "halt",
}

# Partial matches for parameterized fun ops
prefix_ops = {
    "01000010": "rnd",
    "01000011": "swap",
    "01000100": "fzbz",
    "01000101": "emit",
    "01001000": "shl",
    "01001001": "shr",
}

registers = {
    "0000": "r0",
    "0001": "r1",
    "0010": "r2",
    "0011": "r3",
    "0100": "r4",
    "0101": "r5",
    "0110": "r6",
    "0111": "r7",
    "1000": "pc",
    "1001": "sp",
    "1010": "zf",
    "1011": "rnd"
}

def handle_lines(bin_file: str):
    with open(bin_file, "r") as input_file:
        lines = [line.strip() for line in input_file.readlines()]
    
    mips_instructions = []
    for binary in lines:
        mips_instructions.append(bin_to_zap(binary))

    with open("BACK_TO_ZAP.txt", "w") as output_file:
        for instr in mips_instructions:
            output_file.write(instr + "\n")

def bin_to_zap(line):
    if line in fun_opcodes:
        return fun_opcodes[line]

    for prefix, name in prefix_ops.items():
        if line.startswith(prefix):
            if name in ["fzbz", "emit", "rnd"]:
                reg = line[8:12]
                return f"{name} {registers[reg]}"
            elif name == "swap":
                reg1 = line[8:12]
                reg2 = line[12:16]
                return f"swap {registers[reg1]}, {registers[reg2]}"
            elif name in ["shl", "shr"]:
                reg = line[8:12]
                imm = int(line[12:], 2)
                return f"{name} {registers[reg]}, {imm}"

    op_code = line[0:6]

    # R-type
    if op_code in ["000000", "000001", "000010", "000011", "000100", "001000"]:
        rs = line[6:10]
        rt = line[10:14]
        rd = line[14:18]
        return f"{op_codes[op_code]} {registers[rd]}, {registers[rs]}, {registers[rt]}"
    
    # I-type
    if op_code in ["000111"]:  # mov
        reg = line[6:10]
        imm = int(line[10:], 2)
        return f"mov {registers[reg]}, {imm}"

    if op_code in ["100011", "101011"]:  # lw, sw
        rs = line[6:10]
        rt = line[10:14]
        offset = int(line[14:], 2)
        return f"{op_codes[op_code]} {registers[rt]}, {offset}({registers[rs]})"
    
    if op_code == "000101":  # beq
        rs = line[6:10]
        rt = line[10:14]
        offset = int(line[14:], 2)
        return f"beq {registers[rs]}, {registers[rt]}, {offset}"
    
    if op_code == "000110":  # jump
        addr = int(line[6:], 2)
        return f"jump {addr}"

    return f"UNKNOWN {line}"

if __name__ == "__main__":
    handle_lines(sys.argv[1])
