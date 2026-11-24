#!/usr/bin/env python3
"""Generate the C6 Tactics puzzle pack (../puzzles.json).

Every answer comes from a real tool, never from memory:
  exec      the snippet is assembled by the ESP toolchain and RUN in QEMU (qemu-riscv32); the registers are dumped after
            every line, so the explanation's trace is what the CPU actually did
  decode    the word is produced by the ESP assembler; the choices are the ESP objdump's own text
  c2asm     each listing is the ESP gcc -O2 output for exactly that C
  mmio      addresses are parsed from ESP-IDF v6.1's register headers (file:line cited)
  abi       the table in the RISC-V psABI (page cited)
  bits      plain arithmetic (Python ints)

Runs inside the arena-gen container (build.sh mounts /tc /idf /text /out). Deterministic: same seed, same pack.
"""
import json
import os
import random
import re
import subprocess
import sys
import tempfile

TC = "/tc/bin/riscv32-esp-elf-"
IDF = "/idf"
TEXT = "/text"
OUT = "/out/puzzles.json"
MARCH = "rv32imac_zicsr_zifencei"   # what ESP-IDF v6.1 builds the C6 with
M32 = 0xFFFFFFFF
rng = random.Random(6)

SPEC = {   # citations, checked against ~/projects/chip-canvas/sources/text (file = PDF page)
    "fmt": "RISC-V Unprivileged ISA §2.2 Base Instruction Formats (riscv-unpriv/45.txt)",
    "alu": "RISC-V Unprivileged ISA §2.4 Integer Computational Instructions (riscv-unpriv/47-49.txt)",
    "mem": "RISC-V Unprivileged ISA §2.6 Load and Store Instructions (riscv-unpriv/53-54.txt)",
    "mul": "RISC-V Unprivileged ISA §12.1 Multiplication (riscv-unpriv/89.txt)",
    "div": "RISC-V Unprivileged ISA §12.2 Division, Table 11: divide by zero and overflow (riscv-unpriv/90.txt)",
    "rvc": "RISC-V Unprivileged ISA §27.2 Compressed Instruction Formats (riscv-unpriv/182.txt)",
    "abi": "RISC-V psABI Table 1, Integer register convention (riscv-psabi/9.txt)",
}

# Each concept belongs to the lab where it is first needed (README.md "Part" order). The app treats concepts of the
# current lab as "in network", earlier ones as review, later ones as preview.
CONCEPTS = {
    "hex": ("Hex and binary", 1), "twos": ("Two's complement", 1), "arith": ("Add and subtract", 1),
    "logic": ("Bitwise logic", 1), "abi": ("Register names", 2), "shift": ("Shifts", 2), "cmp": ("Compare and set", 2),
    "lui": ("Big constants", 2), "muldiv": ("Multiply and divide", 3), "endian": ("Endianness", 4),
    "mem": ("Loads and stores", 4), "decode": ("Machine code", 5), "rvc": ("Compressed code", 5),
    "c2asm": ("C to assembly", 5), "mmio": ("Memory-mapped I/O", 6),
}


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"{' '.join(cmd)} failed:\n{r.stderr}")
    return r.stdout


def h32(v):
    return f"0x{v & M32:08x}"


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def clamp(r):
    return int(max(500, min(2300, round(r / 10) * 10)))


puzzles = []


def add(pid, concept, rating, kind, q, **kw):
    p = {"id": pid, "c": concept, "lab": CONCEPTS[concept][1], "r": clamp(rating), "k": kind, "q": q}
    p.update(kw)
    puzzles.append(p)


