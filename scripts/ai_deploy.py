import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass


@dataclass
class DeployDecision:
    strategy: str
    reason: str


def choose_strategy(changed_files: int, force_rebuild: bool) -> DeployDecision:
    if force_rebuild:
        return DeployDecision("full_rebuild", "forced by argument")
    if changed_files > 10:
        return DeployDecision("full_rebuild", "many files changed")
    return DeployDecision("quick_restart", "small diff, faster release")


def run(cmd: str) -> None:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"command failed: {cmd}")
    if result.stdout.strip():
        print(result.stdout.strip())


def health_check(url: str, retries: int = 6) -> bool:
    for _ in range(retries):
        rc = subprocess.call(
            f'curl -fsS "{url}" > /dev/null', shell=True, stdout=subprocess.DEVNULL
        )
        if rc == 0:
            return True
        time.sleep(2)
    return False


def main():
    parser = argparse.ArgumentParser(description="AI-like deployment helper")
    parser.add_argument("--changed-files", type=int, default=1)
    parser.add_argument("--force-rebuild", action="store_true")
    parser.add_argument("--health-url", default="http://127.0.0.1:5000/api/v1/health")
    args = parser.parse_args()

    decision = choose_strategy(args.changed_files, args.force_rebuild)
    print(f"[AI decision] {decision.strategy}: {decision.reason}")

    try:
        if decision.strategy == "full_rebuild":
            run("docker compose up -d --build")
        else:
            run("docker compose restart app")
    except RuntimeError:
        print("Deploy failed while executing docker commands.")
        sys.exit(1)

    if health_check(args.health_url):
        print("Deploy successful and service healthy.")
        return

    print("Health check failed, attempting rollback with full rebuild.")
    run("docker compose down")
    run("docker compose up -d --build")
    if not health_check(args.health_url):
        print("Rollback failed, manual intervention required.")
        sys.exit(1)
    print("Rollback successful.")


if __name__ == "__main__":
    if "REPO_URL" in os.environ:
        # This env is reserved for VPS pull style deploy.
        pass
    main()
