# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    
    Parameters:
    - r_w: boolean, True for write, False for read
    - address: int, 7-bit address (0-127)
    - data: LogicArray or int, 8-bit data
    """
    # Convert data to int if it's a LogicArray
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Validate inputs
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # Combine RW and address into first byte
    first_byte = (int(r_w) << 7) | address
    # Start transaction - pull CS low
    sclk = 0
    ncs = 0
    bit = 0
    # Set initial state with CS low
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send first byte (RW + Address)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send second byte (Data)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End transaction - return CS high
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")


TIMEOUT_CYCLES = 20000
@cocotb.test()
async def test_pwm_freq(dut):
    # Write your test here

    dut._log.info("Start PWM Frequency test")
 
    # 1. Start the 10 MHz clock and reset the chip
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
 
    dut.ena.value = 1
    dut.ui_in.value = ui_in_logicarray(1, 0, 0) 
    dut.uio_in.value = 0
 
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
 
    # 2. Turn on PWM on uo_out[0] at 50% duty
    await send_spi_transaction(dut, 1, 0x00, 0x01)  # enable output bit 0
    await send_spi_transaction(dut, 1, 0x02, 0x01)  # PWM mode on bit 0
    await send_spi_transaction(dut, 1, 0x04, 0x80)  # 50% duty
 

    cycle_count = 0

    # 3. Wait for the FIRST rising edge (0 -> 1)
    t_rise1 = None
    prev = int(dut.uo_out.value) & 0x1
 
    for i in range(TIMEOUT_CYCLES):
        await RisingEdge(dut.clk)

        cycle_count += 1
        cur = int(dut.uo_out.value) & 0x1
        if prev == 0 and cur == 1:
            t_rise1 = cycle_count
            break

        prev = cur
 
    assert t_rise1 is not None, f"Timed out: never saw a 1st rising edge"
 
    # 4. Wait for the second rising edge 
    t_rise2 = None
    prev = int(dut.uo_out.value) & 0x1
 
    for i in range(TIMEOUT_CYCLES):
        await RisingEdge(dut.clk)

        cycle_count += 1
        cur = int(dut.uo_out.value) & 0x1
        if prev == 0 and cur == 1:
            t_rise2 = cycle_count
            break

        prev = cur
 
    assert t_rise2 is not None, "Timed out: never saw a 2nd rising edge"
 
    # 5. Period -> frequency, must be 3 kHz +/- 1%
    period_ns = (t_rise2 - t_rise1) * 100  
    freq_hz = 1e9 / period_ns    # 1e9 converts ns to seconds
 
    dut._log.info(f"Period = {period_ns} ns, Frequency = {freq_hz:.1f} Hz")
 
    assert 2970 <= freq_hz <= 3030, f"Frequency {freq_hz:.1f} Hz is outside 2970-3030 Hz"

    dut._log.info("PWM Frequency test completed successfully")


@cocotb.test()
async def test_pwm_duty(dut):
    # Write your test here

    dut._log.info("Start PWM Duty Cycle test")
 
    # 1. Start the 10 MHz clock and reset the chip
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
 
    dut.ena.value = 1
    dut.ui_in.value = ui_in_logicarray(1, 0, 0)
    dut.uio_in.value = 0
 
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
 

    # 2. Turn on PWM on uo_out[0]
    await send_spi_transaction(dut, 1, 0x00, 0x01)  # enable output bit 0
    await send_spi_transaction(dut, 1, 0x02, 0x01)  # PWM mode on bit 0
 
    # CASE A: 0% duty  ->  pin is ALWAYS LOW
    dut._log.info("Testing 0% duty (0x00)")
    await send_spi_transaction(dut, 1, 0x04, 0x00)
 
    for cycle in range(TIMEOUT_CYCLES):
        await RisingEdge(dut.clk)
        pin = int(dut.uo_out.value) & 0x1
        assert pin == 0, f"0% duty: pin went HIGH at cycle {cycle}"
 
    dut._log.info("0% duty passed: pin stayed low")
 
    # CASE B: 100% duty  ->  pin is ALWAYS HIGH
    dut._log.info("Testing 100% duty (0xFF)")
    await send_spi_transaction(dut, 1, 0x04, 0xFF)
 
    for cycle in range(TIMEOUT_CYCLES):
        await RisingEdge(dut.clk)
        pin = int(dut.uo_out.value) & 0x1
        assert pin == 1, f"100% duty: pin went LOW at cycle {cycle}"
 
    dut._log.info("100% duty passed: pin stayed high")

    # CASE C: 50% duty  ->  measure high time vs. full period
    dut._log.info("Testing 50% duty (0x80)")
    await send_spi_transaction(dut, 1, 0x04, 0x80)
 
    # Count clock cycles to measure time (1 cycle = 100 ns)
    cycle_count = 0

    t_rise1 = None
    prev = int(dut.uo_out.value) & 0x1
 
    for i in range(TIMEOUT_CYCLES):
        await RisingEdge(dut.clk)

        cycle_count += 1
        cur = int(dut.uo_out.value) & 0x1
        if prev == 0 and cur == 1:
            t_rise1 = cycle_count
            break

        prev = cur
 
    assert t_rise1 is not None, "50% duty: timed out waiting for rising edge"
 
    t_fall = None
    prev = int(dut.uo_out.value) & 0x1
 
    for i in range(TIMEOUT_CYCLES):

        await RisingEdge(dut.clk)
        cycle_count += 1
        cur = int(dut.uo_out.value) & 0x1
        if prev == 1 and cur == 0:
            t_fall = cycle_count
            break

        prev = cur
 
    assert t_fall is not None, "50% duty: timed out waiting for falling edge"
 
    t_rise2 = None
    prev = int(dut.uo_out.value) & 0x1
 
    for i in range(TIMEOUT_CYCLES):
        await RisingEdge(dut.clk)

        cycle_count += 1
        cur = int(dut.uo_out.value) & 0x1
        if prev == 0 and cur == 1:
            t_rise2 = cycle_count
            break
        
        prev = cur
 
    assert t_rise2 is not None, "50% duty: timed out waiting for 2nd rising edge"
 
    high_time = (t_fall - t_rise1) * 100   # cycles -> ns
    period = (t_rise2 - t_rise1) * 100
    duty_percent = high_time / period * 100
 
    dut._log.info(f"High = {high_time} ns, Period = {period} ns, Duty = {duty_percent:.2f}%")
 
    assert 49 <= duty_percent <= 51, f"50% duty: measured {duty_percent:.2f}%, expected 49-51%"

    dut._log.info("PWM Duty Cycle test completed successfully")