# ---------------------------------------------------------------------------------------------------------------------
# exec: predict a register. Snippets run for real in QEMU.
REGS = ["a0", "a1", "a2", "a3", "t0", "t1", "t2"]      # t6 is the dump pointer, sp the scratch memory
VALS_EASY = [1, 2, 3, 5, 7, 8, 10, 12, 15, 16, 20, 25, 42, 100]
VALS_HARD = [-1, -2, -8, -100, 0xFF, 0x80, 0x7FF, -2048, 0x1234, 0x7FFFFFFF, -0x80000000, 0x12345678, 0xF0F0, 0xABCD]
OPNOTE = {
    "add": "add: rd = rs1 + rs2 (32 bits, overflow wraps around)", "sub": "sub: rd = rs1 - rs2",
    "addi": "addi: rd = rs1 + a 12-bit signed immediate (-2048..2047)", "neg": "neg rd, rs is sub rd, zero, rs",
    "and": "and: 1 only where both bits are 1", "or": "or: 1 where either bit is 1", "xor": "xor: 1 where bits differ",
    "andi": "andi: and with a sign-extended 12-bit immediate", "ori": "ori: or with a sign-extended 12-bit immediate",
    "xori": "xori: xor with a sign-extended immediate (xori rd, rs, -1 is not)", "not": "not rd, rs is xori rd, rs, -1",
    "slli": "slli: shift left, zeros come in from the right (x << n = x * 2^n)",
    "srli": "srli: shift right LOGICAL, zeros come in from the left", "sll": "sll: shift left by rs2's low 5 bits",
    "srai": "srai: shift right ARITHMETIC, copies of the sign bit come in from the left",
    "srl": "srl: logical right shift by rs2's low 5 bits", "sra": "sra: arithmetic right shift by rs2's low 5 bits",
    "slt": "slt: 1 if rs1 < rs2 as SIGNED numbers, else 0", "sltu": "sltu: 1 if rs1 < rs2 as UNSIGNED numbers, else 0",
    "slti": "slti: 1 if rs1 < imm (signed)", "sltiu": "sltiu: 1 if rs1 < imm (unsigned compare; imm is sign-extended first)",
    "seqz": "seqz rd, rs is sltiu rd, rs, 1 (1 only if rs == 0)", "snez": "snez rd, rs is sltu rd, zero, rs",
    "lui": "lui: rd = imm << 12 (sets the upper 20 bits, clears the low 12)",
    "li": "li is a pseudo-instruction: addi for small values, lui + addi for big ones",
    "mul": "mul: low 32 bits of rs1 * rs2", "mulh": "mulh: HIGH 32 bits of the signed 64-bit product",
    "mulhu": "mulhu: high 32 bits of the unsigned 64-bit product",
    "div": "div: signed division, rounds toward zero; x/0 = -1, MIN/-1 = MIN (no trap!)",
    "divu": "divu: unsigned division; x/0 = 0xffffffff", "rem": "rem: signed remainder, has the sign of the dividend; x%0 = x",
    "remu": "remu: unsigned remainder", "mv": "mv rd, rs is addi rd, rs, 0",
    "sw": "sw: store 4 bytes, little-endian (lowest byte at the lowest address)", "sh": "sh: store the low 2 bytes",
    "sb": "sb: store the low byte", "lw": "lw: load 4 bytes", "lh": "lh: load 2 bytes, SIGN-extended",
    "lhu": "lhu: load 2 bytes, zero-extended", "lb": "lb: load 1 byte, SIGN-extended", "lbu": "lbu: load 1 byte, zero-extended",
}
OPSPEC = {**{o: "alu" for o in OPNOTE}, **{o: "mul" for o in ("mul", "mulh", "mulhu")},
          **{o: "div" for o in ("div", "divu", "rem", "remu")},
          **{o: "mem" for o in ("sw", "sh", "sb", "lw", "lh", "lhu", "lb", "lbu")}}


def lit(v):
    """How a person would write the constant: decimal when small, hex when it's a bit pattern."""
    if -2048 <= v < 256:
        return str(v)
    return hex(v & M32)


def pick_val(hard):
    return lit(rng.choice(VALS_HARD if hard and rng.random() < 0.6 else VALS_EASY))


def gen_snippet(concept, level):
    """Returns (lines, target register, difficulty extras). level 0..2 = more lines, nastier values."""
    hard = level >= 1
    regs = rng.sample(REGS, 4)
    x, y, z, w = regs
    lines = [f"li {x}, {pick_val(hard)}"]
    extra = 0
    if concept in ("arith", "logic", "shift", "cmp", "muldiv"):
        lines.append(f"li {y}, {pick_val(hard)}")
    ops = {
        "arith": lambda: rng.choice([f"add {z}, {x}, {y}", f"sub {z}, {x}, {y}", f"addi {z}, {x}, {rng.choice([1, -1, 10, -16, 100, 2047, -2048])}",
                                     f"neg {z}, {x}", f"sub {z}, {y}, {x}"]),
        "logic": lambda: rng.choice([f"and {z}, {x}, {y}", f"or {z}, {x}, {y}", f"xor {z}, {x}, {y}", f"andi {z}, {x}, {rng.choice([0xF, 0xFF, 0x7F0, -16, 1])}",
                                     f"ori {z}, {x}, {rng.choice([1, 0x80, 0x700, -1])}", f"xori {z}, {x}, {rng.choice([1, 0xFF, -1])}", f"not {z}, {x}"]),
        "shift": lambda: rng.choice([f"slli {z}, {x}, {rng.choice([1, 2, 4, 8, 16, 31])}", f"srli {z}, {x}, {rng.choice([1, 4, 8, 28, 31])}",
                                     f"srai {z}, {x}, {rng.choice([1, 2, 4, 8, 31])}", f"sll {z}, {x}, {y}", f"sra {z}, {x}, {y}", f"srl {z}, {x}, {y}"]),
        "cmp": lambda: rng.choice([f"slt {z}, {x}, {y}", f"sltu {z}, {x}, {y}", f"slti {z}, {x}, {rng.choice([0, 1, 10, -1])}",
                                   f"sltiu {z}, {x}, {rng.choice([1, 10, -1])}", f"seqz {z}, {x}", f"snez {z}, {x}"]),
        "lui": lambda: rng.choice([f"lui {z}, {hex(rng.choice([0x1, 0x12345, 0x60091, 0x80000, 0xFFFFF, 0x40800]))}",
                                   f"li {z}, {lit(rng.choice([0x1000, 0x12345678, 0x60091008, 0x800, 0xFFF, 0x7FF, -2049]))}"]),
        "muldiv": lambda: rng.choice([f"mul {z}, {x}, {y}", f"mulh {z}, {x}, {y}", f"mulhu {z}, {x}, {y}", f"div {z}, {x}, {y}",
                                      f"divu {z}, {x}, {y}", f"rem {z}, {x}, {y}", f"remu {z}, {x}, {y}"]),
    }
    if concept == "mem":
        val = rng.choice([0x12345678, 0xCAFEF00D, 0x80FF7F01, 0xDEADBEEF, 0x000000FF, 0x00008001])
        lines = [f"li {x}, {lit(val)}", f"sw {x}, 0(sp)"]
        if level >= 2 and rng.random() < 0.5:
            lines.append(f"sb {rng.choice(['zero', x])}, {rng.choice([1, 2])}(sp)")
        ld = rng.choice(["lb", "lbu", "lh", "lhu", "lw"] if level else ["lbu", "lw", "lhu"])
        off = {"lb": [0, 1, 2, 3], "lbu": [0, 1, 2, 3], "lh": [0, 2], "lhu": [0, 2], "lw": [0]}[ld]
        lines.append(f"{ld} {z}, {rng.choice(off)}(sp)")
        extra += {"lb": 200, "lh": 200, "lbu": 60, "lhu": 80, "lw": 0}[ld]
        return lines, z, extra
    n_ops = 1 + level
    target = z
    for i in range(n_ops):
        line = ops[concept]()
        if i > 0:   # chain: the next op reads the previous result
            line = line.replace(f", {x}", f", {target}", 1)
            target = rng.choice([z, w])
            line = re.sub(r"^(\S+) (\w+)", lambda m: f"{m.group(1)} {target}", line)
        lines.append(line)
    return lines, target, extra


