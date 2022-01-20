# BrainIO
[![Build Status](https://travis-ci.com/brain-score/brainio.svg?branch=main)](https://travis-ci.com/brain-score/brainio)

# What is BrainIO?
BrainIO is a framework for standardizing the exchange of data between 
experimental and computational neuroscientists.  It includes a minimal 
specification for packaged data and tools for working with that packaged data.  

[Glossary](docs/glossary.md)

[BrainIO Format Specification](docs/SPECIFICATION.md) 

Currently the tools are written in [Python](https://www.python.org/), but the format is language-agnostic.

## Why use BrainIO?
* To safeguard the **value** of the data you have collected by ensuring it never gets separated from its metadata.  
* To adopt a **consistent format** in order to provide a minimum level of interoperability.  
* For a fair exchange of effort.  BrainIO is intended to find a **balance** between the effort it requires of the consumer of data and the effort it requires of the provider of data, and to minimize both where possible.  
## Terms and Concepts
There are three terms that are important to understanding BrainIO:  
* **Stimulus Set**
* **Data Assembly**
* **BrainIO Catalog**

We define these terms below.  For other terms, see the [glossary](docs/glossary.md).  

A **Stimulus Set** is a collection of stimuli intended for use in experiments, packaged so that it is organized and easy to obtain.  The parts of a Stimulus Set are:
* a CSV file of metadata
* a ZIP file of stimuli
* a few [rules](docs/SPECIFICATION.md) for how the metadata are organized (like, include a column called "image_id")

A **Data Assembly** is a coherent body of data collected during an experiment, packaged with the metadata which describe it.  The term "assembly" is used in engineering for a set of parts that have been assembled to form a coherent unit.  The parts of a Data Assembly are:
* a [netCDF](https://www.unidata.ucar.edu/software/netcdf/) file containing numeric data and metadata
* a few [rules](docs/SPECIFICATION.md) about what's in the netCDF file (names for dimensions, a reference to a stimulus set)

A **BrainIO Catalog** is a list of Stimulus Sets and Data Assemblies that provides information on how to obtain them and load them into memory.  The only thing a BrainIO Catalog requires is a CSV file containing [specified](docs/SPECIFICATION.md) lookup data for Stimulus Sets And Data Assemblies.

# Installing The BrainIO Python Tools

There are two main ways to install BrainIO, corresponding to two of the main ways of using it:  
* For obtaining and using packaged stimuli and data
* For creating new packages of stimuli and data and adding them to an existing catalog

These are described below.  We recommend installing in a managed Python environment like a `conda` environment.  

## Install BrainIO As A Consumer of Packages

1. Install BrainIO using `pip` in an existing environment
    1. Activate your environment.
    1. `pip install git+https://github.com/brain-score/brainio.git`
1. Install a project that provides a BrainIO Catalog
    * If you intend to use a BrainIO catalog to access data or stimuli that have already been packaged, you will need to install the project that provides the catalog that you intend to use.  Here we illustrate with a project called `brainio-dicarlo` provided by the DiCarlo Lab:  
    1. Activate your environment
    1. `pip install git+https://github.com/dicarlolab/brainio-dicarlo.git`
    * This registers the catalog with the Python interpreter in your environment 
so that the BrainIO tools can use it.  

## Install BrainIO As A Provider Of Packages

If you intend to package Stimulus Sets And Data Assemblies and add them to a project's catalog, instead of installing the project as above, you will need to clone the repository for that project and install it in your environment in editable mode.  In the example below we set up to add to `brianio-dicarlo`'s BrainIO Catalog:  

1.  Activate your environment.  
1.  Change to the directory where you store your [Git](https://git-scm.com/) repositories:  
`cd ~/projects`
1.  `git clone https://github.com/dicarlolab/brainio-dicarlo.git`
1.  `pip install -e brainio-dicarlo`

You should now have a directory `~/projects/brainio-dicarlo` which contains the 
source for the project.  Packaging and cataloging are covered below.  

# Using The BrainIO Python Tools

There are three main ways to use the Python BrainIO tools:
* To access and analyze stimuli and data that are already packaged and cataloged.
* To add packages of stimuli and data to an existing catalog. 
* To create a new project that provides a catalog.   

## Using Packaged Stimulus Sets And Data Assemblies

Here we provide an example of using BrainIO in a Python interactive interpreter session, retrieving a Stimulus Set and a Data Assembly and displaying their text representations, and retrieving a stimulus file.  The types of the returned objects are `StimulusSet`, a subclass of a [pandas](https://pandas.pydata.org/) `DataFrame`, and `DataAssembly`, a subclass of an [xarray](https://xarray.pydata.org/) `DataArray`.  We use the functions `get_stimulus_set` and `get_assembly` and the `StimulusSet` method `get_image`:

```shell
(my-project) $ python
Python 3.8.0 (default, Nov  6 2019, 15:49:01)
[Clang 4.0.1 (tags/RELEASE_401/final)] :: Anaconda, Inc. on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from brainio import get_assembly, get_stimulus_set
>>> hvm_stim = get_stimulus_set("dicarlo.hvm")
>>> hvm_stim
        id                             background_id         s  ... rxy_semantic ryz_semantic        rxz
0        1  ecd40f3f6d7a4d6d88134d648884e0b9b364efc9  1.000000  ...    90.000000    -0.000000   0.000000
1        2  006d66c207c6417574f62f0560c6b2b40a9ec5a1  1.000000  ...    -0.000000    -0.000000   0.000000
...
5758  5759  2363c8c3859603ee9db7f83dd7ba5b6989154258  0.791250  ...   -75.159000    12.283000  29.466000
5759  5760  a7fc954d2bd08fc2c4d3ade347f41a03a5850131  1.050000  ...   -67.467580     7.598457 -25.152591

[5760 rows x 18 columns]
>>> hvm_assy = get_assembly("dicarlo.MajajHong2015.public")
>>> hvm_assy
<xarray.NeuronRecordingAssembly 'dicarlo.MajajHong2015.public' (neuroid: 256, presentation: 148480, time_bin: 1)>
array([[[ 0.06092933],
        [-0.8479065 ],
...
        [ 1.0052351 ],
        [-0.2989609 ]]], dtype=float32)
Coordinates:
  * neuroid          (neuroid) MultiIndex
  - neuroid_id       (neuroid) object 'Chabo_L_M_5_9' ... 'Tito_L_M_8_0'
...
  * time_bin         (time_bin) MultiIndex
  - time_bin_start   (time_bin) int64 70
  - time_bin_end     (time_bin) int64 170
Attributes:
    stimulus_set_identifier:  dicarlo.hvm-public
    stimulus_set:                     id                             backgrou...
    identifier:               dicarlo.MajajHong2015.public

>>> hvm_stim.get_image("ecd40f3f6d7a4d6d88134d648884e0b9b364efc9")
"/Users/me/.brainio/image_dicarlo_hvm/astra_rx+00.000_ry+00.000_rz+00.000_tx+00.000_ty+00.000_s+01.000_ecd40f3f6d7a4d6d88134d648884e0b9b364efc9_256x256.png"
```

## Packaging And Cataloging Stimulus Sets And Data Assemblies In An Existing Catalog

To package Stimulus Sets and Data Assemblies and add them to a BrainIO Catalog, 
first install a project in editable mode as described above.  Make sure you have 
commit privileges on [GitHub](https://github.com/) for the repository you're editing.  Then (using the 
same example as above):  

1.  Activate your environment.
1.  `cd ~/projects/brainio-dicarlo`
1.  Create a new Git branch (the branch name doesn't really matter):  
`git branch dicarlo.Me2025.public`
1.  `git checkout dicarlo.Me2025.public`
1.  Write a script that packages your Stimulus Set and/or Data Assembly.  
We'll call our example `brainio-dicarlo/packaging/scripts/me2025.py`.
    * Examples can be found in the packaging directory:  `packaging/scripts/`.
    * The packaging scripts in a repository serve as a historical record.  The 
  interface to the BrainIO API may have changed since a given script was written.
  Notably, the `package_stimulus_set` and `package_data_assembly` functions now 
  require a `catalog_name` argument.  In this example we would use 
  `"brainio-dicarlo"`.  
1.  `git add packaging/scripts/me2025.py`
1.  `git commit -m "Added script for dicarlo.Me2025.public"`
1.  `git push`
1.  Run your script.  Make sure lines for your packaged files are now present in 
the catalog file at `brainio_dicarlo/lookup.csv`.  
1.  `git add brainio_dicarlo/lookup.csv`
1.  `git commit -m "Packaged dicarlo.Me2025.public"`
1.  `git push`
1.  In the [GitHub](https://github.com/) web interface for the project, open a Pull Request for your branch.  

Depending on the configuration of the project, once a colleague reviews your 
changes and approves them, you can merge the pull request to `main`, and your 
packaged Stimulus Sets and Data Assemblies will be available to anyone who 
installs the project.  

## Creating A New Project That Provides A Catalog

```shell
mkdir -p ~/projects/my-project/my_project
cd ~/projects/my-project/
touch setup.py my_project/entrypoint.py my_project/lookup.csv /my_project/__init__.py
echo include my_project/lookup.csv > MANIFEST.in
```
Use your favorite editor to edit `setup.py`:  
```python
from setuptools import setup, find_packages

setup(
    name='my-project',
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "brainio @ git+https://github.com/brain-score/brainio",
    ],
    entry_points={
        'my_project': [
            'my_project = my_project.entrypoint:my_project',
        ],
    },)
```
Then edit `entrypoint.py`:  
```python
import logging
from pathlib import Path
import pandas as pd
from brainio.lookup import CATALOG_PATH_KEY

_logger = logging.getLogger(__name__)

def my_project():
    path = Path(__file__).parent / "lookup.csv"
    _logger.debug(f"Loading lookup from {path}")
    print(f"Loading lookup from {path}") 
    df = pd.read_csv(path)
    df.attrs[CATALOG_PATH_KEY] = str(path)
    return df
```
Now install your project in editable mode:  
```shell
conda create -n my-project python==3.8
conda activate my-project
pip install -e ~/projects/my-project
```
You should now be able to use packaging scripts (with the argument 
`catalog_name=my_project`) to add to your catalog.  
# Getting Help

If you have questions, [get in touch with us]("mailto:jjpr@mit.edu?subject=BrainIO question).

# License

[MIT License](LICENSE)


