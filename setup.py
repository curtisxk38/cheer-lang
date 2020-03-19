from setuptools import setup, find_packages

setup(
    name="cheer-lang",
    packages=find_packages(),
    description="A compiler for CheerLang",
    extras_require={
        'test': [
            'mypy',
            'flake8',
            'pytest',
        ]
    })