def run_snippets(snips):
    """Assemble all snippets into one program, run it in QEMU, return per-snippet per-line register dumps."""
    asm = [".globl _start", ".text", "_start:", "  la t6, buf", "  addi sp, sp, -64"]
    dump = [f"  sw {r}, {4 * i}(t6)" for i, r in enumerate(REGS)] + [f"  addi t6, t6, {4 * len(REGS)}"]
    for lines in snips:
        asm += [f"  li {r}, 0" for r in REGS] + ["  sw zero, 0(sp)", "  sw zero, 4(sp)"]
        for ln in lines:
            asm += ["  " + ln] + dump
    asm += ["  la a1, buf", "  sub a2, t6, a1", "  li a0, 1", "  li a7, 64", "  ecall", "  li a0, 0", "  li a7, 93", "  ecall",
            ".bss", ".balign 4", f"buf: .space {sum(len(s) for s in snips) * 4 * len(REGS) + 64}"]
    with tempfile.TemporaryDirectory() as d:
        open(f"{d}/p.S", "w").write("\n".join(asm) + "\n")
        sh([TC + "as", f"-march={MARCH}", "-o", f"{d}/p.o", f"{d}/p.S"])
        sh([TC + "ld", "-e", "_start", "-o", f"{d}/p.elf", f"{d}/p.o"])
        raw = subprocess.run(["qemu-riscv32", f"{d}/p.elf"], check=True, capture_output=True).stdout
    words = [int.from_bytes(raw[i:i + 4], "little") for i in range(0, len(raw), 4)]
    out, k = [], 0
    for lines in snips:
        rows = []
        for _ in lines:
            rows.append(dict(zip(REGS, words[k:k + len(REGS)])))
            k += len(REGS)
        out.append(rows)
    return out


def gen_exec():
    base = {"arith": 650, "logic": 850, "shift": 900, "cmp": 1000, "lui": 1050, "muldiv": 1250, "mem": 1150}
    per = {"arith": 70, "logic": 60, "shift": 60, "cmp": 45, "lui": 25, "muldiv": 28, "mem": 26}
    specs, seen = [], set()
    for concept, n in per.items():
        tries = 0
        while sum(1 for s in specs if s[0] == concept) < n and tries < n * 20:
            tries += 1
            level = rng.choice([0, 0, 1, 1, 2])
            lines, target, extra = gen_snippet(concept, level)
            key = tuple(lines)
            if key in seen:
                continue
            seen.add(key)
            specs.append((concept, level, lines, target, extra))
    traces = run_snippets([s[2] for s in specs])
    for i, ((concept, level, lines, target, extra), rows) in enumerate(zip(specs, traces)):
        final = rows[-1][target]
        if all(rows[j][target] == final for j in range(len(rows))) and len(rows) > 1 and concept != "lui":
            continue   # answer visible in line 1: no puzzle
        trace, prev = [], {r: 0 for r in REGS}
        for ln, row in zip(lines, rows):
            op, args = ln.split(None, 1)
            rd = args.split(",")[0].strip()
            ch = [r for r in REGS if row[r] != prev[r] or (r == rd and op not in ("sw", "sh", "sb"))]
            note = " ".join(f"{r}={h32(row[r])}" + (f" ({s32(row[r])})" if abs(s32(row[r])) < 100000 else "") + ("" if row[r] != prev[r] else " (same as before)") for r in ch)
            if op in ("sw", "sh", "sb"):
                note = f"memory at {args.split(',')[1].strip()} now holds the low {dict(sw=4, sh=2, sb=1)[op]} byte(s) of {rd}"
            trace.append([ln, note])
            prev = row
        ops = []
        for ln in lines:
            op = ln.split()[0]
            if op not in ops:
                ops.append(op)
        notes = [OPNOTE[o] for o in ops if o in OPNOTE]
        srcs = sorted({SPEC[OPSPEC.get(o, "alu")] for o in ops if o not in ("li", "mv", "neg", "not", "seqz", "snez")} or {SPEC["alu"]})
        vals = [s32(v) for row in rows for v in row.values()]
        rating = base[concept] + 110 * level + extra + (80 if any(v < 0 for v in vals) else 0) + (60 if abs(s32(final)) > 4096 else 0)
        rating += 120 if any(o in ("srai", "sra", "sltu", "sltiu", "mulh", "mulhu") for o in ops) and any(v < 0 for v in vals) else 0
        rating += rng.randint(-40, 40)
        cpt = "endian" if concept == "mem" and any(o in ("lb", "lbu", "lh", "lhu") for o in ops) and rng.random() < 0.5 else concept
        add(f"x{i:04d}", cpt, rating, "val", f"After these instructions run, what is in {target}?", code="\n".join(lines),
            ans=final & M32, w=32, trace=trace, why=notes, src=srcs + ["Run for real: ESP assembler + QEMU (qemu-riscv32)"])


