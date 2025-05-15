from setuptools import setup, find_packages
from paper_utils import __version__

setup(
    name='paper_utils',
    version=__version__,

    url='https://github.com/katherine-atwell/paper-utils',
    author='Katherine Atwell',
    author_email='atwell.ka@northeastern.edu',

    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'seaborn',
        'scikit-learn',
        'scipy',
        'statsmodels',
        'nltk',
        'requests',
        'tqdm',
        'pytest'
    ],
)