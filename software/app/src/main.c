/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 * SPDX-License-Identifier: Apache-2.0
 */
// START sample code
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>
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
#include <errno.h>

#include "gps.h"
#include "led.h"
// #include "lora.h"

/* Customize based on network configuration */
#define LORAWAN_DEV_EUI	 { 0x00, 0x80, 0xE1, 0x15, 0x06, 0x92, 0x66, 0x73 }
#define LORAWAN_JOIN_EUI { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 }
#define LORAWAN_APP_KEY	 { 0x3A, 0xC3, 0xC1, 0x95, 0x56, 0x82, 0x07, 0x3B, 0x3C, 0xD0, 0xED, 0xAD, 0xB6, 0xFF, 0x1B, 0xDE}

#define DELAY K_MSEC(10000)

#define LOG_LEVEL CONFIG_LOG_DEFAULT_LEVEL
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(lorawan_class_a);

uint8_t dev_eui64[8]; // 8 bytes or 64 bits
char dev_eui64_str[17]; // 16 characters for EUI-64 in hex + null terminator
static uint8_t ttn_dev_nonce = 0u;
int ret; // return status

// this function will be called by zephyr when data is being read
static int lorawan_settings_set(const char *name, size_t len, settings_read_cb read_cb, void *cb_arg)
{
    const char *next;
	// check if the path "devnonce" already exists (the prefix "lorawan/" is filtered by the handler)
	// if yes, read the data from the NVS into the variable "ttn_dev_nonce" 
    if (settings_name_steq(name, "devnonce", &next) && !next) {
        if (len == sizeof(ttn_dev_nonce)) {
            // Daten physisch aus dem NVS in die Variable lesen
            read_cb(cb_arg, &ttn_dev_nonce, sizeof(ttn_dev_nonce));
            LOG_INF("DevNonce successfully loaded: %d", ttn_dev_nonce);
            return 0;
        }
    }
    return -ENOENT;
}

// link the path lorawan/ to the callback function above
static struct settings_handler lorawan_settings_handler = {
    .name = "lorawan",
    .h_set = lorawan_settings_set
};

static void dl_callback(uint8_t port, uint8_t flags, int16_t rssi, int8_t snr, uint8_t len, const uint8_t *hex_data)
{
	LOG_INF("Port %d, Pending %d, RSSI %ddB, SNR %ddBm, Time %d", port,
		flags & LORAWAN_DATA_PENDING, rssi, snr, !!(flags & LORAWAN_TIME_UPDATED));
	if (hex_data) {
		LOG_HEXDUMP_INF(hex_data, len, "Payload: ");
	}
}

static void lorwan_datarate_changed(enum lorawan_datarate dr)
{
	uint8_t unused, max_size;

	lorawan_get_payload_sizes(&unused, &max_size);
	LOG_INF("New Datarate: DR_%d, Max Payload %d", dr, max_size);
}

