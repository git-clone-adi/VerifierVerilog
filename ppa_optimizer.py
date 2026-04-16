# import os
# import re
# import shutil
# import subprocess
# from verifier import run_verification
# from auto_patcher import prompt_llm, extract_verilog

# YOSYS_EXE = shutil.which("yosys") or r"E:\#TOOLS\oss-cad-suite\bin\yosys.exe" 
# DESIGN_FILE = "module.v"
# TOP_MODULE = "priority_encoder_4bit"

# def get_final_cell_count(design_file, module_name):
#     script = f"read_verilog {design_file}; synth -top {module_name}; stat;"
#     try:
#         res = subprocess.run([YOSYS_EXE, "-p", script], capture_output=True, text=True)
#         matches = re.findall(r'(\d+)\s+cells', res.stdout)
#         return int(matches[-1]) if matches else None
#     except Exception as e:
#         print(f"Error during synthesis: {e}")
#         return None

# def start_ppa_engine():
#     print("💎 Initializing Autonomous PPA Optimizer...")

#     initial_area = get_final_cell_count(DESIGN_FILE, TOP_MODULE)
#     print(f"📊 Baseline Area: {initial_area} cells\n")

#     if initial_area is None:
#         print("❌ FAILED: Could not analyze baseline area.")
#         return

#     with open(DESIGN_FILE, "r") as f:
#         original_code = f.read()

#     current_code = original_code
#     error_feedback = ""

#     for attempt in range(1, 4):
#         print(f"--- 🔄 Iteration {attempt}/3 ---")
        
#         opt_prompt = (
#             f"The current Verilog code uses {initial_area} logic cells. "
#             "Your task is to optimize it while strictly maintaining the 3-input majority voter logic. "
#             "CRITICAL RULES: "
#             "1. Derive the boolean logic internally. "
#             "2. DO NOT output any text, explanations, or K-Map derivations. "
#             "3. Provide ONLY the final optimized Verilog code inside a single ```verilog ``` block."
#             f"{error_feedback}"
#         )

#         raw_response = prompt_llm(current_code, opt_prompt)
        
#         # FIX: Check if we actually got a response
#         if not raw_response or raw_response.strip() == "":
#             print("🛑 Breaking loop: No response from AI (network error?).")
#             break 

#         optimized_code = extract_verilog(raw_response)
        
#         # FIX: Don't write if extraction failed
#         if not optimized_code or "module" not in optimized_code:
#             print("⚠️ Skipping iteration: Failed to extract Verilog.")
#             continue

#         with open("optimized_temp.v", "w") as f:
#             f.write(optimized_code)

#         print("🔍 Verifying AI logic...")
#         v_result = run_verification("optimized_temp.v", "tb.v")

#         if v_result.passed:
#             final_area = get_final_cell_count("optimized_temp.v", TOP_MODULE)
#             print(f"📉 New Area: {final_area} cells")

#             original_lines = len(current_code.splitlines())
#             optimized_lines = len(optimized_code.splitlines())
#             print(f"📏 Original lines: {original_lines}, Optimized lines: {optimized_lines}")

#             if final_area is not None and (final_area < initial_area or (final_area == initial_area and optimized_lines < original_lines)):
#                 print("🎉 SUCCESS! AI improved the design (area reduced or code simplified). Patching module.v.")
#                 with open(DESIGN_FILE, "w") as f:
#                     f.write(optimized_code)
#                 return
#             else:
#                 print("⚠️ REJECTED: AI logic correct, but no improvement in area or code length. Trying again...")
#                 error_feedback = f"\nPREVIOUS ATTEMPT FAILED: The code was functionally correct but used {final_area} cells and {optimized_lines} lines. You must use FEWER cells or FEWER lines than {initial_area} cells and {original_lines} lines."
#         else:
#             print("❌ REJECTED: AI logic is broken!")
#             # Feeding the testbench error back to the AI
#             error_feedback = f"\nPREVIOUS ATTEMPT FAILED SIMULATION. Error Log:\n{v_result.message}\nFix the logic and try again."
#             # Update current_code so AI sees its own mistake in the next loop
#             current_code = optimized_code 

#     print("\n💀 MAX ATTEMPTS REACHED. AI couldn't optimize it safely. Keeping original code.")
#     if os.path.exists("optimized_temp.v"):
#         os.remove("optimized_temp.v")

# if __name__ == "__main__":
#     start_ppa_engine()

import os
import re
import shutil
import subprocess
from verifier import run_verification
from auto_patcher import prompt_llm, extract_verilog

# ═══════════════════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

YOSYS_EXE = shutil.which("yosys") or r"E:\#TOOLS\oss-cad-suite\bin\yosys.exe"
DESIGN_FILE = "module.v"
TB_FILE     = "tb.v"
TOP_MODULE  = "priority_encoder_4bit"
MAX_ITER    = 3
# ═══════════════════════════════════════════════════════════════════════════════


