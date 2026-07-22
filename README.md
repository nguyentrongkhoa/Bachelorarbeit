# LoRaWAN Sensor Node for Hazardous Areas

Bachelor thesis project at **Berliner Hochschule für Technik (BHT)**
**Duration:** April 2026 – July 2026

![code](https://img.shields.io/github/actions/workflow/status/nguyentrongkhoa/Bachelorarbeit/lint.yml?branch=master&label=code&style=flat-square)
![build](https://img.shields.io/github/actions/workflow/status/nguyentrongkhoa/Bachelorarbeit/build.yml?branch=master&label=build&style=flat-square)
![kicad](https://img.shields.io/badge/KiCad-v10.0-blue)
![zephyr](https://img.shields.io/badge/Zephyr-v4.3.99-blue)
![zephyrsdk](https://img.shields.io/badge/ZephyrSDK-v0.17.4-blue)

## Overview

This repository contains the work for a bachelor thesis focused on the development of a LoRaWAN-based sensor node designed for deployment in hazardous areas (*Gefahrgebiete*), such as environments with restricted access, elevated risk, or conditions unsuitable for frequent human intervention. The goal is to provide a robust, low-power, long-range wireless sensor platform suitable for remote monitoring in such conditions.

The project is divided into three main parts:

1. **Hardware Design** — PCB and schematic design created in KiCad, maintained in a separate repository and included here as a Git submodule. Visit the submodule's main page for further documentation.
2. **Firmware** — Embedded firmware built on Zephyr RTOS, handling sensor data acquisition, power management, and LoRaWAN communication.
3. **Tests** — Contains current consumption measurements using Nordic's PPK2 and antenna coverage planning in QGIS. More details can be found in the thesis. 
4. **Thesis** — The written bachelor thesis document, typeset in LaTeX using the template provided by Prof. Dr. Sven Tschirley.

## Repository Structure

```
.
├── hardware/       # KiCad hardware design (included here as a submodule)
├── software/       # Zephyr RTOS firmware source
├── tests/       
├── thesis         # bachelor thesis, Latex source code is somewhere else
└── README.md
```

## Hardware

- Designed in **KiCad** 10
- Maintained as a separate repository, linked here via Git submodule
- Focus on low power consumption and durability for deployment in hazardous environments

To initialize the hardware submodule after cloning:

```bash
git submodule update --init --recursive
```

To propagate all changes from the hardware submodule into this repo, use

```bash
git submodule update --remote --merge
```

## Firmware

- Built on **Zephyr RTOS**
- Implements LoRaWAN connectivity for long-range, low-power data transmission
- Handles sensor interfacing and power-efficient operation

*(Build and flashing instructions to be added as development progresses.)*

## Thesis

- Written in **LaTeX**
- Documents the design decisions, implementation, and evaluation of the sensor node

## Project Timeline

| Phase | Period |
|---|---|
| Bachelor Thesis | April 2026 – July 2026 |

## Institution

Berliner Hochschule für Technik (BHT)


