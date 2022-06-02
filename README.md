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
* a few [rules](docs/SPECIFICATION.md) for how the metadata are organized (like, include a column called "stimulus_id")

A **Data Assembly** is a coherent body of data collected during an experiment, packaged with the metadata which describe it.  The term "assembly" is used in engineering for a set of parts that have been assembled to form a coherent unit.  The parts of a Data Assembly are:
* a [netCDF-4](https://www.unidata.ucar.edu/software/netcdf/) file (internally an [HDF5](https://www.hdfgroup.org/solutions/hdf5/) file) containing numeric data and metadata
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
    * If you intend to use a BrainIO catalog to access data or stimuli that have already been packaged, you will need to install the project that provides the catalog that you intend to use.  Here we illustrate with [a project called `brainio-dicarlo`](https://github.com/dicarlolab/brainio-dicarlo) provided by the DiCarlo Lab:  
    1. Activate your environment
    1. `pip install git+https://github.com/dicarlolab/brainio-dicarlo.git`
    * This registers the catalog with the Python interpreter in your environment 
so that the BrainIO tools can use it.  

## Install BrainIO As A Provider Of Packages

If you intend to package Stimulus Sets And Data Assemblies and add them to a project's catalog, instead of installing the project as above, you will need to clone the repository for that project and install it in your environment in editable mode.  In the example below we set up to add to the BrainIO Catalog provided by [a project called `brainio-dicarlo`](https://github.com/dicarlolab/brainio-dicarlo):  

1.  Activate your environment.  
1.  Change to the directory where you store your [Git](https://git-scm.com/) repositories:  
`cd ~/projects`
1.  `git clone https://github.com/dicarlolab/brainio-dicarlo.git`
1.  `pip install -e brainio-dicarlo`

You should now have a directory `~/projects/brainio-dicarlo` which contains the 
source for the project.  Packaging and cataloging are covered below.  

# Using The BrainIO Python Tools

## Basic API

The most commonly used methods of the BrainIO API are:  

* **List Stimulus Sets**:  `brainio.list_stimulus_sets()` lists the identifiers of all the BrainIO stimulus sets available via your installed catalogs.  
* **List Data Assemblies**:  `brainio.list_assemblies()` lists the identifiers of all the BrainIO data assemblies available via your installed catalogs.  
* **List Catalogs**: `brainio.list_catalogs()` lists the identifiers of all the BrainIO catalogs installed in your current Python environment.  


* **Get Stimulus Set**:  `brainio.get_stimulus_set(identifier)` looks up, fetches, loads and returns the stimulus set matching the given unique identifier.  
* **Get Data Assembly**:  `brainio.get_assembly(identifier)` looks up, fetches, loads and returns the data assembly matching the given unique identifier (including getting any associated stimulus set).  


* **Stimulus Set From Files**:  `brainio.stimuli.StimulusSet.from_files(csv_path, dir_path)` loads into memory a stimulus set contained in the provided files.  
* **Data Assembly From Files**:  `brainio.assemblies.DataAssembly.from_files(file_path, **kwargs)` loads into memory a data assembly contained in the provided file.  Usually called from a subclass of DataAssembly.  

## Types of Usage

There are four main ways to use the Python BrainIO tools:
* To look up and fetch stimuli and data that are packaged and cataloged.
* To access and analyze stimuli and data stored in files conforming to the [BrainIO Format Specification](docs/SPECIFICATION.md)
* To add packages of stimuli and data to an existing catalog. 
* To create a new project that provides a catalog.   

### Using Packaged and Cataloged Stimulus Sets And Data Assemblies

Here's an example of using BrainIO in a Python interactive interpreter session, retrieving a Stimulus Set and a Data Assembly and displaying their text representations, and retrieving a stimulus file.  The types of the returned objects are `StimulusSet`, a subclass of a [pandas](https://pandas.pydata.org/) `DataFrame`, and `DataAssembly`, a subclass of an [xarray](https://xarray.pydata.org/) `DataArray`.  We use the functions `get_stimulus_set` and `get_assembly` and the `StimulusSet` method `get_stimulus`:

```pycon
>>> from brainio import get_assembly, get_stimulus_set
>>> hvm_stim = get_stimulus_set(identifier="dicarlo.hvm")
>>> hvm_stim
        id                             background_id         s  ... rxy_semantic ryz_semantic        rxz
0        1  ecd40f3f6d7a4d6d88134d648884e0b9b364efc9  1.000000  ...    90.000000    -0.000000   0.000000
1        2  006d66c207c6417574f62f0560c6b2b40a9ec5a1  1.000000  ...    -0.000000    -0.000000   0.000000
...
5758  5759  2363c8c3859603ee9db7f83dd7ba5b6989154258  0.791250  ...   -75.159000    12.283000  29.466000
5759  5760  a7fc954d2bd08fc2c4d3ade347f41a03a5850131  1.050000  ...   -67.467580     7.598457 -25.152591

[5760 rows x 18 columns]
>>> hvm_assy = get_assembly(identifier="dicarlo.MajajHong2015.public")
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

>>> hvm_stim.get_stimulus(stimulus_id="ecd40f3f6d7a4d6d88134d648884e0b9b364efc9")
"/Users/me/.brainio/stimulus_dicarlo_hvm/astra_rx+00.000_ry+00.000_rz+00.000_tx+00.000_ty+00.000_s+01.000_ecd40f3f6d7a4d6d88134d648884e0b9b364efc9_256x256.png"
```

### Opening Stimulus Sets And Data Assemblies From Files

If you have a CSV file describing a BrainIO Stimulus Set and a directory containing the associated stimulus files, 
you can load the `StimulusSet` into memory with `brainio.stimuli.StimulusSet.from_files()`.  
An example of using BrainIO in a Python interactive interpreter session to load a `StimulusSet`:
```pycon
>>> from brainio.stimuli import StimulusSet
>>> hvm_stim = StimulusSet.from_files(csv_path='hvm-public/hvm-public.csv', dir_path='hvm-public')
>>> hvm_stim
        id                             background_id  ...  ryz_semantic        rxz
0        1  ecd40f3f6d7a4d6d88134d648884e0b9b364efc9  ...     -0.000000   0.000000
1        2  006d66c207c6417574f62f0560c6b2b40a9ec5a1  ...     -0.000000   0.000000
2        3  3b3c1d65865028d0fad0b0bf8f305098db717e7f  ...     -0.000000   0.000000
3        4  687ade2f9ee4d52af9705865395471a24ba38d5f  ...     -0.000000   0.000000
4        5  724e5703cc42aa2c3ff135e3508038a90e4ebcb3  ...     -0.000000   0.000000
    ...                                       ...  ...           ...        ...
3195  3196  70222407751181c4b7723cb09dbda63e7f9c7333  ...     17.585453 -12.905496
3196  3197  f144e3aabccefb4228b8257506a2aa26ba5b4a6d  ...     22.244000  -6.302000
3197  3198  9b87c8be1440ce9626bcfe656700ff3ac8f909fe  ...      9.423000 -13.140000
3198  3199  c3edce2a8fce8c088605bd27fe1f2e7958939f54  ...     38.652000  11.926000
3199  3200  91e68c65ff92e5a77f0fb13693bfe01bc429da18  ...     16.609000 -36.603000
[3200 rows x 18 columns]
>>> hvm_stim.get_stimulus('8a72e2bfdb8c267b57232bf96f069374d5b21832')
'hvm-public/astra_rx+00.000_ry+00.000_rz+00.000_tx+00.000_ty+00.000_s+01.000_ecd40f3f6d7a4d6d88134d648884e0b9b364efc9_256x256.png'
```

If you have a netCDF file containing a BrainIO Data Assembly, you can open it with 
`brainio.assemblies.<DataAssembly subclass>.from_files()`.  
An example of using BrainIO in a Python interactive interpreter session to load a `DataAssembly`:

```pycon
>>> from brainio.assemblies import NeuronRecordingAssembly
>>> hvm_assy = NeuronRecordingAssembly.from_files(file_path='MajajHong2015_public.nc', stimulus_set_identifier='dicarlo.hvm.public', stimulus_set=hvm_stim)
>>> hvm_assy
<xarray.NeuronRecordingAssembly 'dicarlo.MajajHong2015.public' (neuroid: 256, presentation: 148480, time_bin: 1)>
array([[[ 0.06092933],
        [-0.8479065 ],
        [-1.618728  ],
        ...,
        [ 0.42337415],
        [ 0.0775381 ],
        [-0.614134  ]],
       [[ 0.30726328],
        [ 0.35321778],
        [ 0.10181567],
        ...,
        [-2.2552547 ],
        [ 1.0052351 ],
        [-0.2989609 ]]], dtype=float32)
Coordinates:
  * neuroid          (neuroid) MultiIndex
  - neuroid_id       (neuroid) object 'Chabo_L_M_5_9' ... 'Tito_L_M_8_0'
  - arr              (neuroid) object 'M' 'M' 'M' 'M' 'M' ... 'M' 'M' 'M' 'M'
  - col              (neuroid) int64 9 9 8 9 8 8 7 7 5 6 ... 1 0 1 0 1 0 0 1 1 0
  - hemisphere       (neuroid) object 'L' 'L' 'L' 'L' 'L' ... 'L' 'L' 'L' 'L'
  - subregion        (neuroid) object 'cIT' 'cIT' 'cIT' ... 'pIT' 'pIT' 'pIT'
  - animal           (neuroid) object 'Chabo' 'Chabo' 'Chabo' ... 'Tito' 'Tito'
  - y                (neuroid) float64 0.2 0.6 0.2 1.0 0.6 ... 1.0 1.0 1.8 1.4
  - x                (neuroid) float64 1.8 1.8 1.4 1.8 ... -1.8 -1.4 -1.4 -1.8
  - region           (neuroid) object 'IT' 'IT' 'IT' 'IT' ... 'IT' 'IT' 'IT'
  - row              (neuroid) int64 5 6 5 7 6 7 9 7 9 8 ... 4 4 5 5 6 6 7 7 9 8
  * presentation     (presentation) MultiIndex
  - stimulus_id         (presentation) object '8a72e2bfdb8c267b57232bf96f069374d...
  - repetition       (presentation) int64 0 18 18 18 18 18 ... 16 16 16 17 17 17
  - stimulus         (presentation) int64 0 426 427 428 429 ... 2569 2566 0 1 2
...
  - object_name      (presentation) object 'car_astra' 'face0' ... 'apple'
  - variation        (presentation) int64 0 0 0 0 0 0 0 0 0 ... 3 3 3 3 3 3 3 3
  - size             (presentation) float64 256.0 256.0 256.0 ... 256.0 256.0
  - rxy_semantic     (presentation) float64 90.0 -0.0 -0.0 ... 0.02724 -10.4
  - ryz_semantic     (presentation) float64 -0.0 -0.0 -0.0 ... -16.89 -0.2055
  - rxz              (presentation) float64 0.0 0.0 0.0 ... 13.22 -2.621 -14.72
  * time_bin         (time_bin) MultiIndex
  - time_bin_start   (time_bin) int64 70
  - time_bin_end     (time_bin) int64 170
Attributes:
    stimulus_set_identifier:  dicarlo.hvm.public
    stimulus_set:                     id                             backgrou...
```

You can also write a Data Assembly to a netCDF file with `brainio.packaging.write_netcdf()`.  
`write_netcdf` returns the new file's SHA-1 hash.  

```pycon
>>> from brainio.packaging import write_netcdf
>>> hvm_assy_new = hvm_assy.sel(subregion='aIT', object_name='apple')
>>> hvm_assy_new
<xarray.NeuronRecordingAssembly 'dicarlo.MajajHong2015.public' (neuroid: 17, presentation: 2320, time_bin: 1)>
array([[[-0.64983755],
        [-1.058876  ],
        [ 1.3953547 ],
        ...,
        [-0.21288353],
        [ 1.6455535 ],
        [ 3.1486752 ]],
       [[-0.5977455 ],
        [ 2.806696  ],
        [ 0.25336486],
        ...,
        [ 0.6877102 ],
        [ 0.683575  ],
        [ 2.6989598 ]]], dtype=float32)
Coordinates:
  * neuroid          (neuroid) MultiIndex
  - neuroid_id       (neuroid) object 'Chabo_L_A_8_8' ... 'Chabo_L_A_6_5'
  - arr              (neuroid) object 'A' 'A' 'A' 'A' 'A' ... 'A' 'A' 'A' 'A'
  - col              (neuroid) int64 8 8 6 7 5 7 7 6 6 5 6 5 5 5 6 5 5
  - hemisphere       (neuroid) object 'L' 'L' 'L' 'L' 'L' ... 'L' 'L' 'L' 'L'
  - animal           (neuroid) object 'Chabo' 'Chabo' ... 'Chabo' 'Chabo'
  - y                (neuroid) float64 1.4 1.8 0.6 1.4 1.0 ... -0.2 -0.2 0.2 0.6
  - x                (neuroid) float64 1.4 1.4 0.6 1.0 0.2 ... 0.2 0.6 0.2 0.2
  - region           (neuroid) object 'IT' 'IT' 'IT' 'IT' ... 'IT' 'IT' 'IT'
  - row              (neuroid) int64 8 9 6 8 7 9 7 9 7 9 8 8 3 4 4 5 6
  * presentation     (presentation) MultiIndex
  - stimulus_id         (presentation) object '5cde85cc63e677623c606ebf6d21a6b02...
  - repetition       (presentation) int64 18 18 18 18 19 19 ... 17 16 16 17 17
  - stimulus         (presentation) int64 431 310 344 530 60 ... 2551 2544 5 2
...
  - ryz_semantic     (presentation) float64 -0.0 -0.0 -0.0 ... 42.79 -0.2055
  - rxz              (presentation) float64 0.0 0.0 0.0 ... -23.87 -3.039 -14.72
  * time_bin         (time_bin) MultiIndex
  - time_bin_start   (time_bin) int64 70
  - time_bin_end     (time_bin) int64 170
Attributes:
    stimulus_set_identifier:  dicarlo.hvm.public
    stimulus_set:                     id                             backgrou...
>>> write_netcdf(assembly=hvm_assy_new, target_netcdf_file='hvm_aIT_apple.nc')
'7da262e1d35de5fc26bbbe9b10c481792cef1bde'
```

### Packaging And Cataloging Stimulus Sets And Data Assemblies In An Existing Catalog

To package Stimulus Sets and Data Assemblies and add them to a BrainIO Catalog, first install a project in editable mode as described above.  Make sure you have commit privileges on [GitHub](https://github.com/) for the repository you're editing.  Then (using the same [example project](https://github.com/dicarlolab/brainio-dicarlo) as above):  

1.  Activate your environment.
1.  `cd ~/projects/brainio-dicarlo`
1.  Create a new Git branch (the branch name doesn't really matter):  
`git branch dicarlo.Me2025.public`
1.  `git checkout dicarlo.Me2025.public`
1.  Write a script that packages your Stimulus Set and/or Data Assembly.  
We'll call our example `brainio-dicarlo/packaging/scripts/me2025.py`.
    * See the [documentation](docs/packaging.rst) for the packaging methods
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
from brainio.catalogs import Catalog

_logger = logging.getLogger(__name__)


def my_project():
    path = Path(__file__).parent / "lookup.csv"
    _logger.debug(f"Loading lookup from {path}")
    print(f"Loading lookup from {path}")
    catalog = Catalog.from_files("my_project", path)
    return catalog
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

If terminology is unclear, see the [Glossary](docs/glossary.md).  

If you have questions, [get in touch with us]("mailto:jjpr@mit.edu?subject=BrainIO question).

# License

[MIT License](LICENSE)


