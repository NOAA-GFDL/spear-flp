# [Click here to make a QC report](https://github.com/NOAA-GFDL/spear-flp/issues/new?template=qc_update.yml)

Or, go to "Issues", press the "New issue" button in the top right, and then choose "QC Update". The form will ask a few questions. This helps us record the status of the QC, and initiate next steps.

For time range, you can leave blank to select all time ranges for the given variable and experiment. Otherwise, you can pass multiple by putting commas between them, e.g.,
```
20410101-20501231, 20110101-20201231, 20510101-20601231, 20310101-20401231
```
Please make sure all 30 ensemble members pass before reporting.

# (Recommended) Accessing the data:

The data is available on a Globus endpoint [at this link](https://app.globus.org/file-manager?origin_id=20987ccd-15d0-4719-a60c-86ab17d6a393&origin_path=%2F). We recommend using Globus CLI to download the data to your local machine, as it can offer the ability to download only the files of interest with a batch transfer. You will need Globus running on your machine ([Globus Connect Personal](https://www.globus.org/globus-connect-personal), usually) and the [Globus CLI](https://docs.globus.org/cli/) to follow these steps.

1. Follow the instructions to set up [Globus Connect Personal](https://www.globus.org/globus-connect-personal) if you don't already have a Globus endpoint on the machine you wish to transfer the files to.

2. Install [Globus CLI](https://docs.globus.org/cli/). Make sure to log in by running the following in your terminal:
```
$ globus login
```

3. Create a text file that lists the paths to the datasets that you're interested in by using the [search_catalog.ipynb](https://github.com/NOAA-GFDL/spear-flp/blob/main/examples/search_catalog.ipynb) example notebook.

4. In your terminal, run the following:
```
# this is the UUID for the source collection:
$ SPEAR_FLP_RESTRICTED="20987ccd-15d0-4719-a60c-86ab17d6a393"

# replace with the path to the directory you want the data saved:
# if you're not using Globus connect personal, replace
# $(globus endpoint local-id) with the UUID of the collection
# you wish to use.
$ GLOBUS_DEST="$(globus endpoint local-id):/path/to/directory/"

# Run the transfer in batch mode:
$ cat /path/to/my_files.txt | globus transfer $SPEAR_FLP_RESTRICTED $GLOBUS_DEST --batch -
```
