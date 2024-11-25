import streamlit as st
from streamlit_ace import st_ace
import subprocess
import tempfile
import sys
import io
import os
import re

st.set_page_config(page_title="Code Editor", layout="wide")

st.title("Interactive Code Editor")

# Simplified language configurations
LANGUAGE_CONFIGS = {
    "python": {
        "extension": ".py",
        "run_cmd": "python"
    },
    "java": {
        "extension": ".java",
        "compile_cmd": "javac",
        "run_cmd": "java"
    },
    "javascript": {
        "extension": ".js",
        "run_cmd": "node"
    }
}

# Streamlined sidebar
language = st.sidebar.selectbox(
    "Programming Language",
    list(LANGUAGE_CONFIGS.keys())
)

theme = st.sidebar.selectbox(
    "Editor Theme",
    ["monokai", "github", "tomorrow", "twilight", "solarized_dark"]
)

font_size = st.sidebar.slider("Font Size", 14, 24, 16)
editor_height = st.sidebar.slider("Editor Height", 400, 800, 500)

# Initialize session state for code tracking
if 'previous_code' not in st.session_state:
    st.session_state.previous_code = ""

# Code editor with automatic execution
code = st_ace(
    value=st.session_state.previous_code,
    placeholder=f"Write your {language} code here...",
    language=language,
    theme=theme,
    font_size=font_size,
    height=editor_height,
    keybinding="vscode",
    show_gutter=True,
    wrap=True,
    auto_update=True
)

def execute_java(code):
    with tempfile.TemporaryDirectory() as tmpdir:
        class_pattern = r"public\s+class\s+(\w+)"
        match = re.search(class_pattern, code)
        if not match:
            return "Error: Public class not found. Code must contain a public class."
        
        class_name = match.group(1)
        file_path = os.path.join(tmpdir, f"{class_name}.java")
        
        with open(file_path, 'w') as f:
            f.write(code)
        
        try:
            compile_result = subprocess.run(
                ['javac', file_path],
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                return f"Compilation Error:\n{compile_result.stderr}"
            
            run_result = subprocess.run(
                ['java', '-cp', tmpdir, class_name],
                capture_output=True,
                text=True
            )
            return run_result.stdout if run_result.returncode == 0 else f"Runtime Error:\n{run_result.stderr}"
        except Exception as e:
            return f"Execution Error: {str(e)}"

def execute_code(code, language):
    if not code.strip():
        return "No code to execute!"
    
    if language == "java":
        return execute_java(code)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = LANGUAGE_CONFIGS.get(language)
        file_path = os.path.join(tmpdir, f"main{config['extension']}")
        
        with open(file_path, 'w') as f:
            f.write(code)
        
        try:
            run_cmd = f"{config['run_cmd']} {file_path}"
            run_result = subprocess.run(
                run_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            return run_result.stdout if run_result.returncode == 0 else f"Runtime Error:\n{run_result.stderr}"
        except Exception as e:
            return f"Execution Error: {str(e)}"

# Execute code when Run button is clicked
if st.button("Run Code", type="primary"):
    with st.spinner("Executing..."):
        output = execute_code(code, language)
        st.write("## Output:")
        st.code(output)
        st.session_state.previous_code = code
