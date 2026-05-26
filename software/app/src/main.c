/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

int main(void)
{
	static const struct gpio_dt_spec status_led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
	if (!gpio_is_ready_dt(&status_led)) {
		return -ENODEV;
	}
	gpio_pin_configure_dt(&status_led, GPIO_OUTPUT_ACTIVE);
	while (1) {
		gpio_pin_toggle_dt(&status_led);
		k_msleep(1000);
	}
}

