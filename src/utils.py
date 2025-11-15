import os
import json
import subprocess
from pathlib import Path
from typing import Union, List, Dict, Any, Tuple

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, create if it doesn't"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def run_command(cmd: List[str], cwd: Union[str, Path] = None) -> Tuple[str, str]:
    """Run a shell command and return stdout and stderr"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed with exit code {e.returncode}:\n{e.stderr}")

def check_cuda_installation() -> bool:
    """Check if CUDA toolkit is installed and accessible"""
    try:
        run_command(['nvcc', '--version'])
        return True
    except (RuntimeError, FileNotFoundError):
        return False

def parse_kernel_args(args_str: str) -> Dict[str, Any]:
    """Parse kernel arguments from JSON string"""
    if not args_str:
        return {}
    try:
        return json.loads(args_str)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON string for kernel arguments")