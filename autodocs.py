import shutil
import subprocess
import os
from pathlib import Path
from typing import Tuple, List
import datetime

# ----------------------------------------------------------------------- General Settings ----------------------------------------------------------------------- #



# Relative to Doxygen's Doxyfile path.
XML_PATH: Path = Path("_doxygen/xml/")

# Relative to root directory.
DOCUMENTATION_PATH: Path = Path(os.path.dirname(os.path.abspath(__file__)), "docs")
CPP_PATH: Path = Path("src/cpp/")
PY_PATH: Path = Path("src/py")
INCLUDE_PATH: Path = Path("include")

# ----------------------------------------------------------------------- Project Settings ----------------------------------------------------------------------- #

# Options: "Python", "Python/C++", "C++"
PROJECT_LANGUAGE: str = "Python"
PROJECT_NAME: str = "AutoDocs"
AUTHOR_NAME: str = "a22Dv"
PROJECT_RELEASE: str = "1.0"
LANGUAGE: str = "en"

# ----------------------------------------------------------------------- Advanced Settings ----------------------------------------------------------------------- #

doxygen_doxyfile_setup_lines: List[str] = [
    f"PROJECT_NAME = '{PROJECT_NAME}'",
    f"PROJECT_NUMBER = {PROJECT_RELEASE}",
    f"OUTPUT_DIRECTORY = ",
    f"CREATE_SUBDIRS = YES",
    f"INCLUDE_PATH = ../../{str(INCLUDE_PATH)} ",
    f"INPUT = include ../../{str(INCLUDE_PATH)} ../../{CPP_PATH}",
    "RECURSIVE = YES",             
    "FILE_PATTERNS = *.hpp, *.cpp",
    "GENERATE_HTML = NO",
    "GENERATE_LATEX = NO",                  
    "GENERATE_XML = YES",
    f"XML_OUTPUT = {str(XML_PATH)}",
    "XML_PROGRAMLISTING = YES",                
    "EXTRACT_ALL = YES",
    "EXTRACT_PRIVATE = YES",
    "EXTRACT_STATIC = YES",
    "WARN_IF_UNDOCUMENTED = YES"  
]

sphinx_conf_py_extensions: List[str] = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
]

sphinx_conf_py_setup_lines: List[str] = [
    f"project = '{PROJECT_NAME}'",
    f"copyright = '{datetime.date.today().year}, {AUTHOR_NAME}'",
    f"author = '{AUTHOR_NAME}'",
    f"release = '{PROJECT_RELEASE}'",    
    f"extensions = {sphinx_conf_py_extensions!r}",
    f"templates_path = ['_templates']",
    f"exclude_patterns = []",
    f"html_theme = 'furo'",
    f"html_static_path = ['_static']"
]

# ----------------------------------------------------------------------- Script ----------------------------------------------------------------------- #

if PROJECT_LANGUAGE in ("C++", "Python/C++"): # type: ignore
    sphinx_conf_py_extensions.append("breathe")
    sphinx_conf_py_setup_lines.extend([
        f"breathe_projects = {{'{PROJECT_NAME}' : '{str(XML_PATH).replace('\\', '/')}'}}",
        f"breathe_default_project = '{PROJECT_NAME}'"
    ])

if PROJECT_LANGUAGE in ("Python", "Python/C++"):
    sphinx_conf_py_setup_lines.insert(0, f"import sys\nimport os\nsys.path.insert(0, os.path.abspath('../../{str(PY_PATH).replace('\\', '/')}'))")

SPHINX_CONF_SETUP: str = "\n".join(sphinx_conf_py_setup_lines)

try:
    import sphinx  # type: ignore
except ImportError:
    print("Please run 'pip install sphinx")
    print("Cannot proceed without Sphinx. Aborting operation.")
    exit(1)

try:
    import furo # type: ignore
except ImportError:
    print("Please run 'pip install furo'")
    print("Cannot proceed without theme import.")
    exit(1)

if PROJECT_LANGUAGE in ("C++", "Python/C++"): # type: ignore
    if not shutil.which("doxygen"):  # type: ignore
        print("Doxygen not found. Cannot proceed. Aborting operation.")
        exit(1)
    try:
        import breathe # type: ignore
    except ImportError:
        print("Please run 'pip install breathe', cannot proceed C++ documentation without breathe. Aborting operation.")
        exit(1)

if not DOCUMENTATION_PATH.exists():
    DOCUMENTATION_PATH.mkdir()
