module tb;
    reg [3:0] request;
    reg enable;
    wire [1:0] grant;
    wire valid;
    integer i;
    integer errors = 0;

    priority_encoder_4bit uut (
        .request(request),
        .enable(enable),
        .grant(grant),
        .valid(valid)
    );

    // task signature: (r, e, g_exp[1:0], v_exp)
    task check_logic(input [3:0] r, input e, input [1:0] g_exp, input v_exp);
        begin
            if (grant !== g_exp || valid !== v_exp) begin
                $display("FAIL: req=%b en=%b | got grant=%b valid=%b | exp grant=%b valid=%b",
                          r, e, grant, valid, g_exp, v_exp);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        for (i = 0; i < 32; i = i + 1) begin
            {enable, request} = i;
            #10;

            if (!enable)
                check_logic(request, enable, 2'b00, 1'b0);
            else if (request[3])
                check_logic(request, enable, 2'b11, 1'b1);   // g_exp first, v_exp second
            else if (request[2])
                check_logic(request, enable, 2'b10, 1'b1);
            else if (request[1])
                check_logic(request, enable, 2'b01, 1'b1);
            else if (request[0])
                check_logic(request, enable, 2'b00, 1'b1);
            else
                check_logic(request, enable, 2'b00, 1'b0);
        end

        if (errors == 0)
            $display("[VERIFICATION_SUCCESS]");
        else
            $display("[VERIFICATION_FAILED] Total errors: %0d", errors);

        $finish;
    end
endmodule