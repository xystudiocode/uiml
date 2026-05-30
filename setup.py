from setuptools import setup, find_packages

setup(
    name = "uiml",
    version = "0.1.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires = ["PySide6>=6.10.0"],
    python_requires = ">=3.10",
    author = "xystudio",
    author_email = "173288240@qq.com",
    description = "",
    long_description = open("README.md",encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license = "MIT",
    url = "https://github.com/xystudio889/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords = ['uiml', 'PySide6', 'Qt', 'ui', 'xml', 'design'],
)
