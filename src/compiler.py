from pathlib import Path
from typing import Tuple, Union
import triton
import torch
from .utils import run_command, ensure_dir

class Compiler:
    """Handles compilation of CUDA/Triton kernels to PTX and CUBIN"""
    
    def compile(self, input_file: Union[str, Path], output_dir: Union[str, Path]) -> Tuple[Path, Path]:
        """
        Compile a CUDA or Triton kernel to PTX and CUBIN
        
        Args:
            input_file: Path to input .cu or .py file
            output_dir: Directory to store output files
        
        Returns:
            Tuple of (ptx_file, cubin_file) paths
        """
        input_path = Path(input_file)
        output_dir = ensure_dir(output_dir)
        print("firass")
        print(input_path)
        
        if input_path.suffix == '.cu':
            return self._compile_cuda(input_path, output_dir)
        elif input_path.suffix == '.py':
            return self._compile_triton(input_path, output_dir)
        else:
            raise ValueError(f"Unsupported file type: {input_path.suffix}")

    def _compile_cuda(self, cuda_file: Path, output_dir: Path) -> Tuple[Path, Path]:
        """Compile CUDA source to PTX and CUBIN using nvcc"""
        stem = cuda_file.stem
        ptx_file = output_dir / f"{stem}.ptx"
        cubin_file = output_dir / f"{stem}.cubin"
        
        # Compile to PTX
        run_command([
            'nvcc',
            '-ptx',
            str(cuda_file),
            '-o', str(ptx_file),
            #'-arch=sm_80',  # Adjust based on target architecture
            '-arch=sm_86',
            '-O3'
        ])
        
        # Compile to CUBIN
        run_command([
            'nvcc',
            '-cubin',
            str(cuda_file),
            '-o', str(cubin_file),
            '-arch=sm_86',
            '-O3'
        ])
        
        return ptx_file, cubin_file

    def _compile_triton(self, triton_file: Path, output_dir: Path) -> Tuple[Path, Path]:
        """Compile Triton kernel to PTX and CUBIN"""
        # This is a placeholder - actual Triton compilation would need to:
        # 1. Load the Triton kernel from the Python file
        # 2. Use triton.compile() to get PTX
        # 3. Convert PTX to CUBIN using nvcc
        # This would require more complex implementation
        raise NotImplementedError("Triton compilation not yet implemented")