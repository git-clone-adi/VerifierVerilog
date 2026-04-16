// Module for 2-input AND gate
module and_gate(
    input wire a,      // Input port 'a'
    input wire b,      // Input port 'b'
    output reg y       // Output port 'y'
);

    always @(*) begin   // Synchronous logic for combinational logic
        if (a & b) 
            y = 1;     // If both a and b are high, assign 1 to y
        else
            y = 0;     // Else assign 0 to y
    end
endmodule
