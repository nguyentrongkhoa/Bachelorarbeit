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
#include <zephyr/drivers/hwinfo.h>

#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "gps.h"
#include "led.h"
#include "lora.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_DBG);

uint8_t hw_id[12]; // 12 bytes or 96 bits
uint8_t dev_eui64[8]; // 8 bytes or 64 bits
char dev_eui64_str[17]; // 16 characters for EUI-64 in hex + null terminator
int ret; // return status

#define LORAWAN_DEV_EUI  {0x68, 0x76, 0x62, 0x52, 0x48, 0x01, 0x50, 0x38}
#define LORAWAN_JOIN_EUI {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00} // default for TTN
#define LORAWAN_APP_KEY  {0x04, 0x2F, 0xF6, 0x86, 0x22, 0xE9, 0x3B, 0xCF, 0x58, 0x8E, 0x5A, 0x6E, 0xCD, 0xA2, 0xF8, 0x3C}

int main(void) {
	k_msleep(5000);
	// ---------------------------
	led_init();
	gps_init();
	lora_init();
	rf_switch_init();
	// ---------------------------

	// Manually generate 64-bit DevEUI from 96-bit hardware ID to connect to LoRaWAN network servers
	hwinfo_get_device_id(hw_id, sizeof(hw_id)); 
	//calculate 64-bit DevEUI using standard EUI-64 generation method (XOR first 8 bytes with last 4 bytes)
	for (int i = 0; i < 8; i++) {
		dev_eui64[i] = hw_id[i] ^ hw_id[i + 4]; 
	}
	// Convert the EUI-64 to a hexadecimal string for easier display and use
	for (int i = 0; i < 8; i++) {
		snprintf(&dev_eui64_str[i * 2], 3, "%02X", dev_eui64[i]);
	}
	LOG_INF("Device EUI-64: %s\n", dev_eui64_str);
	// -------------------------------------------------------------

	// START: BME680
	const struct device *const dev = DEVICE_DT_GET_ANY(bosch_bme680);

    if (!device_is_ready(dev)) {
        printk("Error: %s sensor is not ready!\n", dev->name);
        return -ENODEV;
    }

    printk("BME680-Driver successfully loaded\n");

    struct sensor_value temp, press, humidity, gas;
	char tx_string[16];

	while(1) {
        if (sensor_sample_fetch(dev) < 0) {
            LOG_INF("Error: cannot read sensor data!\n");
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
			// ret = lora_send(lora_dev, tx_string, strlen(tx_string));
			ret = lora_send(lora_dev, dev_eui64_str, strlen(dev_eui64_str)); // send device EUI-64 instead of sensor data for testing
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

