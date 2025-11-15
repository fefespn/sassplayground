from pathlib import Path
from typing import Union
from .utils import run_command, ensure_dir

class Assembler:
    """Handles reassembly of modified SASS back to CUBIN"""
    
    def assemble(self, cuasm_file: Union[str, Path], output_dir: Union[str, Path]) -> Path:
        """
        Assemble a CuASM file back to CUBIN using CuAssembler
        
        Args:
            cuasm_file: Path to input CuASM file
            output_dir: Directory to store output CUBIN file
        
        Returns:
            Path to the generated CUBIN file
        """
        cuasm_path = Path(cuasm_file)
        output_dir = ensure_dir(output_dir)
        cubin_file = output_dir / f"{cuasm_path.stem}_new.cubin"
        
        if not cuasm_path.exists():
            raise FileNotFoundError(f"Could not find {cuasm_path}. Please run disassemble first.")
            
        # Use CuAssembler to convert CuASM back to CUBIN
        run_command([
            'cuasm',
            '--asm2bin',
            str(cuasm_path),
            '-o', str(cubin_file)
        ])
        
        return cubin_file

    def validate_sass(self, sass_file: Union[str, Path]) -> bool:
        """Validate SASS syntax before assembly"""
        # This would implement SASS validation
        raise NotImplementedError("SASS validation not yet implemented")