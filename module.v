module priority_encoder_4bit(
    input [3:0] request,
    input enable,
    output reg [1:0] grant,
    output reg valid
);
    always @(*) begin
        grant = 2'b00;
        valid = 1'b0;
        if (enable) begin
            casez (request)
                4'b1???: begin grant = 2'b11; valid = 1'b1; end
                4'b01??: begin grant = 2'b10; valid = 1'b1; end
                4'b001?: begin grant = 2'b01; valid = 1'b1; end
                4'b0001: begin grant = 2'b00; valid = 1'b1; end
                default: begin grant = 2'b00; valid = 1'b0; end
            endcase
        end
    end
endmodule