from setuptools import setup

setup(
    name="mp3_linter",
    version="0.1.0",
    author="Jelmer van Arnhem",
    description="Opinionated & consistent ID3 linter & fixer",
    license="MIT",
    py_modules=["mp3_linter"],
    include_package_data=True,
    python_requires=">= 3.5.*",
    setup_requires=["setuptools"],
    install_requires=["pillow", "stagger", "tinytag"],
    entry_points={"console_scripts": ["mp3_linter= mp3_linter:main"]}
)
