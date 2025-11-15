import json
from pathlib import Path
from typing import Tuple

import gradio as gr

from .compiler import Compiler
from .disassembler import Disassembler
from .assembler import Assembler
from .runner import KernelRunner
from .utils import ensure_dir

BUILD_DIR = Path('build')
ensure_dir(BUILD_DIR)

compiler = Compiler()
disassembler = Disassembler()
assembler = Assembler()
runner = KernelRunner()

# Helpers
def _read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ''

def compile_file(file_obj) -> Tuple[str, str, str, str]:
    """Compile uploaded .cu or .py file and return PTX text and cubin path"""
    if file_obj is None:
        return "", "", "No file provided"
    try:
        # Normalize different possible upload types from Gradio:
        # - a path string (e.g. "/tmp/.../upload")
        # - a Gradio UploadFile-like object with .name (original filename) and .file (file-like)
        src_path = None
        if isinstance(file_obj, str):
            src_path = Path(file_obj)
        elif hasattr(file_obj, 'name') and Path(getattr(file_obj, 'name')).exists():
            # some frameworks put the real path in .name
            src_path = Path(file_obj.name)
        else:
            # Write the uploaded bytes to a stable path under BUILD_DIR using the original filename
            name = getattr(file_obj, 'name', None) or 'uploaded_kernel.cu'
            dest = BUILD_DIR / Path(name).name
            # read bytes from common attributes
            data = None
            if hasattr(file_obj, 'file'):
                try:
                    file_obj.file.seek(0)
                except Exception:
                    pass
                data = file_obj.file.read()
            else:
                try:
                    data = file_obj.read()
                except Exception:
                    data = None
            if data is None:
                raise RuntimeError('Could not read uploaded file content')
            # ensure bytes
            if isinstance(data, str):
                data = data.encode('utf-8')
            dest.write_bytes(data)
            src_path = dest
        print("subhi")
        print(src_path)
        ptx_path, cubin_path = compiler.compile(src_path, BUILD_DIR)
        ptx_text = _read_text(ptx_path)
        # Read source text for display
        source_text = _read_text(src_path)
        return ptx_text, str(cubin_path), str(src_path), "Compiled successfully"
    except Exception as e:
        return "", "", "", f"Compilation error: {e}"


def disasm_cubin(cubin_path_str: str) -> Tuple[str, str, str, str]:
    """Disassemble CUBIN into readable SASS and CuASM format"""
    try:
        cubin_path = Path(cubin_path_str)
        # Now disassemble returns the cuasm_path directly
        cuasm_path = disassembler.disassemble(cubin_path, BUILD_DIR)
        
        # Get human-readable SASS for display only
        sass_path = cuasm_path.parent / f"{cuasm_path.stem}.sass"
        
        # Read both files
        sass_text = _read_text(sass_path)  # For display only
        cuasm_text = _read_text(cuasm_path)  # The actual file we'll edit
        
        return sass_text, cuasm_text, str(cuasm_path), "Disassembled successfully"
    except Exception as e:
        return "", "", "", f"Disassembly error: {e}"


def assemble_from_cuasm(cuasm_path_str: str, cuasm_text: str) -> Tuple[str, str]:
    """Write edited cuasm text to disk and assemble into new CUBIN"""
    try:
        # Now we directly use the cuasm path since that's what matters
        cuasm_path = Path(cuasm_path_str)
        # Write the edited CuASM back
        cuasm_path.write_text(cuasm_text)
        # Assemble the CuASM file (not the sass file)
        cubin = assembler.assemble(cuasm_path, BUILD_DIR)
        return str(cubin), "Assembled successfully"
    except Exception as e:
        return "", f"Assembly error: {e}"


def run_and_compare(original_cubin_path: str, new_cubin_path: str, args_str: str) -> Tuple[str, str]:
    """Run the new cubin and compare to original, return JSON results"""
    try:
        args = args_str or '{}'
        print("firas11")
        #res = runner.run(new_cubin_path, args, compare_with=original_cubin_path)
        res = runner.run(new_cubin_path, args, compare_with=None)

        return json.dumps(res, indent=2), "Run completed"
    except Exception as e:
        return "", f"Run error: {e}"


# Gradio UI
with gr.Blocks(title='SASS Playground') as demo:
    gr.Markdown("# SASS Playground — compile, disasm, edit, assemble, run")
    with gr.Row():
        with gr.Column():
            file_input = gr.File(label='Upload .cu or .py kernel')
            compile_btn = gr.Button('Compile')
            source_out = gr.Textbox(label='Source (.cu/.py)', lines=20)
            ptx_out = gr.Textbox(label='PTX', lines=20)
            cubin_path_out = gr.Textbox(label='CUBIN path')
            #source_out = gr.Textbox(label='Source (.cu/.py)', lines=20)
            disasm_btn = gr.Button('Disassemble CUBIN')
            sass_out = gr.Textbox(label='Readable SASS (.sass)', lines=20)
            cuasm_path_out = gr.Textbox(label='cuasm path')
        with gr.Column():
            gr.Markdown('### Edit CuASM (edit this and click Assemble)')
            cuasm_editor = gr.Textbox(label='CuASM Editor', lines=30)
            assemble_btn = gr.Button('Assemble edited CuASM')
            assembled_cubin_path = gr.Textbox(label='Assembled CUBIN path')
            gr.Markdown('### Run & Compare')
            args_input = gr.Textbox(label='Kernel args (JSON)', value='{"n": 1024}')
            run_btn = gr.Button('Run & Compare')
            run_out = gr.Textbox(label='Run results (JSON)', lines=20)

    # Wire callbacks
    def _compile_click(file_obj):
        ptx, cubin_path, src_path, msg = compile_file(file_obj)
        # try to read source text
        src_text = ''
        try:
            if src_path:
                src_text = Path(src_path).read_text()
        except Exception:
            src_text = ''
        return ptx, cubin_path, src_text

    def _disasm_click(cubin_path):
        sass_text, cuasm_text, cuasm_path, msg = disasm_cubin(cubin_path)
        return sass_text, cuasm_path, cuasm_text

    def _assemble_click(cuasm_path_str, cuasm_text):
        cubin, msg = assemble_from_cuasm(cuasm_path_str, cuasm_text)
        return cubin

    def _run_click(new_cubin, original_cubin, args_str):
        out, msg = run_and_compare(original_cubin, new_cubin, args_str)
        return out

    compile_btn.click(_compile_click, inputs=[file_input], outputs=[ptx_out, cubin_path_out, source_out])
    disasm_btn.click(_disasm_click, inputs=[cubin_path_out], outputs=[sass_out, cuasm_path_out, cuasm_editor])
    assemble_btn.click(_assemble_click, inputs=[cuasm_path_out, cuasm_editor], outputs=[assembled_cubin_path])
    run_btn.click(_run_click, inputs=[assembled_cubin_path, cubin_path_out, args_input], outputs=[run_out])


def launch(port: int = 7860, share: bool = False):
    demo.launch(server_name='0.0.0.0', server_port=port, share=share)


if __name__ == '__main__':
    launch()
