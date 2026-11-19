// Lab 03: a button bounces. See it, then debounce it with a state machine. Fill in the TODOs (see README.md).
#include <stdio.h>
#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_rom_sys.h"   // esp_rom_delay_us(): a busy wait, precise to the microsecond

#define BUTTON_PIN   GPIO_NUM_9    // BOOT button: pressed = 0 (it connects the pin to GND). Analyzer CH4
#define RAW_PIN      GPIO_NUM_19   // copy of what the firmware reads right now        Analyzer CH1
#define CLEAN_PIN    GPIO_NUM_20   // debounced state                                   Analyzer CH2
#define SAMPLE_US    50            // read the button every 50 us
#define STABLE_US    5000          // a level must hold this long to count as a real change

void app_main(void)
{
    // TODO 1: BUTTON_PIN as an input with the internal pull-up (gpio_set_pull_mode()),
    //         RAW_PIN and CLEAN_PIN as outputs.

    int naive_presses = 0, clean_presses = 0;
    bool last_raw = true;   // not pressed

    while (1) {
        for (int i = 0; i < 1000; i++) {           // 1000 samples = 50 ms of busy polling...
            bool raw = gpio_get_level(BUTTON_PIN);
            gpio_set_level(RAW_PIN, raw);

            // Naive: every 1 -> 0 transition is a press.
            if (last_raw && !raw) naive_presses++;
            last_raw = raw;

            // TODO 2: a debouncer. Write it as a small state machine (draw it first, on paper):
            //         states like RELEASED, MAYBE_PRESSED, PRESSED, MAYBE_RELEASED, and a counter of how
            //         long the new level has held. Count clean_presses and drive CLEAN_PIN.

            esp_rom_delay_us(SAMPLE_US);
        }
        vTaskDelay(1);                              // ...then let the idle task run (watchdog, Lab 01)

        static int shown_naive = -1, shown_clean = -1;
        if (naive_presses != shown_naive || clean_presses != shown_clean) {
            printf("presses: naive %d, debounced %d\n", naive_presses, clean_presses);
            shown_naive = naive_presses;
            shown_clean = clean_presses;
        }
    }
}
