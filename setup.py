"""
Starling setup script.

See license in LICENSE.txt.
"""

import setuptools
import os
from starling_sim.version import __version__

# short description of the project
DESC = "Agent-based framework for mobility simulation"

# get long description from README.md
# with open("README.md", "r") as fh:
#     LONG_DESC = fh.read()
LONG_DESC = "Long description of the Starling project (TODO)"

# list of classifiers from the PyPI classifiers trove
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Scientific/Engineering :: GIS",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "License :: CeCILL-B Free Software License Agreement (CECILL-B)"
]

# only specify install_requires if not in RTD environment
if os.getenv("READTHEDOCS") == "True":
    INSTALL_REQUIRES = []
else:
    with open("requirements.txt") as f:
        INSTALL_REQUIRES = [line.strip() for line in f.readlines()]

# call setup
setuptools.setup(
    name="starling-sim",
    version=__version__,
    license="CECILL-B",
    author="Tellae",
    author_email="starling@tellae.fr",
    description=DESC,
    long_description=LONG_DESC,
    long_description_content_type="text/markdown",
    url="https://github.com/tellae/starling",
    packages=setuptools.find_packages() + ["starling_sim/schemas"],
    classifiers=CLASSIFIERS,
    python_requires='>=3.6',
    install_requires=INSTALL_REQUIRES,
    include_package_data=True
)
