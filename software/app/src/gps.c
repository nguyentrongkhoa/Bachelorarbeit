#include "gps.h"
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>

// Get the UART device for the GPS module using the device tree alias
static const struct device *uart_dev = DEVICE_DT_GET(DT_ALIAS(gps_uart));

int gps_init(void) {
    if (!device_is_ready(uart_dev)) {
        printk("Error: GPS UART device is not ready\n");
        return -ENODEV; // no such device error
    }
    return 0;
}

void gps_print_raw_data(void) {
    unsigned char c;
    if(uart_poll_in(uart_dev, &c) == 0) {
        printk("%c", c);
    }
}