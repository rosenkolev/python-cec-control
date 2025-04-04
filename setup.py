import pybind11
from setuptools import Extension, setup

ext_modules = [
    Extension(
        "cec_control.cec_lib",
        ["cec_control/bindings.cpp", "cec_control/cec_lib.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
    ),
]

setup(
    name="cec_control",
    version="0.1",
    author="Rosen Kolev",
    author_email="rosen.kolev@hotmail.com",
    ext_modules=ext_modules,
    py_modules=["cec_control.cec"],
    entry_points={
        "console_scripts": [
            "cec-control = cec_control.cli:main",  # This creates a CLI command
        ],
    },
    packages=["cec_control"],
    ext_package=["uinput"],
    include_package_data=True,
)
