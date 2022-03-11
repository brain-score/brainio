# BrainIO Format Specification

The BrainIO specification defines three types of entity:  
* a [Stimulus Set](#stimulus-set),
* a [Data Assembly](#data-assembly) and 
* a [BrainIO Catalog](#brainio-catalog).
## Stimulus Set
A **Stimulus Set** is a collection of files containing experimental stimuli presented to subjects or models and the metadata describing those stimuli.  
* A Stimulus Set must be associated with a **string identifier**.  The identifier must be unique among the Stimulus Sets in any BrainIO Catalog which contains it.  
* The files containing stimuli must be contained in a **ZIP archive**.
* The metadata must be contained in a **CSV file**.  
    * The CSV file must contain a **header row** providing a name for each column containing a metadata variable.  Column names may contain lowercase letters, numerals and underscores.  
    * Each row after the header row must contain the metadata describing **one stimulus**.  
    * It is not necessary that every file in the ZIP archive be included as a stimulus in the set.  
    * The CSV file must contain a column named **`image_id`**.  Each metadata row in the CSV must have an alphanumeric string which is unique within the Stimulus Set in the `image_id` column.  This string is the identifier for the stimulus which is described by the metadata in that row. 
    * The CSV file must contain a column named **`filename`**.  The `filename` value for each metadata row is the name of the file in the ZIP archive (or full file path if the ZIP archive is organized in directories) which corresponds to the stimulus described by that row.  
    * The CSV file may contain zero or more columns containing **metadata** values pertaining to the stimuli described.  
## Data Assembly
A **Data Assembly** is an n-dimensional array of data collected during an experiment, the metadata which provide meaning to those data and a reference to the Stimulus Set used in the experiment.  
* A Data Assembly must be associated with a **string identifier**.  The identifier must be unique among the Data Assemblies in any BrainIO Catalog which contains it.  
* The data and metadata must be contained in a **[netCDF-4](https://www.unidata.ucar.edu/software/netcdf/) file** (internally an [HDF5](https://www.hdfgroup.org/solutions/hdf5/) file).  
* Only one **netCDF Variable** in the file may contain experimental data.  All other Variables will be treated as metadata.  
* The netCDF file must have a global attribute named **`identifier`** which contains the Data Assembly's identifier
* The netCDF file must have a global attribute named **`stimulus_set_identifier`** which contains the identifier of the BrainIO Stimulus Set used in the experiment from which the data were collected.  
* The netCDF file must contain a dimension named **`presentation`** and a metadata Variable with that dimension named **`image_id`**.  
## BrainIO Catalog
A **BrainIO Catalog** is a list providing lookup information, including storage location, about Stimulus Sets and Data Assemblies.  
* A BrainIO Catalog must be associated with a **string identifier**.  It is preferred that the identifier be globally unique.  
* The lookup information must be contained in a **CSV file**.  
* The CSV file must contain a **header row** providing column names.  
* The **column names** must include the following:  
    * `identifier`:  Identifiers of Stimulus Sets and Data Assemblies.  
    * `lookup_type`:  One of either `stimulus_set` or `assembly`.
    * `class`:  To be used by software which uses a BrainIO Catalog to load Stimulus Sets and Data Assemblies into memory.  
    * `location_type`:  To be used by software which fetches files.  
    * `location`:  URLs for retrieving files.  
    * `sha1`:  The SHA-1 hashes of files.  
    * `stimulus_set_identifier`:  For Data Assemblies, the identifiers for the Stimulus Sets with which they are associated.  
* A Stimulus Set is represented in a BrainIO Catalog's CSV file by **two rows**, one describing its CSV file and one describing its ZIP archive.  
* A Data Assembly is represented in a BrainIO Catalog's CSV file by **one row** describing its netCDF file.  