elif input("Documentation path already exists. Running this script will delete everything in this path. Continue? (Y/N): ") in "Yy":
    shutil.rmtree(DOCUMENTATION_PATH)

sphinx_setup_process: subprocess.Popen[str] = subprocess.Popen(
    ["sphinx-quickstart", DOCUMENTATION_PATH],
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

if sphinx_setup_process.stdin:
    for command in ("y\n", f"{PROJECT_NAME}\n", f"{AUTHOR_NAME}\n", f"{PROJECT_RELEASE}\n", f"{LANGUAGE}\n"):
        sphinx_setup_process.stdin.write(command)
        sphinx_setup_process.stdin.flush()

    sphinx_setup_process.wait()
    check_exists: Tuple[bool, ...] = (
        (DOCUMENTATION_PATH / "source" / "conf.py").exists(),
        (DOCUMENTATION_PATH / "source" / "index.rst").exists(),
        (DOCUMENTATION_PATH / "source" / "_static").exists(),
        (DOCUMENTATION_PATH / "source" / "_templates").exists(),
        (DOCUMENTATION_PATH / "build").exists()
    )
    if not all(check_exists):
        print("Sphinx setup failed. Aborting operation.")
        exit(2)

with open(DOCUMENTATION_PATH / "source" / "conf.py", "w") as SPHINX_CONF:
    SPHINX_CONF.write(SPHINX_CONF_SETUP)

if PROJECT_LANGUAGE in ("C++", "Python/C++"): # type: ignore
    doxygen_process: subprocess.Popen[bytes] = subprocess.Popen(["doxygen", "-g"], cwd=DOCUMENTATION_PATH / "source")
    doxygen_process.wait()
    with open(DOCUMENTATION_PATH / "source" / "Doxyfile", "w") as DOXYFILE:
        DOXYFILE_SETUP: str = "\n".join(doxygen_doxyfile_setup_lines)
        DOXYFILE.write(DOXYFILE_SETUP)

# -- RST setup -- #

with open(DOCUMENTATION_PATH / "source" / "index.rst", "w") as I_RST:
    index_title: str = f"{PROJECT_NAME} Documentation"
    index_lines = [
        index_title,
        "=" * len(index_title),
        ".. toctree::",
        "   :maxdepth: 2",
        "   :caption: Contents:\n\n"
    ]
    I_RST.write("\n".join(index_lines))
    I_RST.close()
    

if "C++" in PROJECT_LANGUAGE:
    with open(DOCUMENTATION_PATH / "source" / "cpp.rst", "w") as CPP_RST:
        cpp_files: List[str] | None = os.listdir(DOCUMENTATION_PATH.parent / CPP_PATH).extend(os.listdir(INCLUDE_PATH))
        cpp_doc_title_length: int = len(f"{PROJECT_NAME} C++ Documentation")
        cpp_rst_lines: List[str] = [f"{PROJECT_NAME} C++ Documentation", "=" * cpp_doc_title_length]
        if cpp_files:
            cpp_rst_lines.extend([f".. doxygenfile:: {file}"for file in cpp_files])
        CPP_RST.write("\n".join(cpp_rst_lines))
    doxygen_process: subprocess.Popen[bytes] = subprocess.Popen(["doxygen", "Doxyfile"])
    doxygen_process.wait()

    with open(DOCUMENTATION_PATH / "source" / "index.rst", "a") as CPP_I_RST:
        CPP_I_RST.write("   cpp\n")
        
if "Python" in PROJECT_LANGUAGE:
    with open(DOCUMENTATION_PATH / "source" / "py.rst", "w") as PY_RST:
        py_files: List[str] | None = os.listdir(DOCUMENTATION_PATH.parent / PY_PATH)
        py_doc_title_length: int = len(f"{PROJECT_NAME} Python Documentation")
        py_rst_lines: List[str] = [f"{PROJECT_NAME} Python Documentation", "=" * py_doc_title_length]
        if py_files:
            py_rst_lines.extend([f".. automodule:: {file.removesuffix(".py")}\n   :members:\n   :undoc-members:\n   :show-inheritance:\n" for file in py_files])
        PY_RST.write("\n".join(py_rst_lines))
        with open(DOCUMENTATION_PATH / "source" / "index.rst", "a") as PY_I_RST:
            PY_I_RST.write("   py\n")


sphinx_build: subprocess.Popen[bytes] = subprocess.Popen(["sphinx-build", "-b", "html", ".", "../build"], cwd=DOCUMENTATION_PATH / "source")


    
        





