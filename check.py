import subprocess
import re

def run_yosys_synthesis(design_file, top_module_name):
    """
    Yosys ko background mein chalata hai aur area/cell count nikalta hai.
    """
    # Yosys command: Read Verilog, synthesize it, and print stats
    yosys_script = f"""
    read_verilog {design_file}
    synth -top {top_module_name}
    stat
    """
    
    cmd = ["yosys", "-p", yosys_script]
    
    try:
        print("⚙️ Running Logic Synthesis via Yosys...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)  # Debug: Print Yosys output
        output = result.stdout
        
        # Regex to extract "Number of cells:" from Yosys stat report
        # Purana: match = re.search(r'Number of cells:\s+(\d+)', output)
        # Naya (Stronger):
        match = re.search(r'(\d+)\s+cells', output)
        if match:
            cell_count = int(match.group(1))
            return True, cell_count, output
        else:
            return False, 0, "ERROR: Could not find cell count in Yosys output."
            
    except subprocess.CalledProcessError as e:
        return False, 0, f"SYNTHESIS FAILED:\n{e.stderr}"

# --- Testing the Analyzer ---
if __name__ == "__main__":
    success, cells, log = run_yosys_synthesis("module.v", "and_gate")
    if success:
        print(f"📊 Total Hardware Cells Used: {cells}")
    else:
        print(log)