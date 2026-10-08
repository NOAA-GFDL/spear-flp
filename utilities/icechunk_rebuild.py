import warnings
warnings.filterwarnings(
  "ignore",
  message="Numcodecs codecs are not in the Zarr version 3 specification*",
  category=UserWarning
)

import time
import xarray as xr
import zarr
from obstore.store import from_url
from virtualizarr import open_virtual_dataset, open_virtual_mfdataset
from virtualizarr.parsers import HDFParser, NetCDF3Parser
from virtualizarr.registry import ObjectStoreRegistry
import icechunk
import arraylake as al

def preprocess(ds:xr.Dataset, table_id) -> xr.Dataset:
    if 'fx' in table_id:
        ds = ds.set_coords(['lon_bnds', 'lat_bnds'])
    else:
        ds = ds.set_coords(['time_bnds', 'lon_bnds', 'lat_bnds'])
    # elevate the experiment id to a dimension so that 
    # ..._mfdataset automatically concats along that dimension
    if ds.frequency == '6hr':
        variant_id = ds.attrs['parent_variant_label']
    else:
        variant_id = ds.attrs['parent_experiment_rip']
    experiment_id = ds.attrs['experiment_id']
    ds = ds.assign_coords(member_id=[variant_id], experiment_id=[experiment_id])
    return ds

class SPEAR2IC:
    def __init__(self, bucket_url: str, ic_repo, parser=HDFParser()):
        self.s3_store = from_url(bucket_url, region="us-east-1", skip_signature=True)
        self.registry = ObjectStoreRegistry({bucket_url: self.s3_store})
        self.parser = parser
        self.repo = ic_repo # doesn't have to be arraylake storage! the icechunk
        # can also be stored locally, see https://icechunk.io/en/stable/storage/
    
    def group_exists(self, experiment_id, table_id, branch='main'):
        # checks if group already exists
        session = self.repo.readonly_session(branch)
        root = zarr.open_group(session.store, zarr_format=3, mode='r')
        return f'{experiment_id}/{table_id}' in root
    
    def find_urls(self, experiment_id, table_id):
        # filters the desired datasets by experiment_id, table_id
        urls = []
        stream = self.s3_store.list(
            prefix=f'SPEAR/GFDL-LARGE-ENSEMBLES/CMIP/NOAA-GFDL/GFDL-SPEAR-MED/{experiment_id}'
        )
        for batch in stream:
            for b in batch:
                path = b['path']
                if ('/'+table_id) in path and path.endswith('.nc'):
                    urls.append(path)

        return [bucket+'/'+u for u in urls]
    
    def get_vds(self, experiment_id, table_id):
        urls = self.find_urls(experiment_id, table_id)

        # fx and Ofx don't have time axes, so we can't load them with virtual zarr
        if table_id == 'fx':
            parse=self.parser
            loadables = ['lon_bnds', 'lat_bnds', 'lat', 'lon', 'bnds', 'experiment_id', 'member_id']
        elif table_id == 'Ofx':
            loadables = ['lon_bnds', 'lat_bnds', 'lat', 'lon', 'bnds', 'experiment_id', 'member_id']
            parse=NetCDF3Parser() # the Ofx datasets are stored in netCDF3 still
        else:
            loadables=['time_bnds', 'lon_bnds', 'lat_bnds', 'lat', 'lon', 'bnds', 'plev', 'time', 'experiment_id', 'member_id']
            parse=self.parser
        
        # this is the line that opens all the files and combines them into a
        # virtual dataset:
        vds = open_virtual_mfdataset(
            urls,
            parallel='lithops',
            preprocess=lambda x : preprocess(x, table_id),
            registry=self.registry, 
            parser=parse,
            # the coordinates need to be in memory for xarrays comparison logic to work. 
            loadable_variables=loadables,
            compat='override',
            join='override',
            coords='minimal',
            combine_attrs='drop_conflicts'
        )

        return vds
    
    def commit_group(self, vds, groupname, branch="main", message=None):
        # the virtual dataset is commited to the icechunk as a zarr group
        if message is None:
            message = f"Adding group {groupname}"
        with self.repo.transaction(branch, message=message) as store:
            vds.vz.to_icechunk(store, group=groupname)
        return

    def replace_group(self, vds, groupname, branch="main", message=None):
        # the virtual dataset is commited to the icechunk as a zarr group
        if message is None:
            message = f"Replacing group {groupname}"
        with self.repo.transaction(branch, message=message) as store:
            root = zarr.open_group(store, zarr_format=3, mode='r+')
            del root[groupname]
            vds.vz.to_icechunk(store, group=groupname)
        return

def __main__(arraylake_repo, s3_bucket):
    client = al.Client()
    repo = client.get_or_create_repo(arraylake_repo)

    spear2ic = SPEAR2IC(bucket, repo)

    for exp_id in ['historical', 'scenarioSSP5-85']:
        for tab_id in ['fx', 'Ofx', 'Amon', 'Omon', '6hr', 'day']:
            if spear2ic.group_exists(exp_id, tab_id):
                print(f"Group {exp_id}/{tab_id} already exists, replacing...")
                t = time.time()
                vds = spear2ic.get_vds(exp_id, tab_id)
                spear2ic.replace_group(vds, f"{exp_id}/{tab_id}")
                print(f"{time.time() - t} seconds to open and replace {exp_id}/{tab_id}.")
            else:
                t = time.time()
                vds = spear2ic.get_vds(exp_id, tab_id)
                spear2ic.commit_group(vds, f"{exp_id}/{tab_id}")
                print(f"{time.time() - t} seconds to open and commit {exp_id}/{tab_id}.")

if __name__=="__main__":
    main(
        "GFDL/noaa-gfdl-spear-large-ensembles-pds",
        "s3://noaa-gfdl-spear-large-ensembles-pds"
    )