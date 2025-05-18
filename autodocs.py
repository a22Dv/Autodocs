import shutil
from subprocess import PIPE, Popen
import os
import sys
from pathlib import Path
from typing import Tuple, List
import datetime

# ------------------------------------------------------ General Settings  ------------------------------------------------------ #

# Relative to Doxygen's Doxyfile path.
# BUG: Clunky as hell, prone to breakage.
# Doxygen depends on it being only source/_doxygen/.
# Breathe needs it to be in source/_doxygen/xml/.
# Don't touch unless you know what you're doing. Refer to doxygen_doxyfile_setup_lines, OUTPUT_DIRECTORY.
XML_PATH: Path = Path("source/_doxygen/xml")

# Relative to root directory.
DOCUMENTATION_PATH: Path = Path(os.path.dirname(os.path.abspath(__file__)), "docs")
CPP_PATH: Path = Path("src/cpp/")
PY_PATH: Path = Path("src/py/")
INCLUDE_PATH: Path = Path("include")

# ------------------------------------------------------ Project Settings ------------------------------------------------------ #

# Options: "Python", "Python/C++", "C++"
PROJECT_LANGUAGE: str = "Python"
PROJECT_NAME: str = "Project Name"
AUTHOR_NAME: str = "Author"
PROJECT_RELEASE: str = "0.0"
LANGUAGE: str = "en"

# ------------------------------------------------------ Style Settings ------------------------------------------------------ #

# Checks for fonts are not implemented.
# Make sure the fonts are already installed on your device before running.
FONT_FAMILY_MAIN: str = "Instrument Sans"
FONT_FAMILY_MONOSPACE: str = "Cascadia Code"

# Checks for themes are not implemented. Script will crash or exhibit undefined behavior.
# Make sure the theme is already in your environment before running.
THEME: str = "furo"

# ------------------------------------------------------ Advanced Settings ------------------------------------------------------ #

