#include <zephyr/drivers/lora.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <errno.h>

#include "lora.h"

LOG_MODULE_REGISTER(lora_module, LOG_LEVEL_DBG);

#define DEFAULT_RADIO_NODE DT_ALIAS(lora0)
BUILD_ASSERT(DT_NODE_HAS_STATUS_OKAY(DEFAULT_RADIO_NODE), "No default LoRa radio specified in DT");

const struct device *const lora_dev = DEVICE_DT_GET(DEFAULT_RADIO_NODE);

int lora_init(void) {
	// lora_dev = DEVICE_DT_GET(DEFAULT_RADIO_NODE);
	struct lora_modem_config config = {0};
	int ret;

	if (!device_is_ready(lora_dev)) {
		LOG_ERR("%s Device not ready", lora_dev->name);
		return 0;
	}

	config.frequency = 868000000;
	config.bandwidth = BW_125_KHZ;
	config.datarate = SF_10;
	config.preamble_len = 8;
	config.coding_rate = CR_4_5;
	config.iq_inverted = false;
	config.public_network = false;
	config.tx_power = 14; // dBm
	config.tx = true;

	ret = lora_config(lora_dev, &config);
	if (ret < 0) {
		LOG_ERR("LoRa config failed");
		return 0;
	}

	// LOG_INF("Expected packet airtime: %u ms", lora_airtime(lora_dev, MAX_DATA_LEN));
	return 0;
}

void lora_tx_test(void) {
    const struct device *const lora_dev = DEVICE_DT_GET(DEFAULT_RADIO_NODE);
    int ret;

    ret = lora_send(lora_dev, "LoRa ist geil", 13);
    if (ret < 0) {
        LOG_ERR("LoRa send failed");
        return;
    }
    LOG_INF("LoRa packet sent");
}

// Retrieve RF-switch GPIOs from device tree
static const struct gpio_dt_spec rf_v1 = GPIO_DT_SPEC_GET(DT_ALIAS(rf_v1), gpios);
static const struct gpio_dt_spec rf_v2 = GPIO_DT_SPEC_GET(DT_ALIAS(rf_v2), gpios);

int rf_switch_init(void) {
    if (!gpio_is_ready_dt(&rf_v1) || !gpio_is_ready_dt(&rf_v2)) {
        LOG_ERR("GPIO-Controller for RF-Schalter not ready");
        return -ENODEV;
    }
    return 0;
}

// RX is the default state, since accidentally transmitting without antenna is harmful for the device
void config_rf_switch_rx(void) {
    gpio_pin_set_dt(&rf_v1, 1);
    gpio_pin_set_dt(&rf_v2, 0);
}

void config_rf_switch_tx(void) {
    gpio_pin_set_dt(&rf_v1, 0);
    gpio_pin_set_dt(&rf_v2, 1);
}

