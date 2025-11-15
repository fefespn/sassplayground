from pathlib import Path
from typing import Union
from .utils import run_command, ensure_dir

class Disassembler:
    """Handles disassembly of CUBIN files to SASS"""
    
    def disassemble(self, cubin_file: Union[str, Path], output_dir: Union[str, Path]) -> Path:
        """
        Disassemble a CUBIN file to CuASM format and generate readable SASS
        
        Args:
            cubin_file: Path to input CUBIN file
            output_dir: Directory to store output files
        
        Returns:
            Path to the generated CuASM file (for reassembly)
        """
        cubin_path = Path(cubin_file)
        output_dir = ensure_dir(output_dir)
        sass_file = output_dir / f"{cubin_path.stem}.sass"
        cuasm_file = output_dir / f"{cubin_path.stem}.cuasm"
        
        # Generate human-readable SASS (for viewing only)
        sass_text, _ = run_command([
            'nvdisasm',
            '-g',  # Show debug info
            '-c',  # Show control flow
            str(cubin_path)
        ])
        sass_file.write_text(sass_text)
        
        # Save the original CUBIN alongside for comparison
        import shutil
        shutil.copy2(cubin_path, output_dir / f"{cubin_path.stem}.original.cubin")
        
        # Generate CuASM format (this is what we'll actually modify and reassemble)
        run_command([
            'cuasm',
            '--bin2asm',
            str(cubin_path),
            '-o', str(cuasm_file)
        ])
        
        return cuasm_file

    def _parse_sass(self, sass_text: str) -> dict:
        """Parse SASS assembly into a structured format for easier manipulation"""
        # This would parse the SASS into a more structured format
        # Could be useful for programmatic SASS manipulation
        raise NotImplementedError("SASS parsing not yet implemented")