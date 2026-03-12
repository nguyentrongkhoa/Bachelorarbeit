zephyr only on linux or WSL
install zephyr using [this start guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html) using wsl
zephyr nucleo board name: [nucleo_wl55jc](https://docs.zephyrproject.org/latest/boards/st/nucleo_wl55jc/doc/nucleo_wl55jc.html)

[How to build and flash](https://docs.zephyrproject.org/latest/develop/application/index.html#build-an-application)
1. Navigate to app directory <app>
2. Configure default board: `west config build.board nucleo_wl55jc`
3. `west build -b nucleo_wl55jc samples/hello_world`, zephyr.elf will be created
4. directory structure: zephyrproject/<app>/build/zephyr/zephyr.elf
5. `west flash` (run from <app>/build and not <app>)

How to clean build directory:
1. Navigate to <app>/build
2. `west build -t clean` or `west build -t pristine` to delete all generated files in the build subfolder

How to build and structure app (from template):
[Example application](https://github.com/zephyrproject-rtos/example-application)
`cd <home>/zephyrproject`
`git clone https://github.com/zephyrproject-rtos/example-application my-app`

Build app from scratch

[west](https://docs.zephyrproject.org/latest/develop/west/index.html): 
`west init` and `west update`

-----------------------------
# 🚀 STM32WL Project: Gas Sensor & LoRaWAN (Zephyr + Renode)

This project focuses on developing a low-power firmware for the **STM32WL55CC1** using the **Zephyr RTOS** ecosystem and **Renode** simulation.

---

## 🗺️ Survival Roadmap (Efficiency Focus)

To avoid getting lost in the 4,000+ pages of Zephyr documentation, focus on these **5 core pillars**:

### 1. Hardware Description: **Devicetree (.dts)**
* **Concept:** Software-independent description of the hardware (Pins, I2C, UART).
* **Key Skill:** Learning how to use `app.overlay` files to add your gas sensor without modifying the Zephyr kernel source.


### 2. Feature Configuration: **Kconfig (prj.conf)**
* **Concept:** A menu-driven system to enable/disable software modules.
* **Key Skill:** Mastering flags like `CONFIG_I2C=y`, `CONFIG_LORA=y`, and `CONFIG_LOG=y`.

### 3. System Orchestration: **Kernel Services**
* **Concept:** Managing multi-threading and timing.
* **Key Tools:** * `Threads`: Separate the sensor reading logic from the LoRa transmission logic.
    * `Mutex`: Protect the I2C bus from simultaneous access.
    * `Semaphores`: Signal a thread to wake up after an interrupt (ISR).


### 4. The Master Tool: **West**
* **Concept:** The meta-tool that handles building, flashing, and debugging.
* **Main Commands:**
    * `west build -b nucleo_wl55jc`: Compile for the target board.
    * `west flash`: Upload the binary via OpenOCD/ST-LINK.

### 5. Virtual Hardware: **Renode**
* **Concept:** Simulate the entire system (including LoRa radio) without physical hardware.
* **Key File:** `.repl` (Platform description defining the virtual PCB layout).

---

## 🛠️ Essential "Cheat Sheet" (WSL2)

| Action | Command |
| :--- | :--- |
| **Initialize Workspace** | `west init -m <repo_url>` |
| **Clean Build** | `west build -p always -b nucleo_wl55jc` |
| **Remove Build Artifacts** | `rm -rf build/` |
| **Launch Simulation** | `renode your_script.resc` |
| **Flash to Hardware** | `west flash --runner openocd` |

---

> **Engineer's Note:** Always prioritize the **Devicetree** first. If Zephyr doesn't "see" your sensor at the bus level, your C code will never be able to initialize the driver.

Simulate with renode:
`west simulate --runner=renode`

[Developing with VSCode](https://docs.zephyrproject.org/latest/develop/tools/vscode.html)

find . -name "*:Zone.Identifier" -type f -delete

mon_projet_zephyr/
├── boards/             # Tes définitions de cartes custom (.dts)
├── src/                # Ton code source C (main.c)
├── renode/             # <--- DOSSIER DÉDIÉ AUX FICHIERS DE SIMULATION
│   ├── platforms/      # Tes fichiers .repl (Hardware virtuel)
│   │   └── stm32wl.repl
│   ├── scripts/        # Tes fichiers .resc (Scénarios de test)
│   │   └── blinky.resc
│   └── monitor.py      # (Optionnel) Scripts Python pour simuler ton capteur de gaz
├── prj.conf            # Configuration Kconfig
├── CMakeLists.txt
└── app.overlay         # Ton overlay Devicetree

[Renode platform description C# classes](https://github.com/renode/renode-infrastructure/tree/master/src/Emulator)

[Renode script bluetooth](https://github.com/renode/renode/blob/master/scripts/multi-node/nrf52840-ble-zephyr.resc)

Renode wireless "commands":
    1. connector
    2. emulate
