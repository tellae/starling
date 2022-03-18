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
LONG_DESC = r"""
**Starling** is an agent-based framework for mobility simulation. Users can download and model walkable, drivable, or
bikeable urban networks with a single line of Python code, and then easily
analyze and visualize them. You can just as easily download and work with
amenities/points of interest, building footprints, elevation data, street
bearings/orientations, speed/travel time, and network routing.
Citation info: Boeing, G. 2017. `OSMnx: New Methods for Acquiring,
Constructing, Analyzing, and Visualizing Complex Street Networks`_.
*Computers, Environment and Urban Systems* 65, 126-139.
doi:10.1016/j.compenvurbsys.2017.05.004
Read the `docs`_ or see usage examples and demos on `GitHub`_.
.. _GitHub: https://github.com/gboeing/osmnx-examples
.. _docs: https://osmnx.readthedocs.io
.. _OSMnx\: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks: http://geoffboeing.com/publications/osmnx-complex-street-networks/
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
