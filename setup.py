import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="parse-utils",
    version="1.3.2",
    author="Yogendra Tamang",
    author_email="48yogen@gmail.com",
    description="Page Parser Utils For scraping, List index update",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yogendratamang48/parse_utils.git",
    packages=setuptools.find_packages(),
    install_requires=["lxml"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.5",
)
