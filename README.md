This project is an **Autonomous RTL Optimization & Patching Engine**. It leverages Large Language Models (LLMs) and open-source hardware tools (Yosys, Icarus Verilog) to automatically fix bugs in Verilog code and optimize Power, Performance, and Area (PPA) by reducing logic cell counts.

---

# 🚀 Autonomous RTL Optimizer & Patcher

This suite of Python tools creates a closed-loop "Self-Healing" hardware design flow. It sends faulty or unoptimized RTL to an AI, verifies the response via simulation, and measures logic area via synthesis.

## 🛠 Features
* **Auto-Patching:** Automatically fixes syntax and logical errors using LLM feedback loops.
* **PPA Optimization:** Reduces the logic cell count (Area) using Yosys synthesis metrics.
* **Closed-Loop Verification:** Every AI-generated patch is strictly verified using Icarus Verilog before being accepted.
* **Embedded Expert Knowledge:** Prompts are tuned for VLSI expertise, enforcing `casez` over `casex` and boolean minimization.

---

## 🏗 System Architecture

The engine follows a strict four-stage cycle:
1.  **Analyze:** Measure current cell count (Yosys) and functional correctness (Icarus).
2.  **Prompt:** Send code and error logs/PPA goals to the DeepSeek-Coder-V2 model.
3.  **Verify:** Run the new code through the `verifier.py` engine.
4.  **Patch:** If tests pass AND area/line count is reduced, the original file is updated.

---

## 📦 Core Components

| File | Responsibility |
| :--- | :--- |
| `auto_patcher.py` | Handles LLM communication and the main iterative loop for fixing bugs. |
| `ppa_optimizer.py` | Focuses on area reduction; uses Yosys to ensure the AI actually makes the design smaller. |
| `verifier.py` | The "Gatekeeper"—runs `iverilog` and `vvp` to ensure functional parity. |
| `check.py` | A lightweight utility to test LLM connectivity via Cloudflare Tunnels. |
| `fix_fences.py` | A utility script to clean Markdown formatting from generated Verilog files. |

---

## 🚀 Getting Started

### 1. Prerequisites
You need the following tools installed and added to your system **PATH**:
* **Python 3.10+**
* **Icarus Verilog:** For simulation (`iverilog`, `vvp`).
* **Yosys:** For synthesis and cell counting.
* **Ollama (optional):** If running the LLM locally.

### 2. Setup Tunnel
If you are using a remote GPU (like Google Colab), ensure your Cloudflare tunnel is active and update the `CLOUDFLARE_URL` in `auto_patcher.py`.

### 3. Usage

#### **To fix a broken design:**
Place your RTL in `module.v` and testbench in `tb.v`, then run:
```bash
python auto_patcher.py
```

#### **To optimize for Area (PPA):**
Once the design is functional, run the optimizer to shrink the logic:
```bash
python ppa_optimizer.py
```

---

## 📊 Optimization Metrics
The `ppa_optimizer.py` script tracks:
* **Logic Cells:** Total primitive gates used after synthesis.
* **Line Count:** Code complexity and readability.
* **Functional Parity:** Ensures that optimization doesn't break the original logic.

> **Note:** The optimizer will reject any AI suggestion that passes simulation but results in a larger cell count than the baseline.

---

## ⚠️ Safety Features
* **Automatic Backups:** Every run creates a `module.v.backup` to prevent permanent code loss.
* **Iteration Limits:** Hard-coded `MAX_ITERATIONS` prevent infinite API credit consumption if the AI gets stuck in a hallucination loop.
* **Timeout Protection:** Simulations are capped at 10 seconds to catch combinational loops.
