"""
verifier.py — Baseline Verilog Verification Engine
Phase 1 Core: Compile + Simulate using Icarus Verilog (iverilog + vvp)
"""

import subprocess
import os
import tempfile
import shutil
import logging
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Structured result
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    passed: bool
    stage: str                        # "FILE_CHECK" | "COMPILE" | "SIMULATE" | "PARSE"
    message: str
    stdout: str = ""
    stderr: str = ""
    warnings: list[str] = field(default_factory=list)

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        lines = [f"{status} [{self.stage}] {self.message}"]
        if self.warnings:
            lines.append("  Warnings:")
            for w in self.warnings:
                lines.append(f"    ⚠  {w}")
        if not self.passed and self.stderr:
            lines.append("  STDERR:")
            lines.append(self.stderr.strip())
        if not self.passed and self.stdout:
            lines.append("  STDOUT:")
            lines.append(self.stdout.strip())
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Heuristic fallback
# ---------------------------------------------------------------------------

_FAIL_KEYWORDS = ["ERROR", "FAILED", "MISMATCH", "ASSERTION", "X detected"]

def _parse_simulation_output(stdout: str, stderr: str) -> tuple[bool, str, list[str]]:
    warnings = []
    if stderr.strip():
        warnings = [line for line in stderr.splitlines() if line.strip()]

    if "[VERIFICATION_SUCCESS]" in stdout:
        return True, "Explicit success tag found.", warnings

    if "[VERIFICATION_FAILED]" in stdout:
        return False, "Explicit failure tag found.", warnings

    for kw in _FAIL_KEYWORDS:
        if kw.lower() in stdout.lower():
            return False, f"Heuristic fail: keyword '{kw}' detected in output.", warnings

    return (
        False,
        "No [VERIFICATION_SUCCESS] tag found. Add '$display(\"[VERIFICATION_SUCCESS]\"); $finish;' "
        "to your testbench for reliable detection.",
        warnings
    )


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def run_verification(
    design_file: str,
    tb_file: str,
    timeout_sec: int = 10,
    work_dir: Optional[str] = None,
) -> VerificationResult:
    for path, label in [(design_file, "Design"), (tb_file, "Testbench")]:
        if not os.path.exists(path):
            return VerificationResult(
                passed=False, stage="FILE_CHECK",
                message=f"{label} file not found: '{path}'"
            )

    tmp_owned = work_dir is None
    tmp_dir   = work_dir or tempfile.mkdtemp(prefix="verilog_verify_")
    vvp_path  = os.path.join(tmp_dir, "sim.vvp")

    try:
        compile_cmd = ["iverilog", "-o", vvp_path, "-Wall", design_file, tb_file]
        try:
            comp = subprocess.run(compile_cmd, capture_output=True, text=True, check=True)
            comp_warnings = [l for l in comp.stderr.splitlines() if l.strip()]
        except subprocess.CalledProcessError as e:
            return VerificationResult(
                passed=False, stage="COMPILE",
                message="Compilation failed. Fix syntax errors before optimization.",
                stdout=e.stdout,
                stderr=e.stderr,
            )
        except FileNotFoundError:
            return VerificationResult(
                passed=False, stage="COMPILE",
                message="'iverilog' not found. Is Icarus Verilog installed and on PATH?",
            )

        sim_cmd = ["vvp", vvp_path]
        try:
            sim = subprocess.run(sim_cmd, capture_output=True, text=True, timeout=timeout_sec)
            stdout, stderr = sim.stdout, sim.stderr

            if sim.returncode not in (0, 1):
                return VerificationResult(
                    passed=False, stage="SIMULATE",
                    message=f"Simulator crashed (exit code {sim.returncode}).",
                    stdout=stdout, stderr=stderr, warnings=comp_warnings,
                )
        except subprocess.TimeoutExpired:
            return VerificationResult(
                passed=False, stage="SIMULATE",
                message=(
                    f"Simulation timed out after {timeout_sec}s. "
                    "Likely cause: combinational loop or missing $finish in testbench."
                ),
                warnings=comp_warnings,
            )
        except FileNotFoundError:
            return VerificationResult(
                passed=False, stage="SIMULATE",
                message="'vvp' not found. Is Icarus Verilog installed correctly?",
            )

        passed, reason, sim_warnings = _parse_simulation_output(stdout, stderr)
        all_warnings = comp_warnings + sim_warnings

        return VerificationResult(
            passed=passed, stage="PARSE",
            message=reason,
            stdout=stdout, stderr=stderr, warnings=all_warnings,
        )

    finally:
        if tmp_owned and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) not in (3, 4):
        print("Usage: python verifier.py <module.v> <tb.v> [timeout_sec]")
        sys.exit(1)

    design  = sys.argv[1]
    tb      = sys.argv[2]
    timeout = int(sys.argv[3]) if len(sys.argv) == 4 else 10

    print(f"Verifying: {design} + {tb}  (timeout={timeout}s)")
    print("-" * 50)

    result = run_verification(design, tb, timeout_sec=timeout)
    print(result)

    sys.exit(0 if result.passed else 1)
