# How to study: a workflow for understanding faster

Reading examples is not enough, and it isn't the fastest way either. Examples show *what* to call, never *why it
works*. The fastest way to the "why" is to treat every source as **local text you can search** and to read in a fixed
order: from the hardware truth outwards. Everything below is on this laptop already, version-matched to the chip and
to ESP-IDF v6.1, and `rg` / `rgf` search it in milliseconds.

## 1. Your library (all local, all searchable)

In the `embedded` box (`bench enter embedded`, or a VS Code terminal there). Set this once per terminal:

```bash
IDF=~/.espressif/v6.1/esp-idf        # ($IDF_PATH after `idf`)
TRM=~/projects/chip-canvas/sources/text/esp32c6-trm   # the TRM as text, ONE FILE PER PAGE: 271.txt = page 271
```

| What | Where | What it is for |
| --- | --- | --- |
| **TRM** (Technical Reference Manual) | `$TRM/*.txt`, PDF in `~/projects/chip-canvas/sources/pdf/` | The truth about the hardware: every register, every bit. |
| **Register headers** | `$IDF/components/soc/esp32c6/register/soc/*_reg.h`, `*_struct.h` | The TRM's registers as C names and addresses (generated from the same source). |
| **Low-level (LL) layer** | `$IDF/components/esp_hal_*/esp32c6/include/hal/*_ll.h` | **The cheat sheet:** which registers Espressif's own code writes, in which order. Short, readable. |
| **Drivers** | `$IDF/components/esp_driver_*/src/*.c` | The friendly API (`gpio_set_level`) built on the LL layer. |
| **Docs** (the website) | `$IDF/docs/en/` (`.rst` text) | The docs website is built from these files: same text, exact version. `idf.py docs` opens the web page for v6.1 + esp32c6; in VS Code select a word → right-click → "Search in Documentation...". |
| **Examples** | `$IDF/examples/` (each has a `README.md`) | Smallest working use of an API. |
| **Config options** | `Kconfig*` files in every component | Every setting you can change, with its help text (section 4). |
| **RISC-V specs** | `~/projects/chip-canvas/sources/text/riscv-unpriv/`, `riscv-psabi/` | Instructions, and the calling convention. |
| **History / discussions** | github.com/espressif/esp-idf (issues, `git log`), esp32.com forum | *Why* something is the way it is. The local IDF is a shallow clone (no history): use GitHub for this. |

Trust order when they disagree: TRM > register headers > LL > drivers > docs > examples > forums.

## 2. The study loop (for any new thing: a peripheral, a FreeRTOS call, a boot step)

1. **Concept, from the TRM (10 min).** Find the chapter by its title:
   `rg -l "IO MUX and GPIO Matrix" $TRM | sed 's#.*/##' | sort -n` → `3.txt 9.txt 244.txt`: pages 3 and 9 are the
   table of contents, **page 244** is "Chapter 7, 7.1 Overview". Read only the overview and the block diagram pages.
   Goal: draw it on paper in boxes and arrows.
2. **See it work, unchanged.** Smallest official example: `ls $IDF/examples/peripherals/`, read its `README.md`,
   build and flash it as is. Something running gives you a thing to poke.
3. **Peel the onion: example → driver → LL → register → TRM page.** Ctrl-click (VS Code: F12) from each call down, or
   use `rg`. Stop at the LL function: that is where the real work is. Example, verified in v6.1:
   - `examples/peripherals/gpio/generic_gpio/main/gpio_example_main.c` calls `gpio_set_level`
   - `components/esp_driver_gpio/src/gpio.c:249`: `gpio_set_level` → `gpio_hal_set_level`
   - `components/esp_hal_gpio/include/hal/gpio_hal.h:234`: a macro for `gpio_ll_set_level`
   - `components/esp_hal_gpio/esp32c6/include/hal/gpio_ll.h:328`: `hw->out_w1ts.val = 1 << gpio_num;`
   - `components/soc/esp32c6/register/soc/gpio_reg.h:40`: `GPIO_OUT_W1TS_REG (DR_REG_GPIO_BASE + 0x8)`
   - `rg -l GPIO_OUT_W1TS_REG $TRM` → `271.txt`: TRM page 271, "Register 7.2. GPIO_OUT_W1TS_REG"

   One line of an example turned out to be one store instruction to one address. That is the whole trick.