# ---------------------------------------------------------------------------------------------------------------------
# decode / encode / rvc: machine code, straight from the ESP assembler and objdump.
def objdump_words(asm_lines, rvc):
    with tempfile.TemporaryDirectory() as d:
        src = [".text", ".option rvc" if rvc else ".option norvc"] + [f"l{i}: {a}" for i, a in enumerate(asm_lines)]
        open(f"{d}/d.S", "w").write("\n".join(src) + "\n")
        sh([TC + "as", f"-march={MARCH}", "-o", f"{d}/d.o", f"{d}/d.S"])
        dis = sh([TC + "objdump", "-d", "-M", "no-aliases", f"{d}/d.o"])
    res = []
    for m in re.finditer(r"^\s*([0-9a-f]+):\s+([0-9a-f]{4,8})\s+(\S+)\s*(.*)$", dis, re.M):
        pc, word, op, args = int(m.group(1), 16), m.group(2), m.group(3), m.group(4).split("#")[0].strip()
        if "<" in args:   # branch/jump: objdump prints the absolute target; show it relative to this pc
            parts = args.split("<")[0].strip().split(",")
            tgt = int(parts[-1], 16)
            parts[-1] = f"pc{tgt - pc:+d}"
            args = ",".join(parts)
        res.append((pc, word, f"{op} {args}".strip()))
    return res


def fields(word_hex, text):
    w = int(word_hex, 16)
    b = f"{w:032b}"
    op = text.split()[0]
    if op in ("add", "sub", "and", "or", "xor", "sll", "srl", "sra", "slt", "sltu", "mul", "mulh", "div", "rem"):
        return f"R-type: funct7 {b[0:7]} | rs2 {b[7:12]} (x{int(b[7:12], 2)}) | rs1 {b[12:17]} (x{int(b[12:17], 2)}) | funct3 {b[17:20]} | rd {b[20:25]} (x{int(b[20:25], 2)}) | opcode {b[25:]}"
    if op in ("addi", "andi", "ori", "xori", "slti", "sltiu", "lw", "lh", "lb", "lbu", "lhu", "jalr", "slli", "srli", "srai"):
        return f"I-type: imm[11:0] {b[0:12]} ({s32(w) >> 20}) | rs1 {b[12:17]} (x{int(b[12:17], 2)}) | funct3 {b[17:20]} | rd {b[20:25]} (x{int(b[20:25], 2)}) | opcode {b[25:]}"
    if op in ("sw", "sh", "sb"):
        return f"S-type: imm[11:5] {b[0:7]} | rs2 {b[7:12]} (x{int(b[7:12], 2)}) | rs1 {b[12:17]} (x{int(b[12:17], 2)}) | funct3 {b[17:20]} | imm[4:0] {b[20:25]} | opcode {b[25:]}"
    if op in ("beq", "bne", "blt", "bge", "bltu", "bgeu"):
        return f"B-type: imm[12|10:5] {b[0:7]} | rs2 {b[7:12]} | rs1 {b[12:17]} | funct3 {b[17:20]} | imm[4:1|11] {b[20:25]} | opcode {b[25:]}"
    if op in ("lui", "auipc"):
        return f"U-type: imm[31:12] {b[0:20]} (0x{w >> 12:05x}) | rd {b[20:25]} (x{int(b[20:25], 2)}) | opcode {b[25:]}"
    if op == "jal":
        return f"J-type: imm[20|10:1|11|19:12] {b[0:20]} | rd {b[20:25]} (x{int(b[20:25], 2)}) | opcode {b[25:]}"
    if len(word_hex) == 4:
        h = f"{w:016b}"
        return f"16-bit: funct3 {h[0:3]} | {h[3:14]} | op {h[14:]} (op != 11, so this is a compressed instruction)"
    return ""


R = ["a0", "a1", "a2", "a3", "a4", "a5", "s0", "s1", "t0", "t1", "sp", "ra"]