int main(void)
{
	led_init();
	gps_init();

	// START LoRaWAN setup block
	// ---------------------------------------------------------------

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

	// load settings to retrieve dev_nonce from NVS (if it exists)
	ret = settings_subsys_init();
	ret = settings_register(&lorawan_settings_handler);
	// this will call the callback function "lorawan_settings_set" 
	// which will load the dev_nonce from NVS into the variable "ttn_dev_nonce"
	ret = settings_load(); 

	const struct device *lora_dev;
	struct lorawan_join_config join_cfg;
	uint8_t dev_eui[] = LORAWAN_DEV_EUI;
	uint8_t join_eui[] = LORAWAN_JOIN_EUI;
	uint8_t app_key[] = LORAWAN_APP_KEY;

	struct lorawan_downlink_cb downlink_cb = {
		.port = LW_RECV_PORT_ANY,
		.cb = dl_callback
	};

	lora_dev = DEVICE_DT_GET(DT_ALIAS(lora0));
	if (!device_is_ready(lora_dev)) {
		LOG_ERR("%s: device not ready.", lora_dev->name);
		return 0;
	}

	#if defined(CONFIG_LORAWAN_REGION_EU868)
		/* If more than one region Kconfig is selected, app should set region
		* before calling lorawan_start()
		*/
		ret = lorawan_set_region(LORAWAN_REGION_EU868);
		if (ret < 0) {
			LOG_ERR("lorawan_set_region failed: %d", ret);
			return 0;
		}
	#endif

	ret = lorawan_start();
	if (ret < 0) {
		LOG_ERR("lorawan_start failed: %d", ret);
		return 0;
	}

	lorawan_register_downlink_callback(&downlink_cb);
	lorawan_register_dr_changed_callback(lorwan_datarate_changed);

	join_cfg.mode = LORAWAN_ACT_OTAA;
	join_cfg.dev_eui = dev_eui;
	join_cfg.otaa.join_eui = join_eui;
	join_cfg.otaa.app_key = app_key;
	join_cfg.otaa.nwk_key = app_key;
	join_cfg.otaa.dev_nonce = ttn_dev_nonce;

	LOG_INF("Joining network over OTAA");
	ret = lorawan_join(&join_cfg);
	if (ret < 0) {
		LOG_ERR("lorawan_join_network failed: %d", ret);
		return 0;
	}
	// blink status_led to signalize successful network join
	for(int i=0; i<=10; i++) {
		led_toggle();
		k_msleep(100); // ms
	}
	// increment dev_nonce and save back to NVS for subsequent join attempts
	ttn_dev_nonce++;
	ret = settings_save_one("lorawan/devnonce", &ttn_dev_nonce, sizeof(ttn_dev_nonce)); 

	ret = lorawan_send(2, "Start session", 13, LORAWAN_MSG_CONFIRMED);
	// END LoRaWAN setup block
	// ------------------------------------------------------

	// START: BME680
	const struct device *const bme680_dev = DEVICE_DT_GET_ANY(bosch_bme680);

    if (!device_is_ready(bme680_dev)) {
        LOG_ERR("Error: %s sensor is not ready!\n", bme680_dev->name);
        // return -ENODEV;
    }

    LOG_INF("BME680-Driver successfully loaded\n");
	// Read BME680 data
    struct sensor_value temp, press, humidity, gas;
	char bme680_tx_string[16]; // convert raw data bytes to ASCII strings for ease of debugging

	// superloop
	while (1) {
		if (sensor_sample_fetch(bme680_dev) < 0) {
            LOG_INF("Error: cannot read sensor data!\n");
            k_msleep(2000);
            continue;
        }
		else {
			sensor_channel_get(bme680_dev, SENSOR_CHAN_AMBIENT_TEMP, &temp);
			double temp_double = sensor_value_to_double(&temp);
			// if sensor values should be sent as raw bytes
			// ----------------------------------------------------------
            // int16_t tx_buffer = (int16_t)(temp_double * 100.0);
			// int ret = lora_send(lora_dev, &tx_buffer, sizeof(tx_buffer));
			// ----------------------------------------------------------
			// Alternatively, sensor data can also be sent as strings
			// This is preferred when testing using GNURadio since it interpretes raw bytes as ASCII strings
			// ----------------------------------------------------------
			snprintk(bme680_tx_string, sizeof(bme680_tx_string), "%.2f", temp_double);
			ret = lorawan_send(2, bme680_tx_string, strlen(bme680_tx_string), LORAWAN_MSG_CONFIRMED);
			/*
			* Note: The stack may return -EAGAIN if the provided data
			* length exceeds the maximum possible one for the region and
			* datarate. But since we are just sending the same data here,
			* we'll just continue.
			*/
			if (ret == -EAGAIN) {
				LOG_ERR("lorawan_send failed: %d. Continuing...", ret);
				k_sleep(DELAY);
				continue;
			}

			if (ret < 0) {
				LOG_ERR("lorawan_send failed: %d", ret);
				return 0;
			}

			LOG_INF("Data sent!");
			led_toggle();
			k_msleep(2000);
		}
	}
}
// END sample code

