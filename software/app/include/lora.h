#ifndef CUSTOM_LORA_H
#define CUSTOM_LORA_H

int lora_init(void);
int rf_switch_init(void);
void config_rf_switch_tx(void);
void config_rf_switch_rx(void);
void lora_tx_test(void);

#endif