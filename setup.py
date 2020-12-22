import setuptools

setuptools.setup(
    name="chg",  # Replace with your own username
    version="0.0.1",
    author="Example Author",
    author_email="author@example.com",
    description="chgstructor",
    long_description="TODO",
    url="TODO",
    packages=setuptools.find_packages(),
    scripts=[
        "bin/chg",
        "bin/git-to-chg",
        "chg/scripts/build_semantic_db.sh",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