def rand_insn(kind):
    a, b, c = rng.sample(R, 3)
    imm = rng.choice([1, 4, 8, -1, -4, 16, 100, 255, -32, 2047, -2048, 12])
    sm = rng.choice([1, 2, 3, 4, 8, 16, 31])
    return {
        "R": lambda: f"{rng.choice(['add', 'sub', 'and', 'or', 'xor', 'sll', 'srl', 'sra', 'slt', 'sltu', 'mul'])} {a}, {b}, {c}",
        "I": lambda: f"{rng.choice(['addi', 'andi', 'ori', 'xori', 'slti'])} {a}, {b}, {imm}",
        "SH": lambda: f"{rng.choice(['slli', 'srli', 'srai'])} {a}, {b}, {sm}",
        "L": lambda: f"{rng.choice(['lw', 'lh', 'lb', 'lbu', 'lhu'])} {a}, {abs(imm) & ~3 if abs(imm) < 200 else 8}({b})",
        "S": lambda: f"{rng.choice(['sw', 'sh', 'sb'])} {a}, {abs(imm) & ~3 if abs(imm) < 200 else 8}({b})",
        "U": lambda: f"lui {a}, {rng.choice([0x60091, 0x12345, 0x40800, 0x1, 0xFFFFF])}",
        "B": lambda: f"{rng.choice(['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu'])} {a}, {b}, .+{rng.choice([8, 12, 16, -4, -8, 64])}",
        "C": lambda: rng.choice([f"c.addi {rng.choice(['a0', 'a1', 's0', 'a5'])}, {rng.choice([1, 3, -1, 8, -16])}", f"c.li {rng.choice(['a0', 'a5', 's1'])}, {rng.choice([0, 1, -2, 31])}",
                                 f"c.mv {rng.choice(['a0', 'a1'])}, {rng.choice(['s0', 'a2'])}", f"c.add {rng.choice(['a0', 's0'])}, {rng.choice(['a1', 'a5'])}",
                                 f"c.lw {rng.choice(['a0', 's1'])}, {rng.choice([0, 4, 8])}({rng.choice(['a1', 's0'])})", f"c.sw {rng.choice(['a2', 'a5'])}, {rng.choice([0, 4, 12])}({rng.choice(['a0', 's1'])})",
                                 f"c.slli {rng.choice(['a0', 's0'])}, {rng.choice([1, 2, 4])}", f"c.jr ra", f"c.addi16sp sp, {rng.choice([-16, -32, 16, 32])}"]),
    }[kind]()


def gen_machine():
    kinds = {"R": (1300, 34), "I": (1250, 30), "SH": (1350, 16), "L": (1400, 18), "S": (1550, 16), "U": (1350, 10), "B": (1750, 16), "C": (1650, 40)}
    n = 0
    for kind, (base, count) in kinds.items():
        made, tries = 0, 0
        while made < count and tries < count * 10:
            tries += 1
            group = []
            while len(group) < 4:
                s = rand_insn(kind)
                if s not in group:
                    group.append(s)
            res = objdump_words(group, rvc=(kind == "C"))
            if len(res) != 4 or len({r[2] for r in res}) < 4 or len({r[1] for r in res}) < 4:
                continue
            if kind == "C" and any(len(r[1]) != 4 for r in res):
                continue
            made += 1
            n += 1
            tgt = rng.randrange(4)
            pc, word, text = res[tgt]
            concept = "rvc" if kind == "C" else "decode"
            why = [fields(word, text), "The other choices encode as: " + ", ".join(f"{r[2]} = 0x{r[1]}" for i, r in enumerate(res) if i != tgt)]
            src = [SPEC["rvc" if kind == "C" else "fmt"], "Encoded by the ESP assembler, text from the ESP objdump (-M no-aliases)"]
            if rng.random() < 0.65 or kind == "C":
                add(f"d{n:04d}", concept, base + rng.randint(-60, 60), "pick", f"Which instruction is the machine word 0x{word}?",
                    code=f"0x{word}", ch=[r[2] for r in res], ans=tgt, why=why, src=src)
            else:
                add(f"e{n:04d}", concept, base + 150 + rng.randint(-60, 60), "pick", "How does the assembler encode this instruction?",
                    code=text, ch=[f"0x{r[1]}" for r in res], ans=tgt, why=why, src=src)


