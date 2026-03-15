# STM32WL Gas Sensor & LoRaWAN Firmware
> Low-power firmware for the **STM32WL55CC** using **Zephyr RTOS** and **Renode** simulation.

---

## Prerequisites

- **OS:** Linux or Windows with WSL2 (Zephyr toolchain runs on Linux only)
- **Zephyr:** Install via the [official getting started guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html)
- **STM32CubeProgrammer:** Download from [st.com](https://www.st.com/en/development-tools/stm32cubeprog.html) — needed to flash via USB
- **WSL2 USB passthrough:** Required to flash from WSL2 — follow [Microsoft's guide](https://learn.microsoft.com/en-us/windows/wsl/connect-usb)
- **VS Code (optional):** See [Zephyr VS Code integration](https://docs.zephyrproject.org/latest/develop/tools/vscode.html)

---

## Project Structure

```
my_zephyr_project/
├── boards/             # Custom board definitions (.dts)
├── src/                # Application source code (main.c)
├── renode/             # Renode simulation files
│   ├── platforms/      # Virtual hardware descriptions (.repl)
│   │   └── stm32wl.repl
│   ├── scripts/        # Simulation scenarios (.resc)
│   │   └── blinky.resc
│   └── monitor.py      # Optional: Python scripts to simulate gas sensor input
├── prj.conf            # Kconfig feature flags
├── CMakeLists.txt
└── app.overlay         # Devicetree overlay for custom peripherals
```

---

## Getting Started

### 1. Initialize the workspace

```bash
cd ~
west init zephyrproject
cd zephyrproject
west update
```

Or use the example application template as a starting point:

```bash
cd ~/zephyrproject
git clone https://github.com/zephyrproject-rtos/example-application my-app
```

### 2. Set the default board

```bash
cd my-app
west config build.board nucleo_wl55jc
```

The Zephyr board name for the NUCLEO-WL55JC is [`nucleo_wl55jc`](https://docs.zephyrproject.org/latest/boards/st/nucleo_wl55jc/doc/nucleo_wl55jc.html).

### 3. Build

```bash
west build -b nucleo_wl55jc samples/hello_world
```

The compiled binary will be at:
```
zephyrproject/my-app/build/zephyr/zephyr.elf
```

### 4. Flash to hardware

Make sure the NUCLEO is visible to WSL2 via USB passthrough, then run from the build directory:

```bash
cd build
west flash --runner openocd
```

---

## Build Commands Reference

| Action | Command |
| :--- | :--- |
| Initialize workspace | `west init -m <repo_url>` |
| Update dependencies | `west update` |
| Clean build (keep config) | `west build -t clean` |
| Pristine build (delete all artifacts) | `west build -p always -b nucleo_wl55jc` |
| Manual artifact removal | `rm -rf build/` |
| Flash to hardware | `west flash --runner openocd` |
| Launch Renode simulation | `renode your_script.resc` |
| Simulate via west | `west simulate --runner=renode` |

---

## Zephyr: The 5 Core Concepts

To avoid getting lost in the 4,000+ pages of Zephyr documentation, focus on these five pillars in order.

### 1. Devicetree (`.dts` / `app.overlay`)
The hardware description layer — tells Zephyr what peripherals exist and on which pins/buses. Always start here. If Zephyr doesn't see your sensor at the bus level, your C code will never be able to initialize the driver.

Use an `app.overlay` file to add your gas sensor without touching the Zephyr kernel source:
```dts
&i2c1 {
    my_gas_sensor: gas_sensor@48 {
        compatible = "your,sensor";
        reg = <0x48>;
    };
};
```

### 2. Kconfig (`prj.conf`)
Enables and configures software modules at compile time. Key flags for this project:
```conf
CONFIG_I2C=y          # Enable I2C bus (gas sensor)
CONFIG_LORA=y         # Enable LoRa radio driver
CONFIG_LORAWAN=y      # Enable LoRaWAN stack
CONFIG_LOG=y          # Enable logging subsystem
CONFIG_PM=y           # Enable power management
CONFIG_PM_DEVICE=y    # Enable per-device power states
```

### 3. Kernel Services (Threading & Synchronization)
Separate concerns into dedicated threads to keep the system responsive and safe:
- **Threads** — run sensor reading and LoRa transmission independently
- **Mutex** — protect the I2C bus from simultaneous access by multiple threads
- **Semaphores** — wake up a thread from an ISR when new sensor data is ready

### 4. West (Build & Flash Tool)
The meta-tool that ties everything together. All build, flash, and simulation commands go through `west`. See the command reference table above.

### 5. Renode (Virtual Hardware Simulation)
Simulate the full system — including the LoRa radio — before touching real hardware. Defined by a `.repl` platform file:

```bash
renode renode/scripts/blinky.resc
```

Useful for early firmware development and CI testing. The STM32WL platform classes are available in the [Renode infrastructure repository](https://github.com/renode/renode-infrastructure/tree/master/src/Emulator). For a multi-node wireless simulation reference, see the [nRF52840 BLE example script](https://github.com/renode/renode/blob/master/scripts/multi-node/nrf52840-ble-zephyr.resc).

Renode wireless simulation uses two key commands:
- `connector` — links virtual radio peripherals between nodes
- `emulate` — starts the wireless medium simulation

---

## Useful Links

| Resource | URL |
| :--- | :--- |
| Zephyr Getting Started | https://docs.zephyrproject.org/latest/develop/getting_started/index.html |
| Zephyr LoRaWAN API | https://docs.zephyrproject.org/latest/connectivity/lora_lorawan/index.html |
| Zephyr Power Management | https://docs.zephyrproject.org/latest/subsystems/power_management/index.html |
| NUCLEO-WL55JC board docs | https://docs.zephyrproject.org/latest/boards/st/nucleo_wl55jc/doc/nucleo_wl55jc.html |
| West documentation | https://docs.zephyrproject.org/latest/develop/west/index.html |
| Build & flash guide | https://docs.zephyrproject.org/latest/develop/application/index.html |
| WSL2 USB passthrough | https://learn.microsoft.com/en-us/windows/wsl/connect-usb |
| STM32CubeProgrammer | https://www.st.com/en/development-tools/stm32cubeprog.html |
| Renode infrastructure | https://github.com/renode/renode-infrastructure/tree/master/src/Emulator |
| Example application | https://github.com/zephyrproject-rtos/example-application |

---

## Miscellaneous

Remove Windows Zone.Identifier metadata files that WSL sometimes creates:
```bash
find . -name "*:Zone.Identifier" -type f -delete
```