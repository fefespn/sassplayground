# SASS Playground

A comprehensive tool for exploring and optimizing CUDA kernels at the SASS assembly level. This tool enables developers to:

- **Compile** CUDA/Triton kernels to PTX and CUBIN
- **Disassemble** CUBIN files to human-readable SASS and CuASM format
- **Edit** SASS/CuASM manually to experiment with assembly-level optimizations
- **Reassemble** modified CuASM back to runnable CUBIN files
- **Run and benchmark** modified kernels with correctness verification
- **Compare** original vs. modified kernels (performance, correctness)
- **Visualize** first 10 I/O samples to inspect kernel behavior

Both CLI and web UI (Gradio) interfaces are provided for maximum flexibility.

## Demo Video

Watch a quick demo of the SASS Playground workflow:

<video src="https://github.com/fefespn/sassplayground/raw/main/Recording-cuda-cubin-cuasm-cubin-run.mp4" controls="controls" style="max-width: 730px;">
</video>

## Requirements

- **CUDA Toolkit** 11.0+
- **Python** 3.8+
- **NVIDIA GPU** with compute capability 8.0+ (for default compilation settings, adjust as needed)
- **nvcc** (NVIDIA CUDA compiler)
- **nvdisasm** (NVIDIA disassembler)
- **CuAssembler** (for SASS reassembly) — see installation below

## Installation

### 1. Clone and Setup Python Environment

```bash
cd sassplayground
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install CuAssembler

SASS Playground uses [CuAssembler](https://github.com/cloudcores/CuAssembler) to convert between SASS assembly and CUBIN binaries. Install it as follows:

```bash
# Clone CuAssembler repository
git clone https://github.com/cloudcores/CuAssembler.git
cd CuAssembler

# Install dependencies
pip install -r requirements.txt

# Add to PATH (so `cuasm` command is available globally)
# Option A: On Linux/macOS:
export PATH="$PATH:$(pwd)/bin"

# Option B: On Windows (in PowerShell):
$env:PATH += ";$(Get-Location)\bin"

# Or permanently add the CuAssembler bin directory to your system PATH
```

Verify CuAssembler is installed:

```bash
cuasm --version
# or
python <path-to-CuAssembler>/bin/cuasm --help
```

### 3. Verify CUDA Tools

Make sure CUDA tools are available:

```bash
nvcc --version
nvdisasm --help
```

## Usage

### Option A: Web UI (Gradio) — Recommended for Exploration

Launch the interactive web interface:

```bash
source venv/bin/activate
python gradio_app.py
```

Open http://localhost:7860 in your browser. The UI provides a complete workflow:

1. **Upload Kernel** — Upload a `.cu` or `.py` CUDA/Triton kernel file
2. **View Source** — See your uploaded kernel code in the Source viewer
3. **Compile** — Compile to PTX/CUBIN; view PTX output side-by-side
4. **Disassemble** — Extract SASS (for viewing) and CuASM (for editing)
5. **Edit CuASM** — Manually modify assembly in the browser editor
6. **Assemble** — Convert edited CuASM back to executable CUBIN
7. **Run & Compare** — Execute kernel, benchmark, verify correctness, and inspect I/O samples

### Option B: Command-Line Interface (CLI)

#### Compile a CUDA kernel to PTX/CUBIN:

```bash
python main.py compile examples/add_kernel.cu
```

Output: PTX and CUBIN files in `build/` directory.

#### Disassemble a CUBIN to CuASM:

```bash
python main.py disasm build/add_kernel.cubin
```

Output:
- `build/add_kernel.sass` — Human-readable SASS (for reference)
- `build/add_kernel.cuasm` — CuAssembler format (for editing)
- `build/add_kernel.original.cubin` — Backup of original

#### Edit and Assemble:

```bash
# Edit the CUASM file in your editor:
# build/add_kernel.cuasm

# Then reassemble:
python main.py assemble build/add_kernel.sass
```

Output: `build/add_kernel_new.cubin` — New executable CUBIN

#### Run and Benchmark a Kernel:

```bash
python main.py run build/add_kernel.cubin --args '{"n": 1024}'
```

Output: Execution results including timing, correctness, and **first 10 I/O samples** showing input, output, expected, and error.

#### Compare Original vs. Modified Kernel:

```bash
python main.py run build/add_kernel_new.cubin \
  --compare-with build/add_kernel.original.cubin \
  --args '{"n": 1024}'
```

## Project Structure

```
sassplayground/
├── src/
│   ├── __init__.py              # Package init
│   ├── compiler.py              # CUDA/Triton → PTX/CUBIN compilation
│   ├── disassembler.py          # CUBIN → SASS + CuASM disassembly
│   ├── assembler.py             # CuASM → CUBIN reassembly (via CuAssembler)
│   ├── runner.py                # Kernel execution, benchmarking, I/O sampling
│   ├── ui.py                    # Gradio web interface
│   └── utils.py                 # Common utilities
├── examples/
│   └── add_kernel.cu            # Example CUDA kernel (vector addition)
├── main.py                      # CLI entry point
├── gradio_app.py                # Gradio UI launcher
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Key Features

