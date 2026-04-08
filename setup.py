from setuptools import find_packages, setup

setup(
    name="andes",
    version="0.1.0",
    description="ANDES: Agent Native Data Evolving Synthetis for Agentic Post-training",
    packages=find_packages(include=["andes", "andes.*"]),
    include_package_data=True,
    install_requires=[
        "pandas>=1.5",
        "requests>=2.28",
        "tqdm>=4.65",
    ],
    python_requires=">=3.10",
)
