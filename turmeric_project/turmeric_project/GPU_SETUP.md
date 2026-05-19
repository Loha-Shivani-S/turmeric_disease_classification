# GPU Setup

This project is configured for the Keras Torch backend on native Windows.
That matches this machine because `gpu_check.py` shows:

```text
PyTorch CUDA: working
GPU: NVIDIA GeForce RTX 3050 Laptop GPU
```

Check the environment:

```powershell
py gpu_check.py
```

Train:

```powershell
py train.py
```

At startup, training should print:

```text
Keras backend: torch
Accelerator: 1 CUDA GPU(s) detected by PyTorch
```

By default, `config.py` has:

```python
REQUIRE_GPU = True
```

That means `train.py` stops if PyTorch/Keras cannot see a CUDA GPU. Set it to
`False` only if you intentionally want CPU training.

Native Windows note: TensorFlow GPU is not available for normal TensorFlow
2.11+ installs on native Windows. This project therefore uses PyTorch CUDA
through Keras instead.
