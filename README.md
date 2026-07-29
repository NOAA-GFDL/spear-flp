# [Click here to make a QC report](https://github.com/NOAA-GFDL/spear-flp/issues/new?template=qc_update.yml)

Or, go to "Issues", press the "New issue" button in the top right, and then choose "QC Update". The form will ask a few questions. This helps us record the status of the QC, and initiate next steps.

For time range, you can leave blank to select all time ranges for the given variable and experiment. Otherwise, you can pass multiple by putting commas between them, e.g.,
```
20410101-20501231, 20110101-20201231, 20510101-20601231, 20310101-20401231
```
Please make sure all 30 ensemble members pass before reporting.

Please include in the details additional information on how the dataset was checked. The expectation is to not provide detailed comments, but brief enough to touch on one of the below rubrics. As an example,
> Used in tropical cyclone genesis analysis; output successfully integrated into workflow. This checked for utility and data readability within the scope of our application.

# Quality Control Rubric

| Rubric | Details | Example |
| --- | --- | ---|
| **Data Completeness** | No unexpected missing values | No unexpected NaNs; all expected years/months/variables are present. |
| **Data integrity** | The data in post-processed output files are the same as the data in input files. | This is relevant for the data production teams. No data transfer errors, checksums or summary statistics match. |
| **Dataset-readability** | Data is not corrupted | NetCDF file(s) opens successfully |
| **Range and Boundary validation** | Data is accurate, summary statistics verified (Variables, units, value ranges, and summary statistics are verified, with no obvious processing errors.) | Surface temperature ranges from ~180–330 K and units are correctly specified as K; precipitation values are non-negative; monthly means are within expected bounds. |
| **Metadata Consistency & Documentation** | Adequate metadata in the NetCDF header (time:units, descriptive name, etc) for all time chunks, README with available data and directory structure explained. | Variable names and units are documented; any incorrect or missing information is noted and reported. |
| **Spatial and Temporal Consistency** | Expected spatial and temporal coverage, consistent time intervals | Global coverage spans 1921–2100; monthly data contain no missing months or duplicated timestamps. |
| **Utility**\* | Relevance and utility in your application (e.g. used in studying “X”, or link to research/github code) | Used for tropical cyclone genesis analysis; output successfully integrated into workflow. |
| **Scientific Plausibility**\*\* | Fields are physically reasonable. No obvious unrealistic artifacts or biases. Consistent with expected climatology and/or observations, where applicable. | Examples of potential issues: artificial spatial patterns in the fields, dried-up Great Lakes, or unrealistic precipitation or temperature patterns. |

\*_Required minimum contribution for task force participants; additional QA checks are encouraged_

\*\*_Optional, but please report any issues identified_

# (Recommended) Accessing the data:

The data is available on a Globus endpoint [at this link](https://app.globus.org/file-manager/collections/411dc91a-a5ae-43bd-ae12-d9225fee0ef7). We recommend using Globus CLI to download the data to your local machine, as it can offer the ability to download only the files of interest with a batch transfer. You will need Globus running on your machine ([Globus Connect Personal](https://www.globus.org/globus-connect-personal), usually) and the [Globus CLI](https://docs.globus.org/cli/) to follow these steps.

1. Follow the instructions to set up [Globus Connect Personal](https://www.globus.org/globus-connect-personal) if you don't already have a Globus endpoint on the machine you wish to transfer the files to.

2. Install [Globus CLI](https://docs.globus.org/cli/). Make sure to log in by running the following in your terminal:
```
$ globus login
```

3. Create a text file that lists the paths to the datasets that you're interested in by using the [search_catalog.ipynb](https://github.com/NOAA-GFDL/spear-flp/blob/main/examples/search_catalog.ipynb) example notebook. The file should be formatted as:
```
</path/to/source_file_1> </path/to/destination_file_1>
</path/to/source_file_2> </path/to/destination_file_2>
...
```

5. In your terminal, run the following:
```
# this is the UUID for the source collection:
$ SPEAR_FLP_RESTRICTED="411dc91a-a5ae-43bd-ae12-d9225fee0ef7"

# replace with the path to the directory you want the data saved:
# if you're not using Globus connect personal, replace
# $(globus endpoint local-id) with the UUID of the collection
# you wish to use.
$ GLOBUS_DEST="$(globus endpoint local-id):/path/to/directory/"

# Run the transfer in batch mode:
$ cat /path/to/my_files.txt | globus transfer $SPEAR_FLP_RESTRICTED $GLOBUS_DEST --batch -
```
