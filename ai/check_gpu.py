"""Step 2: check that PyTorch can use your GPU.

    python check_gpu.py

Note for Windows: `pip install torch` from the normal package index gives a
CPU-only build. For an NVIDIA GPU, install the CUDA build instead; pick your
CUDA version on https://pytorch.org/get-started/locally/ and run the command it
shows (it looks like: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu1XX).
"""
import platform
import time

import torch


def main():
    print(f"Python {platform.python_version()} on {platform.system()}, PyTorch {torch.__version__}")
    if not torch.cuda.is_available():
        cuda_build = torch.version.cuda
        print("GPU: NOT available. Everything will run on the CPU (works, but training is much slower).")
        print("  This PyTorch build " + (f"supports CUDA {cuda_build}, so check your NVIDIA driver."
                                         if cuda_build else "is CPU-only. See the note at the top of this file."))
        return False
    name = torch.cuda.get_device_name(0)
    memory = torch.cuda.get_device_properties(0).total_memory / 1e9
    x = torch.randn(2048, 2048, device="cuda")
    torch.cuda.synchronize()
    start = time.time()
    for _ in range(10):
        x = x @ x
        x = x / x.norm()
    torch.cuda.synchronize()
    print(f"GPU: {name}, {memory:.1f} GB memory, CUDA {torch.version.cuda}. "
          f"Test calculation OK ({(time.time() - start) * 1000:.0f} ms).")
    print(f"bfloat16 (used by train_text.py when available): {torch.cuda.is_bf16_supported()}")
    return True


if __name__ == "__main__":
    main()
