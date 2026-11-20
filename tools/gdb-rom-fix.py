# Make GDB disassemble app code again after ESP-IDF loads the chip's ROM symbols.
#
# Why: ESP-IDF's gdbinit adds the ROM ELF (esp-rom-elfs/*/esp32c6_rev0_rom.elf) for ROM function names.
# That ELF also has two data sections, .eh_frame and .eh_frame_hdr, at 0x42000000-0x4200f07c: the same
# addresses where your app's code is mapped from flash. GDB then treats your code there as data and prints
# ".word 0x..." instead of instructions (VS Code's Disassembly view, x/i, disassemble).
# Fix: reload the ROM ELF with those two sections moved to an unused address. ROM function names stay;
# the cost is that GDB can't use the ROM's unwind tables (backtraces through ROM code may be shorter).
#
# Used by .vscode/launch.json (target.connectCommands) after ESP-IDF's own commands; or by hand: source <this file>
import gdb

for objfile in gdb.objfiles():
    path = objfile.filename
    if path and path.endswith("_rom.elf"):
        gdb.execute("set confirm off")
        gdb.execute(f"remove-symbol-file {path}")
        gdb.execute(f"add-symbol-file {path} -s .eh_frame 0xf0000000 -s .eh_frame_hdr 0xf1000000", to_string=True)
        gdb.execute("set confirm on")
        print(f"gdb-rom-fix: reloaded {path} with .eh_frame moved out of the app's flash window")
