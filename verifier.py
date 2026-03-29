import subprocess
import os

def run_verification(design_file, tb_file, output_executable="sim.vvp", timeout_sec=5):
    """
    Compiles and runs a Verilog design and testbench using Icarus Verilog.
    Returns: tuple (bool status, str logs)
    """
    # 1. Sanity Check: Files exist karte hain ya nahi?
    if not os.path.exists(design_file):
        return False, f"SYSTEM ERROR: Design file '{design_file}' missing."
    if not os.path.exists(tb_file):
        return False, f"SYSTEM ERROR: Testbench file '{tb_file}' missing."

    # 2. Compilation Phase (iverilog)
    compile_cmd = ["iverilog", "-o", output_executable, design_file, tb_file]
    try:
        # capture_output captures stdout and stderr. check=True raises exception if exit code != 0
        subprocess.run(compile_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        # AI ne syntax error kiya hai
        return False, f"COMPILATION FAILED:\n{e.stderr.strip()}"

    # 3. Simulation Phase (vvp)
    sim_cmd = ["vvp", output_executable]
    try:
        # CRITICAL: timeout is mandatory. AI might create a zero-delay infinite loop.
        sim_process = subprocess.run(sim_cmd, capture_output=True, text=True, timeout=timeout_sec)
        output = sim_process.stdout
    except subprocess.TimeoutExpired:
        # AI ne logic f*ck up kar diya, infinite loop ban gaya
        return False, f"SIMULATION TIMEOUT: Execution exceeded {timeout_sec} seconds. Possible infinite combinational loop."
    except Exception as e:
        return False, f"SIMULATION CRASHED:\n{str(e)}"

    # 4. Parsing the Result
    # Tera testbench strictly yeh output dena chahiye agar sab sahi hai toh
    if "[VERIFICATION_SUCCESS]" in output:
        return True, "PASS: All tests cleared."
    else:
        # Agar fail hua, toh output return kar taaki aage AI ko pata chale kya galat tha
        return False, f"VERIFICATION FAILED. Output Log:\n{output.strip()}"

# --- Testing the Engine ---
if __name__ == "__main__":
    # Dummy testing ke liye
    module_v = "module.v"
    testbench_v = "tb.v"
    
    print(f"Running Core Engine on {module_v} and {testbench_v}...")
    is_valid, report = run_verification(module_v, testbench_v)
    
    if is_valid:
        print("\n✅ STATUS: SUCCESS")
    else:
        print("\n❌ STATUS: FAILED")
    
    print("-" * 40)
    print(report)
    print("-" * 40)
