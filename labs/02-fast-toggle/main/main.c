// Lab 02: how fast can the CPU wiggle a pin? Fill in the TODOs (see README.md).
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "soc/gpio_reg.h"   // GPIO_OUT_W1TS_REG / GPIO_OUT_W1TC_REG: "write 1 to set" / "write 1 to clear"
#include "soc/soc.h"        // REG_WRITE()

#define OUT_PIN  GPIO_NUM_18   // analyzer CH0
#define BURST    1000          // toggles per burst, then a short sleep so the idle task (and its watchdog) can run

__attribute__((noinline))   // keep it a separate function, so objdump can find it by name
static void burst_with_driver(void)
{
    for (int i = 0; i < BURST; i++) {
        // TODO 1: pin high then low with gpio_set_level().
    }
}

__attribute__((noinline))
static void burst_with_registers(void)
{
    for (int i = 0; i < BURST; i++) {
        // TODO 2: the same, writing the pin's bit (1 << OUT_PIN) straight into the GPIO set/clear registers.
        //         REG_WRITE(register, value). Find the register addresses in soc/gpio_reg.h.
    }
}

void app_main(void)
{
    gpio_reset_pin(OUT_PIN);
    gpio_set_direction(OUT_PIN, GPIO_MODE_OUTPUT);

    while (1) {
        burst_with_driver();
        vTaskDelay(1);            // a gap on the analyzer between the two bursts
        burst_with_registers();
        vTaskDelay(1);
    }
}
