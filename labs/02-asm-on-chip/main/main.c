// Lab 02: the test harness (don't change it; your work is in functions.S). See README.md.
#include <stdio.h>

// The functions you write in functions.S. C calls them like any other function.
int add3(int a, int b, int c);
int max2(int a, int b);
int sum_to(int n);
int count_ones(unsigned x);

static int passed, total;

static void check(const char *call, int got, int expected)
{
    total++;
    if (got == expected) passed++;
    printf("%s  %-22s = %-11d expected %d\n", got == expected ? "PASS" : "FAIL", call, got, expected);
}
#define CHECK(call, expected) check(#call, (call), (expected))

void app_main(void)
{
    printf("\n--- Lab 02 tests ---\n");
    CHECK(add3(1, 2, 3), 6);
    CHECK(add3(-5, 2, 0), -3);
    CHECK(add3(2147483647, 1, 0), -2147483648);   // wraps around: why? (Think 3)

    CHECK(max2(3, 7), 7);
    CHECK(max2(7, 3), 7);
    CHECK(max2(-1, -8), -1);
    CHECK(max2(-1, 1), 1);

    CHECK(sum_to(10), 55);
    CHECK(sum_to(1), 1);
    CHECK(sum_to(0), 0);
    CHECK(sum_to(-4), 0);

    CHECK(count_ones(0), 0);
    CHECK(count_ones(0xB), 3);
    CHECK(count_ones(0xFFFFFFFF), 32);
    CHECK(count_ones(0x80000001), 2);

    printf("%d/%d passed\n", passed, total);
    // app_main returns here; FreeRTOS keeps running. Press RESET on the board to run the tests again.
}