doxygen_doxyfile_setup_lines: List[str] = [
    f"PROJECT_NAME = '{PROJECT_NAME}'",
    f"PROJECT_NUMBER = {PROJECT_RELEASE}",
    # XML_PATH.parent is due to doxygen's quirkiness when it comes to the output directory and the XML_OUTPUT.
    f"OUTPUT_DIRECTORY = {DOCUMENTATION_PATH / XML_PATH.parent}",
    f"CREATE_SUBDIRS = YES",
    f"INCLUDE_PATH = ../../{str(INCLUDE_PATH)} ",
    f"INPUT = ../../{str(INCLUDE_PATH)} ../../{str(CPP_PATH).replace("\\", "/")}",
    "RECURSIVE = YES",
    "FILE_PATTERNS = *.hpp, *.cpp",
    "GENERATE_HTML = NO",
    "GENERATE_LATEX = NO",
    "GENERATE_XML = YES",
    f"XML_OUTPUT = xml",
    "XML_PROGRAMLISTING = YES",
    "EXTRACT_ALL = YES",
    "EXTRACT_PRIVATE = YES",
    "EXTRACT_STATIC = YES",
    "WARN_IF_UNDOCUMENTED = YES",
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

if PROJECT_LANGUAGE in ("C++", "Python/C++"): # type: ignore
    sphinx_conf_py_extensions.append("breathe")

sphinx_conf_py_setup_lines: List[str] = [
    f"project = '{PROJECT_NAME}'",
    f"copyright = '{datetime.date.today().year}, {AUTHOR_NAME}'",
    f"author = '{AUTHOR_NAME}'",
    f"release = '{PROJECT_RELEASE}'",
    f"extensions = {sphinx_conf_py_extensions!r}",
    f"templates_path = ['_templates']",
    f"exclude_patterns = []",
    f"html_theme = '{THEME}'",
    f"html_static_path = ['_static']",
    f"html_css_files = ['custom.css']",
]

custom_css_lines: List[str] = [
    "body {",
    f"  --font-stack--monospace: {FONT_FAMILY_MONOSPACE};",
    "   --api-font-size: var(--font-size--small) !important;"
    f"  --font-stack: {FONT_FAMILY_MAIN} !important;",
    "}",
    ".sig-name {",
    "   color: var(--color-link) !important;",
    "}",
    ".sig-prename.descclassname {",
    "   color: var(--color-link) !important;",
    "}",
    "div.docutils.container {",
    "   em {",
    "       font-family: var(--font-stack--monospace) !important;",
    "       font-style: normal !important;",
    "       font-size: var(--font-size--small) !important;"
    "   }",
    "}",
    ".breathe-sectiondef-title.rubric {",
    "   font-weight: bold !important;",
    "   font-size: var(--font-size--normal) !important;",
    "}",
    "dt {",
    "   font-weight: bold !important;",
    "   font-size: var(--font-size--normal);",
    "}",
    "a:visited {",
    "   color: var(--color-link) !important;"
    "}"
]

# ------------------------------------------------------ Script ------------------------------------------------------ #

if PROJECT_LANGUAGE in ("C++", "Python/C++"):  # type: ignore
    sphinx_conf_py_setup_lines.extend(
        [
            f"breathe_projects = {{'{PROJECT_NAME}' : '{str(DOCUMENTATION_PATH / XML_PATH).replace('\\', '/')}'}}",
            f"breathe_default_project = '{PROJECT_NAME}'",
        ]
    )


if PROJECT_LANGUAGE in ("Python", "Python/C++"): # type: ignore
    sphinx_conf_py_setup_lines.insert(
        0,
        f"import sys\nimport os\nsys.path.insert(0, os.path.abspath('../../{str(PY_PATH).replace('\\', '/')}'))",
    )

SPHINX_CONF_SETUP: str = "\n".join(sphinx_conf_py_setup_lines)

# Check for Sphinx.
try:
    import sphinx  # type: ignore
except ImportError:
    print("Please run 'pip install sphinx")
    print("Cannot proceed without Sphinx. Aborting operation.")
    exit(1)

# Check for Doxygen.
if PROJECT_LANGUAGE in ("C++", "Python/C++"):  # type: ignore
    if not shutil.which("doxygen"):  # type: ignore
        print("Doxygen not found. Cannot proceed. Aborting operation.")
        exit(1)
    try:
        import breathe  # type: ignore
    except ImportError:
        print("Please run 'pip install breathe'.")
        print(
            "Cannot proceed with C++ documentation without breathe. Aborting operation."
        )
        exit(1)

# Check for rebuild command.
if len(sys.argv) == 2 and sys.argv[1] in ("-rb", "--rebuild"):
    if "C++" in PROJECT_LANGUAGE:
        doxygen_rebuild: Popen[bytes] = Popen(["doxygen", "Doxyfile"], cwd=DOCUMENTATION_PATH / "source")
        doxygen_rebuild.wait()
    sphinx_rebuild: Popen[bytes] = Popen(
        ["sphinx-build", "-b", "html", ".", "../build/"],
        cwd=DOCUMENTATION_PATH / "source",
    )
    sphinx_rebuild.wait()
    exit(0)

# Check for existing files.
if not DOCUMENTATION_PATH.exists():
    DOCUMENTATION_PATH.mkdir()
elif (
    input(
        "Documentation path already exists.\n"
        "Running this script will delete everything in this path.\n"
        "Continue? (Y/N): "
    )
    in "Yy"
):
    shutil.rmtree(DOCUMENTATION_PATH)

# Sphinx Process.
sphinx_setup_process: Popen[str] = Popen(
    ["sphinx-quickstart", DOCUMENTATION_PATH],
    stdout=PIPE,
    stdin=PIPE,
    stderr=PIPE,
    text=True,
)

if sphinx_setup_process.stdin:
    for command in (
        "y\n",
        f"{PROJECT_NAME}\n",
        f"{AUTHOR_NAME}\n",
        f"{PROJECT_RELEASE}\n",
        f"{LANGUAGE}\n",
    ):
        sphinx_setup_process.stdin.write(command)
        sphinx_setup_process.stdin.flush()

    sphinx_setup_process.wait()

    # Check for success.
    check_exists: Tuple[bool, ...] = (
        (DOCUMENTATION_PATH / "source" / "conf.py").exists(),
        (DOCUMENTATION_PATH / "source" / "index.rst").exists(),
        (DOCUMENTATION_PATH / "source" / "_static").exists(),
        (DOCUMENTATION_PATH / "source" / "_templates").exists(),
        (DOCUMENTATION_PATH / "build").exists(),
    )
    if not all(check_exists):
        print("Sphinx setup failed. Aborting operation.")
        exit(2)

# Setup conf.py.
with open(DOCUMENTATION_PATH / "source" / "conf.py", "w") as SPHINX_CONF:
    SPHINX_CONF.write(SPHINX_CONF_SETUP)

# Setup Doxyfile.
if PROJECT_LANGUAGE in ("C++", "Python/C++"):  # type: ignore
    doxygen_process: Popen[bytes] = Popen(
        ["doxygen", "-g"], cwd=DOCUMENTATION_PATH / "source"
    )
    doxygen_process.wait()
    with open(DOCUMENTATION_PATH / "source" / "Doxyfile", "w") as DOXYFILE:
        DOXYFILE_SETUP: str = "\n".join(doxygen_doxyfile_setup_lines)
        DOXYFILE.write(DOXYFILE_SETUP)


# Setup index.rst.
with open(DOCUMENTATION_PATH / "source" / "index.rst", "w") as I_RST:
    index_title: str = f"{PROJECT_NAME} Documentation"
    index_lines = [
        index_title,
        "=" * len(index_title),
        ".. toctree::",
        "   :maxdepth: 2\n\n",
    ]
    I_RST.write("\n".join(index_lines))
    I_RST.close()


# Setup C++ .rst branch and Doxygen build.
if "C++" in PROJECT_LANGUAGE:
    with open(DOCUMENTATION_PATH / "source" / "cpp.rst", "w") as CPP_RST:
        cpp_files: List[str] | None = os.listdir(DOCUMENTATION_PATH.parent / CPP_PATH)
        cpp_files.extend(os.listdir(INCLUDE_PATH))
        cpp_doc_title_length: int = len(f"{PROJECT_NAME} C++ Documentation")
        cpp_rst_lines: List[str] = [
            f"{PROJECT_NAME} C++ Documentation",
            "=" * cpp_doc_title_length,
        ]
        if cpp_files:
            cpp_rst_lines.extend([f".. doxygenfile:: {file}\n\n" for file in cpp_files])
        CPP_RST.write("\n".join(cpp_rst_lines))
    doxygen_process: Popen[bytes] = Popen(
        ["doxygen", "Doxyfile"], cwd=DOCUMENTATION_PATH / "source"
    )
    doxygen_process.wait()
    with open(DOCUMENTATION_PATH / "source" / "index.rst", "a") as CPP_I_RST:
        CPP_I_RST.write("   cpp\n")


# Setup Python .rst branch.
if "Python" in PROJECT_LANGUAGE:
    with open(DOCUMENTATION_PATH / "source" / "py.rst", "w") as PY_RST:
        py_files: List[str] | None = os.listdir(DOCUMENTATION_PATH.parent / PY_PATH)
        py_doc_title_length: int = len(f"{PROJECT_NAME} Python Documentation")
        py_rst_lines: List[str] = [
            f"{PROJECT_NAME} Python Documentation",
            "=" * py_doc_title_length,
        ]
        if py_files:
            py_rst_lines.extend(
                [
                    f".. automodule:: {file.removesuffix(".py")}\n   :members:\n   :undoc-members:\n   :show-inheritance:\n"
                    for file in py_files
                ]
            )
        PY_RST.write("\n".join(py_rst_lines))
        with open(DOCUMENTATION_PATH / "source" / "index.rst", "a") as PY_I_RST:
            PY_I_RST.write("   py\n")

# CSS changes.
with open(DOCUMENTATION_PATH / "source" / "_static" / "custom.css", "w") as CUSTOM_CSS:
    CUSTOM_CSS.write("\n".join(custom_css_lines))


# Final build.
sphinx_build: Popen[bytes] = Popen(
    ["sphinx-build", "-b", "html", ".", "../build"], cwd=DOCUMENTATION_PATH / "source"
)