def get_cell_count(verilog_file: str, module_name: str) -> int | None:
    script = f"read_verilog {verilog_file}; synth -top {module_name}; stat;"
    try:
        res = subprocess.run([YOSYS_EXE, "-p", script],
                             capture_output=True, text=True)
        matches = re.findall(r'(\d+)\s+cells', res.stdout)
        return int(matches[-1]) if matches else None
    except FileNotFoundError:
        print(f"❌ Yosys not found: {YOSYS_EXE}")
        return None
    except Exception as e:
        print(f"❌ Yosys error: {e}")
        return None


def start_ppa_engine():
    print("💎 Initializing Autonomous PPA Optimizer...")

    # ── Baseline ──────────────────────────────────────────────────────────────
    initial_area = get_cell_count(DESIGN_FILE, TOP_MODULE)
    if initial_area is None:
        print("❌ Cannot measure baseline area. Check Yosys path.")
        return

    with open(DESIGN_FILE, "r") as f:
        original_code = f.read()
    original_lines = len(original_code.splitlines())

    print(f"📊 Baseline Area : {initial_area} cells")
    print(f"📏 Baseline Lines: {original_lines}\n")

    # ── Must pass testbench before optimizing ─────────────────────────────────
    print("🔍 Checking baseline passes testbench...")
    baseline = run_verification(DESIGN_FILE, TB_FILE)
    if not baseline.passed:
        print("❌ ABORTED: Original design fails verification. Run auto_patcher.py first.")
        print(baseline)
        return
    print("✅ Baseline verification passed.\n")

    current_code  = original_code
    current_area  = initial_area
    current_lines = original_lines
    error_feedback = ""
    best_improved  = False

    # ── Optimization loop ─────────────────────────────────────────────────────
    for attempt in range(1, MAX_ITER + 1):
        print(f"--- 🔄 Iteration {attempt}/{MAX_ITER} ---")

        task = (
            f"You are given a Verilog module '{TOP_MODULE}' (4-bit priority encoder).\n"
            f"It currently uses {current_area} logic cells and {current_lines} lines.\n\n"
            "GOAL: Rewrite it to use FEWER cells OR FEWER lines while keeping\n"
            "all port names and input→output behavior 100% identical.\n\n"
            "RULES:\n"
            "1. Keep exact same module name and port list.\n"
            "2. Use casez (not casex).\n"
            "3. Output ONLY Verilog inside a single ```verilog ``` block.\n"
            f"{error_feedback}"
        )

        raw = prompt_llm(current_code, task)
        if not raw or not raw.strip():
            print("🛑 No response from AI. Stopping.")
            break

        optimized_code = extract_verilog(raw)
        if not optimized_code or "module" not in optimized_code:
            print("⚠️  Could not extract valid Verilog. Skipping.")
            error_feedback = "\nPREVIOUS ATTEMPT: output was not valid Verilog. Use ```verilog ``` block."
            continue

        with open("optimized_temp.v", "w") as f:
            f.write(optimized_code)

        # ── Functional check ──────────────────────────────────────────────────
        print("🔍 Verifying AI output...")
        v = run_verification("optimized_temp.v", TB_FILE)

        if not v.passed:
            print(f"❌ REJECTED: Simulation failed!\n{v}")
            error_feedback = (
                f"\nPREVIOUS ATTEMPT FAILED simulation:\n"
                f"  Reason: {v.message}\n"
                f"  Output: {v.stdout.strip()[:400]}\n"
                "Fix the logic."
            )
            current_code = optimized_code
            continue

        # ── Area check ────────────────────────────────────────────────────────
        new_area  = get_cell_count("optimized_temp.v", TOP_MODULE)
        new_lines = len(optimized_code.splitlines())
        print(f"📉 New Area : {new_area} cells  (was {current_area})")
        print(f"📏 New Lines: {new_lines}  (was {current_lines})")

        area_better  = new_area is not None and new_area < current_area
        lines_better = new_lines < current_lines
        area_same    = new_area is not None and new_area == current_area

        if area_better or (area_same and lines_better):
            print("🎉 IMPROVEMENT! Patching module.v...\n")
            with open(DESIGN_FILE, "w") as f:
                f.write(optimized_code)
            current_code  = optimized_code
            current_area  = new_area
            current_lines = new_lines
            error_feedback = ""
            best_improved  = True
        else:
            print("⚠️  REJECTED: Correct but no improvement.")
            error_feedback = (
                f"\nPREVIOUS ATTEMPT was correct but NOT better:\n"
                f"  Got {new_area} cells / {new_lines} lines.\n"
                f"  Must beat: <{current_area} cells OR <{current_lines} lines.\n"
                "Try boolean minimization or assign statements instead of always block."
            )

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if os.path.exists("optimized_temp.v"):
        os.remove("optimized_temp.v")

    print("\n" + "═" * 50)
    if best_improved:
        print(f"✅ FINAL: {initial_area}→{current_area} cells, "
              f"{original_lines}→{current_lines} lines.")
    else:
        print("💀 No improvement found. Original code kept.")
    print("═" * 50)


if __name__ == "__main__":
    start_ppa_engine()