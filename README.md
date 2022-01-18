# BrainIO
[![Build Status](https://travis-ci.com/brain-score/brainio.svg?branch=main)](https://travis-ci.com/brain-score/brainio)

## What is BrainIO?
BrainIO is a framework for standardizing the exchange of data between 
computational neuroscientists.  It includes a minimal specification for 
packaged data and tools for working with that packaged data.  

Currently the tools are written in Python, but the 
[BrainIO Format Specification](docs/SPECIFICATION.md) is language-agnostic.

### Why use BrainIO?
#### To Safeguard The Value Of Data You Have Collected
* All data decays in usefulness as it gets farther from the place and time where it was collected
* Other people will know less than you about what the data means and how to use it
* **Future you** will know less than **present you** about what the data means and how to use it
* If you can help that knowledge accompany the data on its travels, you can expand the contexts in which it is useful 
#### To Adopt A Consistent Format
* Everyone stores their data differently.  One person uses a single monolithic CSV file, another uses five separate CSV files;  one keeps data in the proprietary binary format the instrument produces, yet another uses a fifteen year old version of MATLAB  
* In principle data in one style of organization can be transformed to any other style of organization
* In practice people are rarely willing to spend the time to translate multiple conventions to the same format just so they can use data from multiple sources  
#### For A Fair Exchange Of Effort
BrainIO is intended to find a balance between the effort it requires of the consumer of data and the effort it requires of the provider of data, and to minimize both where possible.  
### Terms and Concepts
The [BrainIO Format Specification](docs/SPECIFICATION.md) defines three types of entity:  
* A Stimulus Set
* A Data Assembly
* A BrainIO Catalog

A **Stimulus Set** consists of:
* a CSV file of metadata
* a zip file of stimuli
* a few rules for how the metadata are organized (like, include a column called "image_id")

A **Data Assembly** consists of:
* a netCDF file containing numeric data and metadata
* a few rules about what's in the netCDF file (names for dimensions, a reference to a stimulus set)

A **BrainIO Catalog** consists of:  
* a CSV file containing specified lookup data for Stimulus Sets And Data Assemblies

### Further information:  

[The BrainIO Format Specification](docs/SPECIFICATION.md)

[Glossary](docs/glossary.md)

## Installing BrainIO

We recommend installing in a managed Python environment like a `conda` environment.  

### Install BrainIO with `pip` in an Existing Interpreter or Environment

* Activate your environment.
* `pip install git+https://github.com/brain-score/brainio.git`

### Install a Project That Provides a BrainIO Catalog

If you intend to use a BrainIO catalog to access data or stimuli that have already 
been packaged, you will need to install the project that provides the catalog that 
you intend to use.  Here we illustrate with a project called `brainio-dicarlo` 
provided by the DiCarlo Lab:  

* Activate your environment.  
* `pip install git+https://github.com/dicarlolab/brainio-dicarlo.git`

This registers the catalog with the Python interpreter in your environment 
so that the BrainIO tools can use it.  

### Set Up To Add To A Project That Provides a BrainIO Catalog

If you intend to package Stimulus Sets And Data Assemblies and add them 
to a project's catalog, instead of installing the project as above, you will need to clone the repository for that project and 
install it in your environment in editable mode.  In the example below we set up to 
add to `brianio-dicarlo`'s BrainIO Catalog:  

* Activate your environment.  
* Change to the directory where you store your Git repositories:  
`cd ~/projects`
* `git clone https://github.com/dicarlolab/brainio-dicarlo.git`
* `pip install -e brainio-dicarlo`

You should now have a directory `~/projects/brainio-dicarlo` which contains the 
source for the project.  Packaging and cataloging are covered below.  

## Using Python BrainIO tools

There are three main ways to use the Python BrainIO tools:
* To access and analyze stimuli and data that are already packaged and cataloged.
* To package stimuli and data in an existing catalog. 
* To create a new catalog.   

### Using Packaged Stimulus Sets And Data Assemblies

An example, retrieving a Stimulus Set and a Data Assembly and displaying their text representations:

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


```

### Packaging And Cataloging Stimulus Sets And Data Assemblies In An Existing Catalog

To package Stimulus Sets and Data Assemblies and add them to a BrainIO Catalog, 
first install a project in editable mode as described above.  Make sure you have 
commit privileges on GitHub for the repository you're editing.  Then (using the 
same example as above):  

* Activate your environment.
* `cd ~/projects/brainio-dicarlo`
* Create a new Git branch (the branch name doesn't really matter):  
`git branch dicarlo.Me2025.public`
* `git checkout dicarlo.Me2025.public`
* Write a script that packages your Stimulus Set and/or Data Assembly.  
We'll call our example `brainio-dicarlo/packaging/scripts/me2025.py`.
  * Examples can be found in the packaging directory:  `packaging/scripts/`.
  * The packaging scripts in a repository serve as a historical record.  The 
  interface to the BrainIO API may have changed since a given script was written.
  Notably, the `package_stimulus_set` and `package_data_assembly` functions now 
  require a `catalog_name` argument.  In this example we would use 
  `"brainio-dicarlo"`.  
* `git add packaging/scripts/me2025.py`
* `git commit -m "Added script for dicarlo.Me2025.public"`
* `git push`
* Run your script.  Make sure lines for your packaged files are now present in 
the catalog file at `brainio_dicarlo/lookup.csv`.  
* `git add brainio_dicarlo/lookup.csv`
* `git commit -m "Packaged dicarlo.Me2025.public"`
* `git push`
* In the GitHub web interface for the project, open a Pull Request for your branch.  

Depending on the configuration of the project, once a colleague reviews your 
changes and approves them, you can merge the pull request to `main`, and your 
packaged Stimulus Sets and Data Assemblies will be available to anyone who 
installs the project.  

### Creating A New Project That Provides A Catalog

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
## Getting Help

If you have questions, [get in touch with us]("mailto:jjpr@mit.edu,mferg@mit.edu?subject=Brain-Score submission).  

## License

[MIT License](LICENSE)


