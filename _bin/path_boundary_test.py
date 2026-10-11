#!/usr/bin/env python3
"""Regression tests for vault and Context Pack path boundaries."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brainlib as B


def check(name, condition, detail=""):
    if not condition:
        FAIL.append(name)
        print("  ✗ %s%s" % (name, ("\n      → " + detail) if detail else ""))
        return
    OK.append(name)
    print("  ✓ %s" % name)


def scout(vault, path):
    env = os.environ.copy()
    env.update({"BRAIN_VAULT": vault, "BRAIN_STATE": os.path.join(vault, "state")})
    payload = {"tool_input": {"file_path": path}}
    return subprocess.run(
        [sys.executable, os.path.join(HERE, "gate_scout.py")],
        input=json.dumps(payload).encode(), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=env,
    )


def main():
    with tempfile.TemporaryDirectory() as root:
        vault = os.path.join(root, "vault")
        os.mkdir(vault)
        sibling = vault + "-evil"
        os.mkdir(sibling)

        old_vault = B.VAULT
        B.VAULT = vault
        try:
            check("the vault itself is inside", B.in_vault(vault))
            check("a real child is inside", B.in_vault(os.path.join(vault, "note.md")))
            check("a sibling with the vault prefix is outside", not B.in_vault(
                os.path.join(sibling, "note.md")))
        finally:
            B.VAULT = old_vault

        valid = os.path.join(vault, "60-Context-Packs", "pack.md")
        os.mkdir(os.path.dirname(valid))
        evil = os.path.join(vault, "60-Context-Packs-evil", "pack.md")
        os.mkdir(os.path.dirname(evil))
        check("context scout allows a real Context Pack", scout(vault, valid).stdout == b"")
        denied = scout(vault, evil)
        check("context scout denies a prefixed sibling", b"permissionDecision" in denied.stdout,
              denied.stdout.decode("utf-8", "replace"))
    print("\nRESULT: %d passed, %d failed" % (len(OK), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    OK, FAIL = [], []
    raise SystemExit(main())
