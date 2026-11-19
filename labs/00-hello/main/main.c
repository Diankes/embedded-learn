// Lab 00: hello. This one is complete on purpose: the goal is the tools, not the code.
#include <stdio.h>
#include <inttypes.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_chip_info.h"
#include "esp_flash.h"

void app_main(void)   // ESP-IDF calls this after the bootloader, the startup code and FreeRTOS are running
{
    esp_chip_info_t chip;
    esp_chip_info(&chip);

    uint32_t flash_bytes = 0;
    esp_flash_get_size(NULL, &flash_bytes);

    printf("Hello from %s: %d core(s), silicon v%d.%d, %" PRIu32 " MB flash\n",
           CONFIG_IDF_TARGET, chip.cores, chip.revision / 100, chip.revision % 100,
           flash_bytes / (1024 * 1024));

    for (int n = 0;; n++) {
        printf("alive %d\n", n);
        vTaskDelay(pdMS_TO_TICKS(1000));   // sleep 1 s; other tasks (and the idle task) run meanwhile
    }
}
