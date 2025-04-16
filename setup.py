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
    description="A HDMI-CEC host that track CEC messages and control the PC with by the TV remote",
    author="Rosen Kolev",
    author_email="rosen.kolev@hotmail.com",
    ext_modules=ext_modules,
    py_modules=[],
    entry_points={
        "console_scripts": [
            "cec-control = cec_control.main:main",  # This creates a CLI command
        ],
    },
    packages=["cec_control"],
    include_package_data=True,
)
