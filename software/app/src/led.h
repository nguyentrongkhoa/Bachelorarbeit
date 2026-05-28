#ifndef LED_H
#define LED_H

#include <zephyr/types.h>
#include <zephyr/device.h>

int led_init(void);
void led_blink(int delay_ms);

#endif