# ---------------------------------------------------------------------------------------------------------------------
# c2asm: what GCC -O2 emits for tiny C. Each group compiles 4 close variants; the choices are their real listings.
C_GROUPS = [
    ("int f(int x)", ["return x * 8;", "return x * 7;", "return x * 9;", "return x * 10;"], 1350,
     "Multiplying by a constant: a power of two is one shift; others become shift+add or a mul."),
    ("int f(int x)", ["return x / 8;", "return x >> 3;", "return (unsigned)x / 8;", "return x % 8;"], 1750,
     "Signed x/8 rounds toward zero, so negative x needs +7 added before the shift (srai). x>>3 rounds down: different!"),
    ("int f(int x)", ["return x == 0;", "return x != 0;", "return x < 0;", "return x >= 0;"], 1450,
     "Comparisons produce 0 or 1 with seqz / snez / slt / srli 31 tricks: no branch needed."),
    ("int f(int x)", ["return x & 0xff;", "return (signed char)x;", "return (short)x;", "return (unsigned short)x;"], 1650,
     "Without the B extension, sign- and zero-extension are a shift left then a shift right (srai keeps the sign, srli doesn't)."),
    ("int f(int x)", ["return x + 2047;", "return x + 2048;", "return x + 100000;", "return x - 2048;"], 1550,
     "addi's immediate is 12-bit signed: -2048..2047. 2048 doesn't fit, so the compiler needs lui (+addi)."),
    ("int f(int a, int b)", ["return a > b ? a : b;", "return a < b ? a : b;", "return (unsigned)a > (unsigned)b ? a : b;", "return a < b;"], 1600,
     "max/min become a compare-and-branch around a mv; unsigned uses bltu/bgeu instead of blt/bge."),
    ("int f(int *p)", ["return p[3];", "return p[1] + p[2];", "return *p + 1;", "return p[-1];"], 1300,
     "Array indexing is a byte offset: p[3] is 12(a0) because an int is 4 bytes."),
    ("int f(signed char *p)", ["return p[3];", "return ((unsigned char *)p)[3];", "return ((short *)p)[1];", "return ((unsigned short *)p)[1];"], 1500,
     "The type picks the load: lb sign-extends, lbu zero-extends, lh/lhu do the same for 2 bytes."),
    ("int f(void)", ["return 0x12345678;", "return 0x800;", "return -1;", "return 0x7ff;"], 1400,
     "A constant that fits in 12 signed bits is one li (addi); a bigger one is lui + addi."),
    ("void f(int *p)", ["*p = 1; *p = 2;", "*(volatile int *)p = 1; *(volatile int *)p = 2;", "*p = 1;", "p[1] = 1; p[0] = 2;"], 1700,
     "Without volatile the compiler deletes the first store (nobody can see it). With volatile, both stores stay: that's why every register access is volatile."),
    ("void f(void)", ["*(volatile unsigned *)0x60091008 = 1u << 5;", "*(volatile unsigned *)0x6009100c = 1u << 5;",
                      "*(volatile unsigned *)0x60091008 = 1u << 15;", "*(volatile unsigned *)0x60091024 = 1u << 5;"], 1550,
     "One register write: lui builds the address 0x60091000, the store's 12-bit offset adds the rest (0x008 = GPIO_OUT_W1TS)."),
    ("unsigned f(unsigned x)", ["return x | (1u << 5);", "return x & ~(1u << 5);", "return x ^ (1u << 5);", "return (x >> 5) & 1;"], 1250,
     "Set, clear, toggle, test one bit: ori / andi with the inverted mask / xori / srli+andi."),
]


def gen_c2asm():
    n = 0
    with tempfile.TemporaryDirectory() as d:
        for sig, bodies, rating, note in C_GROUPS:
            listings = []
            for body in bodies:
                open(f"{d}/f.c", "w").write(f"{sig} {{ {body} }}\n")
                sh([TC + "gcc", "-O2", f"-march={MARCH}", "-mabi=ilp32", "-c", "-o", f"{d}/f.o", f"{d}/f.c"])
                dis = sh([TC + "objdump", "-d", f"{d}/f.o"])
                ins = []
                for m in re.finditer(r"^\s*([0-9a-f]+):\s+[0-9a-f]{4,8}\s+(\S+)\s*(.*)$", dis, re.M):
                    args = m.group(3).split("#")[0].strip()
                    if "<" in args:
                        parts = args.split("<")[0].strip().split(",")
                        parts[-1] = f"pc{int(parts[-1], 16) - int(m.group(1), 16):+d}"
                        args = ",".join(parts)
                    ins.append(f"{m.group(2)} {args}".strip())
                listings.append("\n".join(ins))
            if len(set(listings)) < 4:
                print(f"c2asm: group '{bodies[0]}' has identical listings, skipped", file=sys.stderr)
                continue
            for tgt in range(4):
                n += 1
                why = [note] + [f"{bodies[i]}  →  {listings[i].replace(chr(10), '; ')}" for i in range(4) if i != tgt]
                add(f"c{n:04d}", "c2asm", rating + rng.randint(-50, 50), "pick", "Which listing does GCC -O2 produce for this C?",
                    code=f"{sig} {{ {bodies[tgt]} }}", ch=listings, ans=tgt, mono=True, why=why,
                    src=[f"Compiled by the ESP gcc (-O2 -march={MARCH}), disassembled by its objdump"])


