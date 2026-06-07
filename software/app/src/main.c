/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <errno.h>

#include <zephyr/sys/util.h>
#include <zephyr/sys/printk.h>

#include <zephyr/drivers/lora.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/gpio.h>

#include <stdio.h>
#include <string.h>

#include "gps.h"
#include "led.h"
#include "lora.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_DBG);

int main(void) {
	k_msleep(5000);
	// ---------------------------
	led_init();
	gps_init();
	lora_init();
	rf_switch_init();
	// ---------------------------
	const struct device *const dev = DEVICE_DT_GET_ANY(bosch_bme680);

    if (!device_is_ready(dev)) {
        printk("Error: %s sensor is not ready!\n", dev->name);
        return -ENODEV;
    }

    printk("BME680-Driver successfully loaded\n");

    struct sensor_value temp, press, humidity, gas;
	char tx_string[16];
	int ret; // return status

	while(1) {
        if (sensor_sample_fetch(dev) < 0) {
            printk("Error: cannot read sensor data!\n");
            k_msleep(2000);
            continue;
        }
		// start reading sensor values
		else {
			sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &temp);
			double temp_double = sensor_value_to_double(&temp);
			// if sensor values should be sent as raw bytes
			// ----------------------------------------------------------
            // int16_t tx_buffer = (int16_t)(temp_double * 100.0);
			// int ret = lora_send(lora_dev, &tx_buffer, sizeof(tx_buffer));
			// ----------------------------------------------------------
			// Alternatively, sensor data can also be sent as strings
			// This is preferred when testing using GNURadio since it interpretes raw bytes as ASCII strings
			// ----------------------------------------------------------
			snprintk(tx_string, sizeof(tx_string), "%.2f", temp_double);
			ret = lora_send(lora_dev, tx_string, strlen(tx_string));
			// ----------------------------------------------------------
			if (ret < 0) {
				printk("Failed transmitting sensor data");
			}
			else {
				printk("Sensor data sent");
				led_toggle();
				k_msleep(2000);
			}
		}

		// lora_tx_test();
		// printf("Packet sent\n");
		// led_toggle();
		// k_msleep(2000);
		gps_print_raw_data();
	}
}

