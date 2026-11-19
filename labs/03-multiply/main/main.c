// Lab 03: the test harness and the stopwatch (don't change it; your work is in multiply.S). See README.md.
#include <stdio.h>
#include "esp_cpu.h"   // esp_cpu_get_cycle_count(): the CPU's cycle counter (one tick per clock, 160 MHz)

unsigned mul_hw(unsigned a, unsigned b);
unsigned mul_soft(unsigned a, unsigned b);

static int passed, total;

static void check(unsigned a, unsigned b)
{
    unsigned expected = a * b;   // the C compiler uses the mul instruction here
    unsigned got = mul_soft(a, b);
    total++;
    if (got == expected) passed++;
    printf("%s  mul_soft(%u, %u) = %u, expected %u\n", got == expected ? "PASS" : "FAIL", a, b, got, expected);
}

// Cycles one call takes, timed with the cycle counter. The best of 10 tries, to skip one-off delays
// (an interrupt, the first fetch from flash into the cache...).
static unsigned cycles(unsigned (*f)(unsigned, unsigned), unsigned a, unsigned b)
{
    unsigned best = ~0u;
    for (int i = 0; i < 10; i++) {
        unsigned start = esp_cpu_get_cycle_count();
        f(a, b);
        unsigned took = esp_cpu_get_cycle_count() - start;
        if (took < best) best = took;
    }
    return best;
}

void app_main(void)
{
    printf("\n--- Lab 03 tests ---\n");
    check(6, 7);
    check(0, 12345);
    check(12345, 0);
    check(1, 4000000000u);
    check(65535, 65537);
    check(0xFFFFFFFF, 2);       // overflows: only the low 32 bits are kept, like mul
    check(0xFFFFFFFF, 0xFFFFFFFF);
    printf("%d/%d passed\n", passed, total);

    printf("\n--- cycles per call (including the call and the return) ---\n");
    unsigned bs[] = {0, 1, 3, 255, 0x10000, 0x80000000, 0xFFFFFFFF};
    for (int i = 0; i < sizeof bs / sizeof bs[0]; i++) {
        printf("b = 0x%08x: mul_hw %3u cycles, mul_soft %4u cycles\n", bs[i], cycles(mul_hw, 12345, bs[i]),
               cycles(mul_soft, 12345, bs[i]));
    }
    // Press RESET to run again.
}
