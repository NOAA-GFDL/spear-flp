
SPEAR (Seamless System for Prediction and EArth System Research) is a next generation modeling system for seasonal to decadal prediction and projection developed at the Geophysical Fluid Dynamics Laboratory (GFDL). It is built from component models developed at GFDL—the AM4 atmosphere model, MOM6 ocean code, LM4 land model, and SIS2 sea ice model. The SPEAR models are specifically designed with attributes needed for a prediction model for seasonal to decadal time scales, including the ability to run large ensembles of simulations with available computational resources.

The Seasonal-to-Decadal Division at GFDL has conducted 30-member ensembles of climate change simulations over the period 1921-2100 using the SPEAR_MED climate model ([Delworth et al., 2020](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2019MS001895)). Selected output from these model runs is available as described below. This model has a 50 km atmosphere/land horizontal resolution and an approximate 1° horizontal resolution for the ocean and sea ice components. Simulations extend from calendar year 1921 to 2100, and are forced with historical radiative forcings over the period 1921-2014, and the SSP5-8.5 projected radiative forcings ([O’Neill et al., 2016](https://gmd.copernicus.org/articles/9/3461/2016/); [van Vuuren et al., 2013](https://rd.springer.com/article/10.1007/s10584-013-0906-1)) for 2015-2100. For further details on the design and simulation aspects of the ensembles see sections 2.4.3 and 3.4 of [Delworth et al., 2020](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2019MS001895). 

## Data Characteristics

### Data Variables

Note that variable names correspond to [CMIP6 conventions](https://pcmdi.llnl.gov/CMIP6/). Some atmospheric variables are available at 17 pressure levels in the monthly frequency, denoted with \*.

- **Temperature**: Air Temperature (`ta`\* and `tas`), Daily Minimum and Maximum Near-Surface Air Temperature (`tasmin`, `tasmax`), and Sea Surface Temperature (`sst`)
- **Pressure**: Sea Level Pressure (`psl`)
- **Wind**: zonal and meridional components (`ua`\*, `uas` and `va`\*, `vas` respectively), surface wind speed (`sfcWind`)
- **Radiation**: Outgoing Longwave and Shortwave Radiation (`rlut`, `rsut`), Incident Shortwave Radiation (`rsdt`)
- Precipitation (`pr`)
- Specific Humidity (`hus`)\*
- **Grid Parameters**: Atmospheric and ocean grid cell areas (`areacella` and `areacello`, respectively)

### Organization, Optimization, and Chunking

<!-- What choices were made about how to organize, optimize, and chunk the data variables? Which query patterns work best with this data? Which query patterns work less well? -->

The dataset is organized by `experiment_id`, `member_id`, and `table_id`. The simulation was run 30 times and data was saved for each realization, which correspond to the `pp_ens_XX` directories. The data is chunked for each time step.

Available `experiment_id`:
- `historical` : Historical radiative forcings over the period 1921-2014
- `scenarioSSP5-85` : SSP5-8.5 projected radiative forcings ([O’Neill et al., 2016](https://gmd.copernicus.org/articles/9/3461/2016/); [van Vuuren et al., 2013](https://rd.springer.com/article/10.1007/s10584-013-0906-1)) for 2015-2100

Available `table_id`:
- `6hr` : atmospheric data saved every 6 hours
- `day` : atmospheric data saved daily
- `Amon` : atmospheric data saved monthly
- `Omon` : ocean data saved monthly
- `fx` : contains the grid cell area `areacella` for the atmos realm
- `Ofx` : contains the grid cell area `areacello` for the ocean realm

### Coordinates

<!-- What are the coordinates of this dataset? Describe the temporal sampling resolution and spatial grid in human-readable terms. Enumerate any other dimensions or coordinates that exist in the dataset? -->

The physical coordinates are `time`, latitude (`lat`), and longitude (`lon`). Data for the period 1921-2014 is in the “historical” directory, and data for 2015-2100 is in the “scenarioSSP5-85” directory. Temporal resolution varies based on `table_id`. This model has a 50 km atmosphere/land horizontal resolution and an approximate 1° horizontal resolution for the ocean and sea ice components.

### Update Frequency and Latency

<!--  How and when is this dataset updated? (E.g. monthly, daily.) For forecast products, describe the anticipated latency between forecast time and data publication. If the dataset is static in nature (no updates other than errata), note that here. -->

This dataset is being updated as additional relevant variables are cleared for public release.

## Provenance and Processing

### Inputs

<!-- What other data sources were used to generate this dataset? This is the place to provide appropriate attribution and citation if your dataset is a derived work. -->

This dataset contains model output from the coupled global climate model SPEAR, developed at GFDL. For more information on the model designs, see [Delworth et al., 2020](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2019MS001895).

### Processing

<!--  How is your dataset produced? Describe the processing chain that is used to generate this dataset. Reveal as much or as little as you think is necessary to help your users understand the dataset. If your processing code is open source, link to it here. -->

The simulations were performed on the GAEA supercomputer at Oak Ridge National Laboratory (ORNL), Oak Ridge, TN. Raw model output was post-processed at NOAA GFDL using the FMS Runtime Environment (FRE).

### Citation

When using this data please acknowledge as downloaded from GFDL, with a publication reference to ‘SPEAR: The Next Generation GFDL Modeling System for Seasonal to Multidecadal Prediction and Projection’, Delworth et al. (2020), Journal of Advances in Modeling Earth Systems, 12, e2019MS001895, https://doi.org/10.1029/2019MS001895.

### External Links

<!-- Provide any external links which can help understand your dataset better. Examples include a publication that describes the method or a use of the dataset, or the "Algorithm Theoretical Basis Document" (ATBD) for satellite datasets. -->

Directly download the netCDF files:
- [NOAA NODD cloud-hosted data](https://noaa-gfdl-spear-large-ensembles-pds.s3.amazonaws.com/index.html#SPEAR/GFDL-LARGE-ENSEMBLES/CMIP/NOAA-GFDL/GFDL-SPEAR-MED/)
- [Globus](https://app.globus.org/file-manager?origin_id=5ac03700-685a-4845-ab82-4a5771b58426&origin_path=%2F2%2FGFDL-LARGE-ENSEMBLES%2FCMIP%2FNOAA-GFDL%2FGFDL-SPEAR-MED%2F)

Further information about this data release can be found [here](https://www.gfdl.noaa.gov/spear_large_ensembles/), and further information about the SPEAR model in general can be found [here](https://www.gfdl.noaa.gov/spear/).

Relevant references:

Delworth, T. L., Cooke, W. F., Adcroft, A., Bushuk, M., Chen, J.-H., Dunne, K. A., et al. (2020). SPEAR: The Next Generation GFDL Modeling System for Seasonal to Multidecadal Prediction and Projection. Journal of Advances in Modeling Earth Systems, 12(3), e2019MS001895. https://doi.org/10.1029/2019MS001895

O’Neill, B. C., Tebaldi, C., van Vuuren, D. P., Eyring, V., Friedlingstein, P., Hurtt, G., et al. (2016). The Scenario Model Intercomparison Project (ScenarioMIP) for CMIP6. Geoscientific Model Development, 9(9), 3461–3482. https://doi.org/10.5194/gmd-9-3461-2016

van Vuuren, D. P., Kriegler, E., O’Neill, B. C., Ebi, K. L., Riahi, K., Carter, T. R., et al. (2014). A new scenario framework for Climate Change Research: scenario matrix architecture. Climatic Change, 122(3), 373–386. https://doi.org/10.1007/s10584-013-0906-1