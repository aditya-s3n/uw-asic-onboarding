<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

The design operates at **10 MHz** and uses SPI communication at **\~100 KHz** to configure registers that control output enables, PWM enables, and duty cycles. The system comprises two main modules: an **SPI Peripheral** for register management and a **PWM Peripheral** for signal generation

## How to test

* **Mode 0**: Data sampled on rising `SCLK` edge, valid on falling edge.
* **No CIPO**: Read operations are ignored; only writes are supported.
* **Clock Domain Crossing (CDC)**: Synchronized using a 2-stage flip-flop chain to prevent metastability.
* **Fixed Transaction Length**: 16 clock cycles per transaction (1 R/W bit + 7 address bits + 8 data bits).

| Addr | Register | Description | Reset Value |
|----|----|----|----|
| `0x00` | `en_reg_out_7_0` | Enable outputs on `uo_out[7:0]`   | `0x00`   |
| `0x01` | `en_reg_out_15_8` | Enable outputs on `uio_out[7:0]`   | `0x00`   |
| `0x02` | `en_reg_pwm_7_0` | Enable PWM for `uo_out[7:0]`   | `0x00`   |
| `0x03` | `en_reg_pwm_15_8` | Enable PWM for `uio_out[7:0]`   | `0x00`   |
| `0x04` | `pwm_duty_cycle` | PWM Duty Cycle ( `0x00`=0%, `0xFF`=100%) | `0x00`   |


## External hardware

An external microcontroller (or any SPI controller) is needed to write the registers over SPI
