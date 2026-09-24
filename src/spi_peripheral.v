`default_nettype none

module spi_peripheral (
    input wire clk;
    input wire rst_n;
    input wire COPI;
    input wire nCS;
    input wire SCLK;
    output reg  [7:0] en_reg_out_7_0,   // addr 0x00
    output reg  [7:0] en_reg_out_15_8,  // addr 0x01
    output reg  [7:0] en_reg_pwm_7_0,   // addr 0x02
    output reg  [7:0] en_reg_pwm_15_8,  // addr 0x03
    output reg  [7:0] pwm_duty_cycle    // addr 0x04
);





endmodule