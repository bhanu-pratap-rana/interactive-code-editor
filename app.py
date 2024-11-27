import streamlit as st
from streamlit_ace import st_ace
import subprocess
import tempfile
import sys
import os
import shutil

NODE_PATH = r"C:\Program Files\nodejs"
NPM_PATH = os.path.join(NODE_PATH, "npm.cmd")
NODE_EXE = os.path.join(NODE_PATH, "node.exe")
NPX_PATH = os.path.join(NODE_PATH, "npx.cmd")

if 'workspace_dir' not in st.session_state:
    st.session_state.workspace_dir = tempfile.mkdtemp()
    subprocess.run([NPM_PATH, "init", "-y"], cwd=st.session_state.workspace_dir)

def install_dependency(dependency_type, package_name):
    try:
        if dependency_type == "npm":
            subprocess.run([NPM_PATH, "install", package_name], 
                         cwd=st.session_state.workspace_dir, check=True)
            return f"Successfully installed {package_name} via npm"
        elif dependency_type == "pip":
            subprocess.run([sys.executable, "-m", "pip", "install", 
                          "--target", st.session_state.workspace_dir, package_name], 
                         check=True)
            return f"Successfully installed {package_name} via pip"
    except subprocess.CalledProcessError as e:
        return f"Failed to install {package_name}: {str(e)}"

st.set_page_config(page_title="Playwright Test Editor", layout="wide")

st.markdown("""
    <style>
        .streamlit-expanderContent {
            max-height: 400px;
            overflow-y: auto;
        }
        .ace_editor {
            border-radius: 4px;
            border: 1px solid #ccc;
        }
        .ace_gutter {
            background-color: #f5f5f5;
        }
        .stTextInput > div > div > input {
            font-family: monospace;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Playwright Test Editor")

LANGUAGE_CONFIGS = {
    "python": {"extension": ".py"},
    "javascript": {"extension": ".spec.js"}
}

with st.sidebar:
    language = st.selectbox(
        "Programming Language",
        list(LANGUAGE_CONFIGS.keys())
    )

    theme = st.selectbox(
        "Editor Theme",
        ["monokai", "github", "tomorrow", "twilight", "solarized_dark"]
    )

    font_size = st.slider("Font Size", 14, 24, 16)
    editor_height = st.slider("Editor Height", 400, 800, 500)

    with st.expander("Dependency Manager"):
        dep_type = st.selectbox("Dependency Type", ["npm", "pip"])
        package_name = st.text_input(
            f"Enter {'npm' if dep_type == 'npm' else 'pip'} package name",
            placeholder="e.g., @playwright/test for npm or playwright for pip"
        )
        if st.button("Install Dependency"):
            result = install_dependency(dep_type, package_name)
            st.write(result)

        if st.button("Install Playwright"):
            if dep_type == "npm":
                result = install_dependency("npm", "@playwright/test")
            else:
                result = install_dependency("pip", "playwright")
            st.write(result)

        if st.button("Install Playwright Browsers"):
            result = subprocess.run([NPX_PATH, "playwright", "install"], 
                                 cwd=st.session_state.workspace_dir,
                                 capture_output=True,
                                 text=True)
            st.write("Browsers installed successfully!" if result.returncode == 0 else f"Error: {result.stderr}")

if 'previous_code' not in st.session_state:
    st.session_state.previous_code = ""

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
    auto_update=True,
    tab_size=4,
    show_print_margin=True
)

def execute_code(code, language):
    if not code.strip():
        return "No code to execute!"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        if language == "javascript":
            tests_dir = os.path.join(tmpdir, "tests")
            os.makedirs(tests_dir)
            
            config_source = os.path.join(os.getcwd(), "playwright.config.js")
            config_dest = os.path.join(tmpdir, "playwright.config.js")
            shutil.copy2(config_source, config_dest)
            
            subprocess.run([NPM_PATH, "init", "-y"], cwd=tmpdir)
            subprocess.run([NPM_PATH, "install", "@playwright/test"], cwd=tmpdir)
            
            test_path = os.path.join(tests_dir, "test.spec.js")
            with open(test_path, 'w') as f:
                f.write(code)
            
            try:
                result = subprocess.run(
                    [NPX_PATH, "playwright", "test", "--headed"],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir,
                    env=os.environ.copy()
                )
                return result.stdout if result.returncode == 0 else f"Error:\n{result.stderr}"
            except Exception as e:
                return f"Execution Error: {str(e)}"
        else:
            file_path = os.path.join(tmpdir, f"script{LANGUAGE_CONFIGS[language]['extension']}")
            with open(file_path, 'w') as f:
                f.write(code)
            
            try:
                env = os.environ.copy()
                env["PYTHONPATH"] = f"{st.session_state.workspace_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
                result = subprocess.run(
                    [sys.executable, file_path],
                    capture_output=True,
                    text=True,
                    env=env
                )
                return result.stdout if result.returncode == 0 else f"Error:\n{result.stderr}"
            except Exception as e:
                return f"Execution Error: {str(e)}"

if st.button("Run Code", type="primary"):
    with st.spinner("Executing..."):
        execution_output = execute_code(code, language)
        st.write("## Output:")
        st.code(execution_output)
        st.session_state.previous_code = code

def cleanup():
    if hasattr(st.session_state, 'workspace_dir'):
        shutil.rmtree(st.session_state.workspace_dir, ignore_errors=True)

st.session_state['cleanup'] = cleanup

if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("Cache cleared successfully!")
