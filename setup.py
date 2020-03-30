from setuptools import setup, find_packages

install_requires = [
    # "gurobipy",  # install this manually
    "matplotlib",
    "numpy",
    "click",
    "pyyaml",
    "jsonpickle",
    "unidecode",
    "networkx",
    "pytest"
]

setup(
    name="alib3",
    python_requires=">=3.7",
    packages=["alib3"],
    package_data={"alib3": ["data/topologyZoo/*.yml"]},
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "alib3 = alib3.cli:cli",
        ]
    }
)
