`default_nettype none

module spi_peripheral (
    input wire clk,
    input wire rst_n,
    input wire COPI,
    input wire nCS,
    input wire SCLK,
    output reg  [7:0] en_reg_out_7_0,   // addr 0x00
    output reg  [7:0] en_reg_out_15_8,  // addr 0x01
    output reg  [7:0] en_reg_pwm_7_0,   // addr 0x02
    output reg  [7:0] en_reg_pwm_15_8,  // addr 0x03
    output reg  [7:0] pwm_duty_cycle    // addr 0x04
);

    localparam max_address = 7'h04;

    // Synchronizer chains
    reg SCLK_sync1, SCLK_sync2, SCLK_sync3;
    reg nCS_sync1, nCS_sync2, nCS_sync3;
    reg COPI_sync1, COPI_sync2;

    // Edge detection on the two oldest samples
    wire SCLK_posedge = SCLK_sync2 & ~SCLK_sync3;
    wire nCS_posedge  = nCS_sync2 & ~nCS_sync3;

    // Transaction state
    reg [15:0] shift_reg;   
    reg [4:0] bit_count;
    reg transaction_ready;
    reg transaction_processed;

    wire rw = shift_reg[15];
    wire [6:0] address = shift_reg[14:8];
    wire [7:0] data = shift_reg[7:0];

    // Synchronize SPI inputs into the clk domain
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            SCLK_sync1 <= 1'b0;
            SCLK_sync2 <= 1'b0;
            SCLK_sync3 <= 1'b0;
            nCS_sync1 <= 1'b1;
            nCS_sync2 <= 1'b1;
            nCS_sync3 <= 1'b1;
            COPI_sync1 <= 1'b0;
            COPI_sync2 <= 1'b0;
        end else begin
            SCLK_sync1 <= SCLK;
            SCLK_sync2 <= SCLK_sync1;
            SCLK_sync3 <= SCLK_sync2;
            nCS_sync1 <= nCS;
            nCS_sync2 <= nCS_sync1;
            nCS_sync3 <= nCS_sync2;
            COPI_sync1 <= COPI;
            COPI_sync2 <= COPI_sync1;
        end
    end

    // Process SPI protocol in the clk domain
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg <= 16'd0;
            bit_count <= 5'd0;
            transaction_ready <= 1'b0;
        end else if (nCS_sync2 == 1'b0) begin
            if (SCLK_posedge && bit_count < 5'd16) begin
                shift_reg <= {shift_reg[14:0], COPI_sync2};
                bit_count <= bit_count + 1'b1;
            end
        end else begin
            // When nCS goes high (transaction ends), validate the complete transaction
            if (nCS_posedge) begin
                if (bit_count == 5'd16) begin
                    transaction_ready <= 1'b1;
                end
            end else if (transaction_processed) begin
                // Clear ready flag once processed
                transaction_ready <= 1'b0;
            end
            bit_count <= 5'd0;
        end
    end

    // Update registers only after the complete transaction has finished and been validated
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            en_reg_out_7_0 <= 8'h00;
            en_reg_out_15_8 <= 8'h00;
            en_reg_pwm_7_0 <= 8'h00;
            en_reg_pwm_15_8 <= 8'h00;
            pwm_duty_cycle <= 8'h00;
            transaction_processed <= 1'b0;
        end else if (transaction_ready && !transaction_processed) begin
            // Only writes to valid addresses update registers
            if (rw && address <= max_address) begin
                case (address)
                    7'h00: en_reg_out_7_0  <= data;
                    7'h01: en_reg_out_15_8 <= data;
                    7'h02: en_reg_pwm_7_0  <= data;
                    7'h03: en_reg_pwm_15_8 <= data;
                    7'h04: pwm_duty_cycle  <= data;
                    default: ;
                endcase
            end
            transaction_processed <= 1'b1;
        end else if (!transaction_ready && transaction_processed) begin
            // Reset processed flag when ready flag is cleared
            transaction_processed <= 1'b0;
        end
    end

endmodule