# ---------------------------------------------------------------------------------------------------------------------
# mmio: the C6's memory map and GPIO registers, from ESP-IDF's headers.
def gen_mmio():
    base_h = f"{IDF}/components/soc/esp32c6/register/soc/reg_base.h"
    bases = {}
    for i, ln in enumerate(open(base_h), 1):
        m = re.match(r"#define DR_REG_(\w+)_BASE\s+(0x[0-9A-Fa-f]+)", ln)
        if m:
            bases[m.group(1)] = (int(m.group(2), 16), i)
    want = ["GPIO", "IO_MUX", "UART0", "UART1", "SYSTIMER", "TIMERGROUP0", "INTMTX", "PCR", "LEDC", "SPI2", "I2C_EXT", "RMT", "USB_SERIAL_JTAG"]
    have = [k for k in want if k in bases]
    rel = "components/soc/esp32c6/register/soc/reg_base.h"
    n = 0
    for k in have:
        others = rng.sample([o for o in have if o != k], 3)
        ch = [k] + others
        rng.shuffle(ch)
        n += 1
        add(f"m{n:04d}", "mmio", 1200 + (0 if k in ("GPIO", "IO_MUX", "UART0") else 150), "pick",
            f"Which peripheral's registers start at {h32(bases[k][0])}?", ch=[c.replace("_", " ") for c in ch], ans=ch.index(k),
            why=[f"DR_REG_{k}_BASE = {h32(bases[k][0])}. Peripherals sit at 0x6000_0000 and up, one 4 KB page (0x1000) or more each."],
            src=[f"ESP-IDF v6.1 {rel}:{bases[k][1]}"])
    gpio_h = f"{IDF}/components/soc/esp32c6/register/soc/gpio_reg.h"
    regs = []
    for i, ln in enumerate(open(gpio_h), 1):
        m = re.match(r"#define (GPIO_\w+_REG) \(DR_REG_GPIO_BASE \+ (0x[0-9a-fA-F]+)\)", ln)
        if m and int(m.group(2), 16) < 0x80:
            regs.append((m.group(1), int(m.group(2), 16), i))
    trm = f"{TEXT}/esp32c6-trm"
    pages = {}
    for f in os.listdir(trm):
        txt = open(f"{trm}/{f}", errors="ignore").read()
        for name, _, _ in regs:
            if re.search(rf"Register 7\.\d+\. {name}\b", txt):
                pages[name] = int(f.split(".")[0])
    gb = bases["GPIO"][0]
    for name, off, line in regs:
        others = rng.sample([r for r in regs if r[0] != name], 3)
        ch = [name] + [o[0] for o in others]
        rng.shuffle(ch)
        n += 1
        src = [f"ESP-IDF v6.1 components/soc/esp32c6/register/soc/gpio_reg.h:{line}"] + ([f"ESP32-C6 TRM page {pages[name]} (esp32c6-trm/{pages[name]}.txt)"] if name in pages else [])
        add(f"m{n:04d}", "mmio", 1400 + off * 4 + rng.randint(-40, 40), "pick", f"Which GPIO register is at address {h32(gb + off)}?",
            ch=ch, ans=ch.index(name), why=[f"{h32(gb + off)} = DR_REG_GPIO_BASE ({h32(gb)}) + {hex(off)}, which is {name}."] +
            [f"{o[0]} is at +{hex(o[1])}" for o in others], src=src)


# ---------------------------------------------------------------------------------------------------------------------
# abi: the psABI register table.
ABI = [("x0", "zero", "Zero", None), ("x1", "ra", "Return address", False), ("x2", "sp", "Stack pointer", True),
       ("x3", "gp", "Global pointer", None), ("x4", "tp", "Thread pointer", None)]
ABI += [(f"x{5 + i}", f"t{i}", "Temporary", False) for i in range(3)]
ABI += [("x8", "s0", "Callee-saved (and frame pointer)", True), ("x9", "s1", "Callee-saved", True)]
ABI += [(f"x{10 + i}", f"a{i}", "Argument" + (" / return value" if i < 2 else ""), False) for i in range(8)]
ABI += [(f"x{18 + i}", f"s{2 + i}", "Callee-saved", True) for i in range(10)]
ABI += [(f"x{28 + i}", f"t{3 + i}", "Temporary", False) for i in range(4)]


def gen_abi():
    n = 0
    for x, name, meaning, saved in ABI:
        others = rng.sample([a for a in ABI if a[1] != name], 3)
        n += 1
        ch = [name] + [o[1] for o in others]
        rng.shuffle(ch)
        hard = int(x[1:]) in range(18, 32) or int(x[1:]) in (3, 4, 8, 9)
        add(f"a{n:04d}", "abi", 700 + (250 if hard else 0) + rng.randint(-30, 30), "pick", f"What is the ABI name of register {x}?",
            ch=ch, ans=ch.index(name), why=[f"{x} = {name}: {meaning}."], src=[SPEC["abi"]])
        if saved is not None:
            n += 1
            add(f"a{n:04d}", "abi", 900 + rng.randint(-30, 60), "pick", f"You call a function. Is {name} ({x}) guaranteed to hold the same value when it returns?",
                ch=["Yes: callee-saved", "No: caller-saved"], ans=0 if saved else 1,
                why=[f"{name}: {meaning}. Preserved across calls: {'yes' if saved else 'no'}. s-registers and sp are preserved; a-, t-registers and ra are not."],
                src=[SPEC["abi"]])
    for i in range(8):
        n += 1
        ch = [f"a{i}"] + rng.sample([f"a{j}" for j in range(8) if j != i], 2) + [rng.choice(["t0", "s0", "ra"])]
        rng.shuffle(ch)
        add(f"a{n:04d}", "abi", 750 + 30 * i, "pick", f"In int f(int p0, ..., int p7), which register holds p{i}?", ch=ch, ans=ch.index(f"a{i}"),
            why=[f"Integer arguments go in a0..a7 in order, so p{i} is in a{i}. The return value comes back in a0."], src=[SPEC["abi"]])


