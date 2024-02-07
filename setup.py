import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ocadsvalidator",
    version="0.0.1",
    author="Xingjian Xu and Steven Mugisha Mizero",
    description="Quicksample Test Package for SQLShack Demo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: EUP License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    py_modules=["quicksample"],
    package_dir={'':'quicksample/src'},
    install_requires=[]
)