4. **Rebuild it yourself, at register level** (that's each lab): your code, the harness says PASS/FAIL.
5. **Watch it happen.** chip-canvas (zen mode + ▶) for the instructions, GDB `stepi` + `x` for memory, the logic
   analyzer for the pins. Predict first, then look: a wrong prediction is the best lesson you'll get.
6. **Write down what surprised you** in the lab's README. Explaining it in your own words is what makes it stick.

Rule of thumb: never read a big file top to bottom. Search for the name you care about, read 30 lines around it, follow one name further down. Repeat.

## 3. Search recipes

```bash
rgf                                          # live grep in the current dir: type, preview, Enter opens VS Code at the line
cd $IDF/components && rgf gpio_ll_set_level  # same, with a starting query

rg -n "^esp_err_t gpio_set_level" $IDF/components         # where is it DEFINED
rg -l gpio_set_level $IDF/examples                         # which examples USE it
rg -l gpio_set_level $IDF/examples | xargs wc -l | sort -n | head   # ...the shortest ones first
rg -n "out_w1ts" $IDF/components/esp_hal_gpio/esp32c6     # only our chip (each chip has its own folder)
rg -il "ledc" $TRM | sort -n | head                        # TRM pages about a peripheral (file name = page)
rg -n -t c -t h "esp_rom_delay_us" $IDF/components         # only C/headers (-g '*.S' for assembly)
rg -n "config FREERTOS_HZ" -A8 -g 'Kconfig*' $IDF/components   # a config option's definition + help
rg -n "CONFIG_FREERTOS_HZ" $IDF/components                 # where C code reads it
gh search issues --repo espressif/esp-idf "esp32c6 gpio glitch"   # what others hit (gh works in every box)
```

## 4. Configuration (menuconfig, the VS Code settings page, sdkconfig)

The "tons of settings" you remember from the Korvo are **Kconfig options**. There is one system with three faces:

| Face | How to open it | What it is |
| --- | --- | --- |
| `idf.py menuconfig` | terminal, in the project | The terminal UI (that's the Python script you remember: `idf.py` is Python). `/` searches, `?` shows the help and the option's `CONFIG_` name. |
| **SDK Configuration Editor (Menuconfig)** | VS Code: the gear icon in the bottom bar, `Ctrl+E G`, or right-click `sdkconfig` | A GUI over the same options (the extension talks to `idf.py confserver`). **Save** writes the `sdkconfig` file; it doesn't write code. |
| The files | `sdkconfig`, `sdkconfig.defaults` | What both UIs read and write. |

How a setting flows (doc: `$IDF/docs/en/api-guides/kconfig/configuration_structure.rst`):

1. **Defined** in a `Kconfig` file of some component (or your project's `main/Kconfig.projbuild`): name, type, range,
   default, help text. Lab 00 has **1105** options, coming from ~147 components: you will never read them all, and
   you don't need to.
2. **Chosen** in `sdkconfig` (the full list of current values, generated: don't edit by hand) and
   `sdkconfig.defaults` (only what *you* changed: this is what the labs commit; `sdkconfig` is gitignored).
3. **Turned into C** at build time: `build/config/sdkconfig.h`, one `#define CONFIG_...` per option. C code reads
   it with `#if CONFIG_...` or as a plain value.

Traced end to end in your own Lab 00 (`vTaskDelay(pdMS_TO_TICKS(1000))`, `main.c:24`):

- `pdMS_TO_TICKS(ms)` = `ms * configTICK_RATE_HZ / 1000` (`components/freertos/FreeRTOS-Kernel/include/freertos/projdefs.h:46`)
- `configTICK_RATE_HZ` = `CONFIG_FREERTOS_HZ` (`components/freertos/config/include/freertos/FreeRTOSConfig.h:92`)
- defined at `components/freertos/Kconfig:33`: `int`, range 1 to 1000, **default 100**
- `labs/00-hello/sdkconfig:2557`: `CONFIG_FREERTOS_HZ=100` → `build/config/sdkconfig.h:713`: `#define CONFIG_FREERTOS_HZ 100`
- so `pdMS_TO_TICKS(1000)` = 100 ticks, computed by the compiler: in chip-canvas you can see `li a0,100` right
  before `jal vTaskDelay` (0x4200a7e6). And a surprise: `pdMS_TO_TICKS(5)` = 5·100/1000 = **0** ticks. A tick is 10 ms.

Try it: open the editor, search `configTICK_RATE_HZ`, set 1000, save, `git diff sdkconfig`, rebuild, and look at
that `li` again in chip-canvas. Then keep the change in `sdkconfig.defaults` (`idf.py save-defconfig` writes a
minimal one; in VS Code: right-click `sdkconfig` → "Save Default SDKCONFIG File") or revert it.

Big frameworks (esp-skainet on the Korvo, esp-who, esp-bsp) add their own `Kconfig` menus. Start from the example's
`sdkconfig.defaults` (and `sdkconfig.defaults.<target>`): that short file lists exactly what the authors needed to
change. Look up each line with the `rg ... -g 'Kconfig*'` recipe above.

## 5. Use Claude as a reading partner

In this repo Claude is a tutor. Good questions: "trace `uart_write_bytes` down to the register write", "which TRM
page explains this bit?", "why is this `CONFIG_` set in this example?". Ask it to cite `file:line` and TRM pages,
then open them yourself: the citation is the lesson.
