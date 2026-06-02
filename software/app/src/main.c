/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <errno.h>
#include <zephyr/sys/util.h>
#include <zephyr/drivers/lora.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/gpio.h>

#include "gps.h"
#include "led.h"

LOG_MODULE_REGISTER(module, LOG_LEVEL_DBG);
// Get the GPIO device for the status LED using the device tree alias
static const struct gpio_dt_spec status_led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

int main(void) {
	k_msleep(2000);
	led_init();
	gps_init();
	while(1) {
		led_toggle();
		k_msleep(1000);
		gps_print_raw_data();
	}
}