### I/O Sample Inspection

Every kernel run includes the **first 10 I/O samples** with:
- Index, input values (a, b)
- Actual output (out)
- Expected value
- Absolute error

Example output:
```json
{
  "samples": [
    {
      "idx": 0,
      "a": 0.42,
      "b": 0.58,
      "out": 1.00,
      "expected": 1.00,
      "error": 0.0
    },
    // ... more samples ...
  ]
}
```

This allows quick visual inspection to spot systematic failures.

### Performance Comparison

- Timing statistics (mean, std, min, max)
- Speedup calculation (original vs. modified)
- Correctness verification
- Side-by-side comparison in CLI and UI

### SASS Editing Workflow

1. Disassemble original CUBIN to CuASM
2. Edit assembly in text editor or Gradio UI
3. Reassemble to new CUBIN using CuAssembler
4. Run and compare with original
5. Iterate on further optimizations

## Examples

### Example 1: Basic Workflow (CLI)

```bash
# Compile
python main.py compile examples/add_kernel.cu

# Disassemble
python main.py disasm build/add_kernel.cubin

# (Edit build/add_kernel.cuasm in your editor)

# Reassemble
python main.py assemble build/add_kernel.sass

# Run and compare
python main.py run build/add_kernel_new.cubin \
  --compare-with build/add_kernel.original.cubin \
  --args '{"n": 1024}'
```

### Example 2: Using the Gradio UI

1. Open http://localhost:7860
2. Upload `examples/add_kernel.cu`
3. Click **Compile**
4. View your source code, PTX, and CUBIN path
5. Click **Disassemble CUBIN**
6. Review human-readable SASS and edit the CuASM
7. Click **Assemble edited CuASM**
8. Click **Run & Compare** to see timings, correctness, and I/O samples

## Troubleshooting

### CuAssembler Not Found

If you see `cuasm: command not found`, ensure:
1. CuAssembler is cloned and installed
2. The `bin/` directory is in your system PATH
3. Try running: `python /path/to/CuAssembler/bin/cuasm --version`

### "Named Symbol Not Found" Error

This means the kernel entry point couldn't be found in the CUBIN. Common causes:
- Kernel was compiled without `extern "C"` (for C++ kernels)
- CUBIN doesn't match what you expect (check file timestamps)
- GPU architecture mismatch

Try specifying kernel name explicitly:
```bash
python main.py run build/add_kernel.cubin --args '{"n": 1024, "kernel": "my_kernel_name"}'
```

### CUBIN Load Errors

Ensure:
- CUBIN file is valid: `file build/add_kernel.cubin`
- GPU driver is up-to-date
- CUDA toolkit version matches GPU driver

### Assembly Syntax Errors

When reassembling, CuAssembler will report syntax errors. Common issues:
- Invalid instruction format
- Incorrect operand types
- Encoding mismatches

Check the error message and edit the CuASM file accordingly.

## GPU Architecture Settings

By default, SASS Playground targets **SM 8.6** (Ampere RTX 30-series mobile / Ada RTX 40-series). Adjust for your GPU:

Common compute capabilities:
- `sm_75` — Turing (RTX 20-series)
- `sm_80` — Ampere (RTX 30-series, A100)
- `sm_86` — Ampere mobile (RTX 30-series mobile)
- `sm_89` — Ada Lovelace (RTX 40-series)

To change, edit:
- `src/compiler.py` — Change `-arch=sm_86` lines
- `src/disassembler.py` — Change `--gpu-arch=sm_86` line
- `src/assembler.py` — Change `--gpu-arch=sm_86` line

## Future Enhancements

- [ ] SASS version history and undo/redo in UI
- [ ] Automatic instruction scheduling suggestions
- [ ] Register pressure analysis
- [ ] Full Triton kernel compilation support
- [ ] Integration with profiling tools (NSys, NSight Compute)
- [ ] Multi-kernel analysis and comparison
- [ ] SASS syntax highlighting in editor
- [ ] Export/import optimization profiles

## License

[Add your license here, e.g., MIT, Apache 2.0]

## References

- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
- [CuAssembler (GitHub)](https://github.com/cloudcores/CuAssembler)
- [Gradio Documentation](https://www.gradio.app/docs)
- [PyCUDA](https://documen.tician.de/pycuda/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review server logs (if running Gradio, check terminal output)
3. Verify CUDA tools are installed: `nvcc --version && nvdisasm --help && cuasm --version`
4. Open a GitHub issue with setup details and error messages