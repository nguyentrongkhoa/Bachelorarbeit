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
#include "lora.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_DBG);

#define MAX_DATA_LEN 5
char data[MAX_DATA_LEN] = {'h', 'e', 'l', 'l', 'o'};

int main(void) {
	k_msleep(2000);
	LOG_DBG("Program started");

	led_init();
	gps_init();
	lora_init();
	rf_switch_init();

	while(1) {
		lora_tx_test();
		led_toggle();
		k_msleep(1000);
		gps_print_raw_data();
	}
}

