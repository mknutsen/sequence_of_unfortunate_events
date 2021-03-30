import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="unfortunate_sequencer",  # Replace with your own username
    version="0.0.1",
    author="Example Author",
    author_email="author@example.com",
    description="A larg example package",
    classifiers=[
        "Programming Language :: Python :: 3",
        "SORRY :: HI",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=['mido', 'pygame', 'python-rtmidi']
)
