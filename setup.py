from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "cec_lib",
        ["cec_lib.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++"
    ),
]

setup(
    name="cec-control",
    version="0.1",
    ext_modules=ext_modules,
    py_modules=["cli"],
    entry_points={
        "console_scripts": [
            "cec-control = cli:main",  # This creates a CLI command named 'mycli'
        ],
    }
)