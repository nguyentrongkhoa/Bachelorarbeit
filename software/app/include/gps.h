#ifndef GPS_H
#define GPS_H

#include <zephyr/types.h>
#include <zephyr/errno.h>
#include <zephyr/device.h>

int gps_init(void);
void gps_print_raw_data(void);

#endif