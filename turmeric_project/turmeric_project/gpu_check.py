"""
Check whether Keras can actually train on the NVIDIA GPU using PyTorch backend.

Run:
    python gpu_check.py
"""

import subprocess
import sys


def print_nvidia_smi():
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception as exc:
        print(f"nvidia-smi: not available ({exc})")
        return

    print("nvidia-smi:")
    print(result.stdout.strip() or result.stderr.strip())


def main():
    print_nvidia_smi()
    print("\nPyTorch (Keras Backend):")

    try:
        import torch
    except Exception as exc:
        print(f"  PyTorch import failed: {exc}")
        sys.exit(1)

    print(f"  version: {torch.__version__}")
    print(f"  built with CUDA: {torch.backends.cudnn.is_available()}")

    gpus = torch.cuda.device_count()
    if not torch.cuda.is_available() or gpus == 0:
        print("  GPUs visible to PyTorch: 0")
        print("\nResult: PyTorch is running CPU-only in this environment.")
        sys.exit(1)

    print(f"  GPUs visible to PyTorch: {gpus}")
    for i in range(gpus):
        print(f"    - {torch.cuda.get_device_name(i)}")

    a = torch.randn(2048, 2048, device="cuda")
    b = torch.randn(2048, 2048, device="cuda")
    c = torch.matmul(a, b)
    _ = c.cpu().numpy()

    print("\nResult: GPU PyTorch is working. Keras will use it!")


if __name__ == "__main__":
    main()
