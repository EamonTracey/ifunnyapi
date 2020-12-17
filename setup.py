import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="ifunnyapi",
    version="0.0.8",
    author="Eamon Tracey",
    description="Interact with iFunny's API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "pillow",
        "requests"
    ],
    url="https://github.com/EamonTracey/ifunnyapi",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
