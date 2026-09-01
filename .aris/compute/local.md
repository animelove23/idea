# Local Compute Ledger

### env: vista@7d630cb6

- how: existing conda environment `/workspace/miniconda3/envs/vista`
- spec: `.aris/compute/local-vista-env-spec.json`
- tier: `{cpus: host, mem_gib: host, gpus: 1, gpu: "NVIDIA GeForce RTX 4090 24GB"}`
- weights: `/workspace/download_models/llava-v1.5-7b`
- validated: 2026-08-30 (imports + seeded CUDA matmul witness)
- witness: `WITNESS (8, 8) NVIDIA GeForce RTX 4090 2.0169806480407715`
- documented invocation: `/workspace/miniconda3/envs/vista/bin/python -c 'import torch; torch.manual_seed(0); x=torch.randn(8,8,device="cuda"); y=x@x; print("WITNESS", tuple(y.shape), torch.cuda.get_device_name(0), float(y[0,0]))'`
- gotcha: torchvision emits an undefined-symbol warning in the exported environment; current VISTA image loading path still runs, but torchvision I/O extension should not be treated as validated.
