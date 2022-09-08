"""
Starling setup script.

See license in LICENSE.txt.
"""

import setuptools
import os
from starling_sim import __version__

# short description of the project
DESC = "Agent-based framework for mobility simulation"

# get long description from README.md
# with open("README.md", "r") as fh:
#     LONG_DESC = fh.read()
LONG_DESC = r"""
**Starling** is an agent-based framework for mobility simulation implemented in Python. 
The framework provides users with tools to quickly develop agent-based simulators of a specific transport service.
Among these tools, there is a number of generic transport classes that can be used in several transport contexts,
accessible input and output formats (JSON, GeoJSON) with JSON schema specifications, visualisation and KPI outputs, etc.

**Starling** also comes with three simulation models :

 - A free-floating vehicle-sharing service
 - A station-based vehicle-sharing service
 - A station-based vehicle-sharing service with repositioning

**For now, Starling is not adapted to be used as a package : users should rather clone the project 
locally to develop and run new simulations.**

Read the `docs`_ or see the project on `Github`_.

Citation info: Leblond, V, Desbureaux, L, Bielecki, V., 2020. `A new agent-based software for designing and 
optimizing emerging mobility services : application to city of Rennes`_. 
*Proceedings of the European Transport Conference*, 11 September 2020, Milan.

.. _Github: https://github.com/tellae/starling
.. _docs: https://starling.readthedocs.io/en/latest/
.. _A new agent-based software for designing and optimizing emerging mobility services \: application to city of Rennes : https://aetransport.org/past-etc-papers/conference-papers-2020?abstractId=6706&state=b
"""

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
    "License :: CeCILL-B Free Software License Agreement (CECILL-B)",
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
    long_description_content_type="text/x-rst",
    long_description=LONG_DESC,
    url="https://github.com/tellae/starling",
    packages=setuptools.find_packages() + ["starling_sim/schemas"],
    classifiers=CLASSIFIERS,
    python_requires=">=3.6",
    install_requires=INSTALL_REQUIRES,
    include_package_data=True,
)
