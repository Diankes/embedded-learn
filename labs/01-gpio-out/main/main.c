// Lab 01: drive a pin and measure time on the wire. Fill in the TODOs (see README.md).
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"

#define OUT_PIN    GPIO_NUM_18   // analyzer CH0
#define HALF_MS    500           // time high, then time low (period = 2 * HALF_MS)

void app_main(void)
{
    // TODO 1: make OUT_PIN a push-pull output.
    //         Look at gpio_reset_pin() and gpio_set_direction() in driver/gpio.h.

    printf("FreeRTOS tick: %d Hz, so one tick = %d ms\n", configTICK_RATE_HZ, 1000 / configTICK_RATE_HZ);
    printf("pdMS_TO_TICKS(%d) = %d ticks\n", HALF_MS, (int)pdMS_TO_TICKS(HALF_MS));

    while (1) {
        // TODO 2: set the pin high, wait HALF_MS, set it low, wait HALF_MS.
        //         gpio_set_level() and vTaskDelay(pdMS_TO_TICKS(...)).
        vTaskDelay(pdMS_TO_TICKS(HALF_MS));   // remove this line once TODO 2 is done
    }
}
