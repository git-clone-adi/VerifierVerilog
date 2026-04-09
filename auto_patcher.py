# import re
# import requests
# import json
# from verifier import run_verification

# # Constants
# MODEL_NAME = "deepseek-coder-v2:16b"
# DESIGN_FILE = "module.v"
# TB_FILE = "tb.v"
# MAX_ITERATIONS = 5

# def extract_verilog(llm_response: str) -> str:
#     match = re.search(r'```verilog\s*(.*?)\s*```', llm_response, re.DOTALL)
#     if match:
#         return match.group(1).strip()
    
#     # Fallback: Agar LLM ne markdown use nahi kiya, toh assume pura response code hai (Risky)
#     return llm_response.strip()

# def prompt_llm(current_code: str, error_log: str) -> str:
#     # 1. Colab se mila hua Cloudflare URL yahan paste karo
#     api_url = "https://apt-believed-fireplace-essentially.trycloudflare.com/api/chat" 
    
#     # Headers simple rahenge (No skip-warning needed!)
#     headers = {
#         "Content-Type": "application/json"
#     }
    
#     payload = {
#         "model": "deepseek-coder-v2:16b", # Ya jo bhi model tumne load kiya hai
#         "messages": [
#             {"role": "system", "content": "You are a VLSI expert. Fix Verilog. Output ONLY code in ```verilog ```."},
#             {"role": "user", "content": f"FIX THIS CODE:\n{current_code}\n\nERROR:\n{error_log}"}
#         ],
#         "stream": False
#     }

#     try:
#         print(f"🧠 Sending request to Cloudflare Tunnel...")
#         response = requests.post(api_url, json=payload, headers=headers, timeout=180)
        
#         # Check if response is valid JSON
#         response.raise_for_status()
#         return response.json()["message"]["content"]
        
#     except Exception as e:
#         print(f"❌ API Crash: {e}")
#         return ""
    
#     # Backup original file just in case
#     with open(DESIGN_FILE, "r") as f:
#         original_code = f.read()
#     with open(f"{DESIGN_FILE}.backup", "w") as f:
#         f.write(original_code)
        
#     for attempt in range(1, MAX_ITERATIONS + 1):
#         print(f"\n--- Iteration {attempt}/{MAX_ITERATIONS} ---")
        
#         # 1. Run Baseline Verification
#         result = run_verification(DESIGN_FILE, TB_FILE)
        
#         if result.passed:
#             print("✅ SUCCESS: Logic is correct. AI job done.")
#             return True
        
#         print(f"❌ FAILED at stage: {result.stage}")
#         print("Log:", result.message)
        
#         if attempt == MAX_ITERATIONS:
#             print("\n💀 MAX ITERATIONS REACHED. LLM is stuck in a loop. Rolling back.")
#             break
            
#         # 2. Get current faulty code
#         with open(DESIGN_FILE, "r") as f:
#             current_code = f.read()
            
#         # 3. Query LLM
#         # Hum pass kar rahe hain error details (message + stderr/stdout)
#         full_error = f"{result.message}\n{result.stderr}\n{result.stdout}"
#         raw_response = prompt_llm(current_code, full_error)
#         if not raw_response:
#             print("❌ Critical: LLM API unreachable. Aborting optimization.")
#         break
        
#         # 4. Extract and Patch
#         patched_code = extract_verilog(raw_response)
        
#         if not patched_code or "module" not in patched_code:
#             print("⚠ ERROR: LLM hallucinated and returned garbage. Retrying...")
#             continue
            
#         # Overwrite the file with AI's fix
#         with open(DESIGN_FILE, "w") as f:
#             f.write(patched_code)
            
#         print("🔧 Patch applied. Re-verifying in next iteration...")

#     # Rollback logic if it fails completely
#     print("🔄 Restoring original file from backup...")
#     with open(DESIGN_FILE, "w") as f:
#         f.write(original_code)
#     return False

# if __name__ == "__main__":
#     auto_patch_loop()

import re
import requests
from verifier import run_verification

# ═══════════════════════════════════════════════════════════════════════════════
#  ⚙️  ONLY CHANGE THIS WHEN COLAB RESTARTS — paste new tunnel URL here
# ═══════════════════════════════════════════════════════════════════════════════
CLOUDFLARE_URL = "https://genetic-amp-leave-andrea.trycloudflare.com/api/chat"
MODEL_NAME     = "deepseek-coder-v2:16b"
# ═══════════════════════════════════════════════════════════════════════════════

