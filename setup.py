"""
setup.py – ZimAgent Desktop
"""

from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="zimagent-desktop",
    version="1.0.0",
    description="Offline CRUD + semantic search desktop app for Wikipedia ZIM archives",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ZimAgent Contributors",
    python_requires=">=3.9",
    packages=find_packages(),
    package_data={
        "zimagent": [
            "resources/style.qss",
            "resources/icons/*.png",
            "resources/icons/*.svg",
        ],
    },
    install_requires=[
        "PyQt5>=5.15.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "zim":     ["libzim>=3.3.0"],
        "rag":     ["turborag-ahx47"],
        "mcp":     ["fastmcp>=0.2.0"],
        "webview": ["PyQtWebEngine>=5.15.0"],
        "full":    ["libzim>=3.3.0", "turborag-ahx47", "fastmcp>=0.2.0",
                    "PyQtWebEngine>=5.15.0"],
    },
    entry_points={
        "console_scripts": [
            "zimagent = zimagent.main:main",
        ],
        "gui_scripts": [
            "zimagent-gui = zimagent.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Desktop Environment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
