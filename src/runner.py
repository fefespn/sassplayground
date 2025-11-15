import numpy as np
import pycuda.driver as cuda
from pathlib import Path
from typing import Union, Dict, Any, Optional, Tuple
import time
import json
import threading
import atexit


def parse_kernel_args(args_str: str) -> Dict[str, Any]:
    import json
    return json.loads(args_str)


class KernelRunner:
    """Handles execution and benchmarking of CUDA kernels from CUBIN files"""
    
    _thread_local = threading.local()
    _contexts_to_cleanup = []
    _cleanup_registered = False
    
    def __init__(self):
        # Register cleanup handler once
        if not KernelRunner._cleanup_registered:
            atexit.register(KernelRunner._cleanup_all_contexts)
            KernelRunner._cleanup_registered = True
    
    @classmethod
    def _cleanup_all_contexts(cls):
        """Clean up all CUDA contexts at exit"""
        for ctx in cls._contexts_to_cleanup:
            try:
                ctx.pop()
            except:
                pass
        cls._contexts_to_cleanup.clear()
    
    def _ensure_cuda_context(self):
        """Initialize CUDA context if not already done in this thread"""
        if not hasattr(self._thread_local, 'context'):
            cuda.init()
            device = cuda.Device(0)
            ctx = device.make_context()
            self._thread_local.context = ctx
            self._contexts_to_cleanup.append(ctx)
        else:
            # Push context if it's not current
            try:
                self._thread_local.context.push()
            except cuda.LogicError:
                pass  # Context already current

    def run(
        self,
        cubin_file: Union[str, Path],
        args_str: Optional[str] = None,
        compare_with: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Load and run a kernel from a CUBIN file"""
        # Ensure CUDA context exists in this thread
        self._ensure_cuda_context()
        
        cubin_path = Path(cubin_file)
        args = parse_kernel_args(args_str or '{"n": 1024}')

        print("Loading CUBIN:", cubin_path)
        module = self._load_cubin(cubin_path)

        kernel_name = self._get_first_kernel_name(module)
        print("Kernel name:", kernel_name)

        kernel = module.get_function(kernel_name)

        # Prepare test data
        n = args.get("n", 1024)
        block_size = 256
        grid_size = (n + block_size - 1) // block_size

        a = np.random.rand(n).astype(np.float32)
        b = np.random.rand(n).astype(np.float32)
        c = np.zeros_like(a)

        a_gpu = cuda.mem_alloc(a.nbytes)
        b_gpu = cuda.mem_alloc(b.nbytes)
        c_gpu = cuda.mem_alloc(c.nbytes)

        cuda.memcpy_htod(a_gpu, a)
        cuda.memcpy_htod(b_gpu, b)

        results = {
            "kernel": cubin_path.name,
            "kernel_name": kernel_name,
            "success": False,
            "error": None,
            "timing": {},
            "correctness": {},
        }

        try:
            # Warmup
            kernel(a_gpu, b_gpu, c_gpu, np.int32(n),
                   block=(block_size, 1, 1), grid=(grid_size, 1))
            cuda.Context.synchronize()

            # Benchmark
            times = []
            for _ in range(100):
                start = time.perf_counter()
                kernel(a_gpu, b_gpu, c_gpu, np.int32(n),
                       block=(block_size, 1, 1), grid=(grid_size, 1))
                cuda.Context.synchronize()
                times.append(time.perf_counter() - start)

            # Retrieve results
            cuda.memcpy_dtoh(c, c_gpu)
            expected = a + b
            max_error = np.max(np.abs(c - expected))

            # Prepare human-inspectable samples (first 10 entries)
            sample_count = min(5, int(n))
            samples = []
            for i in range(sample_count):
                samples.append({
                    'idx': int(i),
                    'a': float(a[i]),
                    'b': float(b[i]),
                    'out': float(c[i]),
                    'expected': float(expected[i]),
                    'error': float(abs(c[i] - expected[i])),
                })

            results.update({
                'success': True,
                'timing': {
                    'mean_ms': np.mean(times) * 1000,
                    'std_ms': np.std(times) * 1000,
                    'min_ms': np.min(times) * 1000,
                    'max_ms': np.max(times) * 1000,
                },
                'correctness': {
                    'max_error': float(max_error),
                    'passed': float(max_error) < 1e-6,
                },
                'samples': samples,
                'test_size': n,
            })

            if compare_with:
                compare_results = self.run(compare_with, args_str)
                results['comparison'] = self._compare_results(results, compare_results)

        except Exception as e:
            results.update({"success": False, "error": str(e)})
        finally:
            a_gpu.free()
            b_gpu.free()
            c_gpu.free()

        return results

    # ---- Helpers ----

    def _load_cubin(self, cubin_path: Path):
        """Load a CUBIN file and return the CUDA module"""
        print("Loading CUBIN file...")

        with open(cubin_path, "rb") as f:
            cubin = f.read()

        try:
            module = cuda.module_from_buffer(cubin)
            print("CUBIN loaded successfully!")
            return module
        except Exception as e:
            print("CUBIN load failed:", e)
            raise

    def _get_first_kernel_name(self, module: cuda.Module) -> str:
        """Return known kernel name (for now static)"""
        return "vector_add"

    def _compare_results(
        self, new_results: Dict[str, Any], old_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not (new_results["success"] and old_results["success"]):
            return {"error": "One or both kernels failed"}

        speedup = old_results["timing"]["mean_ms"] / new_results["timing"]["mean_ms"]
        return {
            "speedup": float(speedup),
            "speedup_percent": float((speedup - 1) * 100),
            "original_ms": float(old_results["timing"]["mean_ms"]),
            "modified_ms": float(new_results["timing"]["mean_ms"]),
            "both_correct": (
                new_results["correctness"]["passed"]
                and old_results["correctness"]["passed"]
            ),
        }