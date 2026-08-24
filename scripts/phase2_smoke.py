import os
import subprocess
import sys


def main() -> int:
    secret = os.environ.get("ACUITYNET_JWT_SECRET")
    if not secret:
        print("ACUITYNET_JWT_SECRET is required for Phase 2 smoke verification", file=sys.stderr)
        return 2
    child_env = os.environ.copy()
    child_env["ACUITYNET_JWT_SECRET"] = secret
    print("Phase 2 smoke preflight passed; secret value is not displayed.")
    # The integration test owns the temporary database and HTTP assertions.
    result = subprocess.run([sys.executable, "-m", "pytest", "backend/tests/test_phase2_integration.py", "-q"], env=child_env)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())