DESIGN_FILE    = "module.v"
TB_FILE        = "tb.v"
MAX_ITERATIONS = 5


def extract_verilog(llm_response: str) -> str:
    """Pull code from ```verilog ... ``` block, or return raw text as fallback."""
    match = re.search(r'```verilog\s*(.*?)\s*```', llm_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return llm_response.strip()


def prompt_llm(current_code: str, task: str) -> str:
    """Send code + task to Ollama via Cloudflare tunnel. Returns model reply or ''."""
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a VLSI expert. Fix or optimize Verilog RTL. "
                    "Output ONLY the complete Verilog inside a single ```verilog ``` block. "
                    "No explanations, no text outside the code block."
                )
            },
            {
                "role": "user",
                "content": f"{task}\n\nCODE:\n{current_code}"
            }
        ],
        "stream": False
    }

    try:
        print("🧠 Sending request to Cloudflare Tunnel...")
        r = requests.post(
            CLOUDFLARE_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300          # 5 min — DeepSeek-16b can be slow on first call
        )

        # ── Diagnose non-200 clearly ──────────────────────────────────────────
        if r.status_code == 404:
            print(f"❌ 404 Not Found — wrong endpoint path in CLOUDFLARE_URL.")
            print(f"   Current URL : {CLOUDFLARE_URL}")
            print(f"   Try changing '/api/chat' to '/v1/chat/completions' if using LiteLLM.")
            return ""
        if r.status_code == 502:
            print("❌ 502 Bad Gateway — tunnel is up but Ollama is not running in Colab.")
            return ""

        r.raise_for_status()
        data = r.json()

        # Ollama format: {"message": {"content": "..."}}
        if "message" in data:
            return data["message"]["content"]
        # OpenAI-compat format: {"choices": [{"message": {"content": "..."}}]}
        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        print(f"⚠️  Unexpected response format. Keys: {list(data.keys())}")
        print(f"   Raw (first 300 chars): {str(data)[:300]}")
        return ""

    except requests.exceptions.ConnectionError:
        print("❌ Connection error — tunnel URL is unreachable.")
        print(f"   URL: {CLOUDFLARE_URL}")
        print("   → Is your Colab cell still running?")
        return ""
    except requests.exceptions.Timeout:
        print("❌ Timed out after 300s — model is too slow or Colab is overloaded.")
        return ""
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return ""


def auto_patch_loop():
    """Ask LLM to fix module.v repeatedly until it passes the testbench."""

    with open(DESIGN_FILE, "r") as f:
        original_code = f.read()
    with open(f"{DESIGN_FILE}.backup", "w") as f:
        f.write(original_code)
    print(f"💾 Backup saved → {DESIGN_FILE}.backup\n")

    for attempt in range(1, MAX_ITERATIONS + 1):
        print(f"--- Iteration {attempt}/{MAX_ITERATIONS} ---")

        result = run_verification(DESIGN_FILE, TB_FILE)

        if result.passed:
            print("✅ SUCCESS: All tests pass.")
            return True

        print(f"❌ FAILED [{result.stage}]: {result.message}")

        if attempt == MAX_ITERATIONS:
            print("\n💀 MAX ITERATIONS REACHED. Rolling back.")
            break

        with open(DESIGN_FILE, "r") as f:
            current_code = f.read()

        # Build error context
        error_ctx = f"Stage: {result.stage}\nReason: {result.message}"
        if result.stdout.strip():
            error_ctx += f"\nSimulator output:\n{result.stdout.strip()}"
        if result.stderr.strip():
            error_ctx += f"\nCompiler errors:\n{result.stderr.strip()}"

        task = f"The Verilog module FAILS its testbench. Fix ALL bugs.\n\nERROR DETAILS:\n{error_ctx}"

        raw = prompt_llm(current_code, task)
        if not raw:
            print("❌ No response from LLM. Aborting.")
            break

        fixed = extract_verilog(raw)
        if not fixed or "module" not in fixed:
            print("⚠️  LLM returned unusable output. Retrying...")
            continue

        with open(DESIGN_FILE, "w") as f:
            f.write(fixed)
        print("🔧 Patch applied. Re-verifying...\n")

    print("🔄 Restoring original from backup...")
    with open(DESIGN_FILE, "w") as f:
        f.write(original_code)
    return False


if __name__ == "__main__":
    auto_patch_loop()