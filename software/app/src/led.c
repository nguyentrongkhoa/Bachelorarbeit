#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
//#include <zephyr/lib/libc/minimal/include/errno.h> // to use error codes like -ENODEV

#include "led.h"

// Get the GPIO device for the status LED using the device tree alias
static const struct gpio_dt_spec status_led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

int led_init(void) {
    if (!gpio_is_ready_dt(&status_led)) {
        printk("Error: Status LED device is not ready\n");
        return -ENODEV; // no such device error
    }
    else {
        gpio_pin_configure_dt(&status_led, GPIO_OUTPUT_ACTIVE);
        return 0;
    }
}
    
void led_blink(int delay_ms) {
	while (1) {
		gpio_pin_toggle_dt(&status_led);
		k_msleep(delay_ms);
	}
}