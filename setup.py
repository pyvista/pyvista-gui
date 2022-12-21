"""
Installation file for python pyvista_gui module
"""
import os
from io import open as io_open

from setuptools import setup

package_name = "pyvista_gui"

__version__ = None
filepath = os.path.dirname(__file__)
version_file = os.path.join(filepath, package_name, "_version.py")
with io_open(version_file, mode="r") as fd:
    exec(fd.read())

# pre-compiled vtk available for python3
install_requires = [
    "pyvista>=0.22.4",
    "PyQt5>=5.11.3",
    "scooby>=0.2.2",
    "matplotlib",
    "pyvistaqt",
    "qdarkstyle",
    "qtconsole",
]

readme_file = os.path.join(filepath, "README.md")

setup(
    name=package_name,
    packages=[package_name],
    version=__version__,
    description="Easier Pythonic interface to VTK",
    long_description=io_open(readme_file, encoding="utf-8").read(),
    author="PyVista Developers",
    author_email="info@pyvista.org",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    url="https://github.com/pyvista/pyvista_gui",
    keywords="vtk numpy plotting mesh gui",
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*",
    install_requires=install_requires,
)
