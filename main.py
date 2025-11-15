#!/usr/bin/env python3
import click
from rich.console import Console
from rich.traceback import install
from pathlib import Path
from src.compiler import Compiler
from src.disassembler import Disassembler
from src.assembler import Assembler
from src.runner import KernelRunner
from src.utils import ensure_dir

# Install rich traceback handler
install()
console = Console()

@click.group()
def cli():
    """SASS Playground - CUDA/Triton kernel compilation and SASS manipulation tool"""
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='build', help='Output directory for compiled files')
def compile(input_file, output_dir):
    """Compile a CUDA/Triton kernel to PTX and CUBIN"""
    try:
        ensure_dir(output_dir)
        compiler = Compiler()
        ptx_file, cubin_file = compiler.compile(input_file, output_dir)
        console.print(f"[green]Successfully compiled:[/green]")
        console.print(f"PTX: {ptx_file}")
        console.print(f"CUBIN: {cubin_file}")
    except Exception as e:
        console.print(f"[red]Error during compilation:[/red] {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('cubin_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='build', help='Output directory for SASS file')
def disasm(cubin_file, output_dir):
    """Disassemble a CUBIN file to SASS"""
    try:
        ensure_dir(output_dir)
        disassembler = Disassembler()
        sass_file = disassembler.disassemble(cubin_file, output_dir)
        console.print(f"[green]Successfully disassembled to SASS:[/green] {sass_file}")
    except Exception as e:
        console.print(f"[red]Error during disassembly:[/red] {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('sass_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='build', help='Output directory for new CUBIN')
def assemble(sass_file, output_dir):
    """Assemble a SASS file back to CUBIN"""
    try:
        ensure_dir(output_dir)
        assembler = Assembler()
        cubin_file = assembler.assemble(sass_file, output_dir)
        console.print(f"[green]Successfully assembled to CUBIN:[/green] {cubin_file}")
    except Exception as e:
        console.print(f"[red]Error during assembly:[/red] {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('cubin_file', type=click.Path(exists=True))
@click.option('--args', help='Kernel arguments as JSON string')
@click.option('--compare-with', type=click.Path(exists=True), help='Original CUBIN to compare against')
def run(cubin_file, args, compare_with):
    """Run and benchmark a CUBIN kernel"""
    try:
        runner = KernelRunner()
        results = runner.run(cubin_file, args, compare_with)
        console.print("[green]Kernel execution results:[/green]")
        console.print(results)
    except Exception as e:
        console.print(f"[red]Error during kernel execution:[/red] {str(e)}")
        raise click.Abort()

if __name__ == '__main__':
    cli()