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

#include <zephyr/lorawan/lorawan.h>

#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "gps.h"
#include "led.h"
#include "lora.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_DBG);

uint8_t dev_eui64[8]; // 8 bytes or 64 bits
char dev_eui64_str[17]; // 16 characters for EUI-64 in hex + null terminator
int ret; // return status

#define DEV_EUI  {0x00, 0x80, 0xE1, 0x15, 0x06, 0x92, 0x66, 0x73}
#define JOIN_EUI {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00} // default for TTN
#define APP_KEY  {0x3A, 0xC3, 0xC1, 0x95, 0x56, 0x82, 0x07, 0x3B, 0x3C, 0xD0, 0xED, 0xAD, 0xB6, 0xFF, 0x1B, 0xDE} // obtained on TTN when registering a new end device
uint8_t dev_eui[]  = DEV_EUI;
uint8_t join_eui[] = JOIN_EUI;
uint8_t app_key[]  = APP_KEY;
struct lorawan_join_config join_cfg;

int main(void) {
	led_init();
	gps_init();
	lora_init();
	rf_switch_init();
	// retrieve 64-bit/8-byte DevEUI to connect to TTN
	ret = hwinfo_get_device_eui64(dev_eui64);
	if (ret < 0) {
		LOG_ERR("Cannot retrieve 64-bit DevEUI\n");
		return -1; // halt main completely
	}
	// Convert the DevEUI-64 to a hexadecimal string for easier display and use
	for (int i = 0; i < 8; i++) {
		snprintf(&dev_eui64_str[i * 2], 3, "%02X", dev_eui64[i]);
	}
	LOG_INF("Device EUI-64: %s\n", dev_eui64_str);
	// commence OTAA joining process
	join_cfg.mode = LORAWAN_ACT_OTAA;
	join_cfg.dev_eui = dev_eui;
	join_cfg.otaa.join_eui = join_eui;
	join_cfg.otaa.app_key = app_key;
	join_cfg.otaa.nwk_key = app_key;
	join_cfg.otaa.dev_nonce = 0u;

	LOG_DBG("Attempting to join network using OTAA");
	ret = lorawan_join(&join_cfg);
	if(ret < 0) {
		LOG_ERR("Failed to join LoRaWAN network");
		return -1;
	}
	// done joining network, now data can be sent in the while(1) loop

	// START: BME680
	const struct device *const dev = DEVICE_DT_GET_ANY(bosch_bme680);

    if(!device_is_ready(dev)) {
        printk("Error: %s sensor is not ready!\n", dev->name);
        return -ENODEV;
    }

    printk("BME680-Driver successfully loaded\n");

    struct sensor_value temp, press, humidity, gas;
	char tx_string[16];

	while(1) {
		// ret = lorawan_send(2, "Hello world", 11, LORAWAN_MSG_CONFIRMED);
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
			// ret = lora_send(lora_dev, dev_eui64_str, strlen(dev_eui64_str)); // send device EUI-64 instead of sensor data for testing
			ret = lorawan_send(2, dev_eui64_str, strlen(dev_eui64_str), LORAWAN_MSG_CONFIRMED);
			// ----------------------------------------------------------
			if(ret < 0) {
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