# ---------------------------------------------------------------------------------------------------------------------
# bits: number sense. Plain arithmetic.
def gen_bits():
    n = 0
    for v in rng.sample(range(1, 256), 40):
        n += 1
        add(f"b{n:04d}", "hex", 600 + (v > 15) * 100 + rng.randint(-30, 30), "val", f"Write {v} in hex.", ans=v, w=32, fmt="hex",
            why=[f"{v} = {v // 16} × 16 + {v % 16} → 0x{v:x}. Each hex digit is 4 bits: {v:08b} → {v >> 4:04b} {v & 15:04b}."], src=["Arithmetic"])
    for v in rng.sample(range(16, 4096), 30):
        n += 1
        add(f"b{n:04d}", "hex", 750 + (v > 255) * 150 + rng.randint(-30, 30), "val", f"What is 0x{v:x} in decimal?", ans=v, w=32, fmt="dec",
            why=[" + ".join(f"{int(d, 16)}×16^{len(f'{v:x}') - 1 - i}" for i, d in enumerate(f"{v:x}")) + f" = {v}"], src=["Arithmetic"])
    for k in rng.sample(range(0, 32), 22):
        n += 1
        add(f"b{n:04d}", "hex", 800 + (k > 15) * 100, "val", f"What is 1 << {k}, in hex?", ans=1 << k, w=32, fmt="hex",
            why=[f"Bit {k} set: 0x{1 << k:08x}. Every 4 bits is one hex digit, so bit {k} is digit {k // 4} with value {1 << (k % 4)}."], src=["Arithmetic"])
    for v in rng.sample([1, 2, 3, 5, 8, 16, 100, 128, 255, 256, 1000, 2048, 4096, 65536], 14):
        n += 1
        add(f"b{n:04d}", "twos", 950 + (v > 255) * 100, "val", f"-{v} as a 32-bit word, in hex?", ans=(-v) & M32, w=32, fmt="hex",
            why=[f"Two's complement: invert all bits of {v} (0x{v:08x} → 0x{~v & M32:08x}) and add 1 → 0x{(-v) & M32:08x}."], src=[SPEC["alu"]])
    for w_ in rng.sample([0xFFFFFFFF, 0xFFFFFFFE, 0x80000000, 0xFFFFFF00, 0xFFFFF800, 0x7FFFFFFF, 0xFFFFFFF0, 0xFFFF0000], 8):
        n += 1
        add(f"b{n:04d}", "twos", 1100, "val", f"0x{w_:08x} read as a signed int is? (decimal)", ans=w_, w=32, fmt="dec",
            why=[f"The top bit is {w_ >> 31}: " + (f"negative. Value = 0x{w_:08x} − 2^32 = {s32(w_)}." if w_ >> 31 else f"positive: {w_}.")], src=[SPEC["alu"]])
    for imm in rng.sample([0x7FF, 0x800, 0xFFF, 0x801, 0x0FF, 0xF00, 0x400, 0xC00], 8):
        n += 1
        sx = imm - 0x1000 if imm & 0x800 else imm
        add(f"b{n:04d}", "twos", 1250, "val", f"An I-type immediate field holds 0x{imm:03x} (12 bits). What does addi add, as a 32-bit word? (hex)", ans=sx & M32, w=32, fmt="hex",
            why=[f"Bit 11 is {imm >> 11}, the sign: the 12 bits are sign-extended to 32 → 0x{sx & M32:08x} ({sx})."], src=[SPEC["fmt"]])
    for word in rng.sample([0x12345678, 0xCAFEF00D, 0xDEADBEEF, 0x60091008, 0x00C0FFEE, 0x80000001], 6):
        for off in rng.sample(range(4), 2):
            n += 1
            add(f"b{n:04d}", "endian", 1050 + off * 30, "val", f"sw stores 0x{word:08x} at address 0x40800000. Which byte is at 0x4080000{off}? (hex)",
                ans=(word >> (8 * off)) & 0xFF, w=8, fmt="hex", why=[f"RISC-V is little-endian: lowest address = lowest byte. Bytes at +0..+3: " +
                                                       " ".join(f"{(word >> (8 * i)) & 0xFF:02x}" for i in range(4))], src=[SPEC["mem"]])
    for mask_bits in rng.sample(range(0, 28), 10):
        v = rng.choice([0xFFFFFFFF, 0x0, 0x12345678, 0xF0F0F0F0])
        n += 1
        add(f"b{n:04d}", "logic", 950, "val", f"x = 0x{v:08x}. What is x & ~(0xF << {mask_bits})? (hex)", ans=v & ~(0xF << mask_bits) & M32, w=32, fmt="hex",
            why=[f"0xF << {mask_bits} = 0x{(0xF << mask_bits) & M32:08x}; ~ inverts it; & clears those 4 bits: 0x{v & ~(0xF << mask_bits) & M32:08x}. This is how you clear a register field."],
            src=["Arithmetic"])


def main():
    gen_exec()
    gen_machine()
    gen_c2asm()
    gen_mmio()
    gen_abi()
    gen_bits()
    ids = [p["id"] for p in puzzles]
    assert len(ids) == len(set(ids)), "duplicate puzzle ids"
    meta = {"concepts": {k: {"name": v[0], "lab": v[1]} for k, v in CONCEPTS.items()}, "count": len(puzzles)}
    with open(OUT, "w") as f:
        f.write('{"meta":' + json.dumps(meta) + ',"puzzles":[\n')
        f.write(",\n".join(json.dumps(p, separators=(",", ":")) for p in puzzles))
        f.write("\n]}\n")
    by = {}
    for p in puzzles:
        by[p["c"]] = by.get(p["c"], 0) + 1
    print(f"{len(puzzles)} puzzles: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))


if __name__ == "__main__":
    main()
