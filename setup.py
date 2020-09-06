import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as requirements:
    install_requires = [x.replace("\n", "") for x in requirements.readlines()]

setuptools.setup(
    name="fluxo-aws",
    version="0.0.25",
    author="Brenno Flavio",
    author_email="brenno.flavio@fluxoresultados.com.br",
    description="Provides a bunch of functions and utils to help you build applications on top of Amazon Web Services Resources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Fluxo-Resultados/fluxo-aws",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
)
