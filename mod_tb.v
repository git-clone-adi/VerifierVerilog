 ```verilog
module tb;
    reg A;
    reg B;
    wire Y;
    integer errors = 0;

    // Unit Under Test (UUT) connect kar
    and_gate uut (
        .a(A),
        .b(B),
        .y(Y)
    );

    initial begin
        $monitor("Time=%0t A=%b B=%b Y=%b", $time, A, B, Y);
        
        A = 0; B = 0; #10;
        if (Y !== 0) errors = errors + 1;

        A = 0; B = 1; #10;
        if (Y !== 0) errors = errors + 1;

        A = 1; B = 0; #10;
        if (Y !== 0) errors = errors + 1;

        A = 1; B = 1; #10;
        if (Y !== 1) errors = errors + 1;

        if (errors == 0) 
            $display("[VERIFICATION_SUCCESS]");
        else 
            $display("[VERIFICATION_FAILED] Errors found: %d", errors);

        $finish;
    end
endmodule
```
