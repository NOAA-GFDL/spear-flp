import intake,os,sys
import intake_esm
import pandas as pd

def search_to_subcat(output_dir, output_name, catalog, variables_df):
    empty_cat = catalog.search()
    empty_cat.serialize(directory=output_dir, name=output_name, catalog_type="file")
    dfs = []
    for index,row in variables_df.iterrows():
        dfs.append(catalog.search(realm=row['realm'], 
                   variable_id=row['variable_id'],
                   frequency=row['frequency'],
                   chunk_freq=row['chunk_freq']).df)

    concat_df = pd.concat(dfs, ignore_index=True)
    concat_df.to_csv(output_dir+output_name+".csv", header=False, index=None, mode='a')
    return

def main(catalog_path, variable_df, output_name):
    var_df = pd.read_csv(variable_df)

    cat_url = catalog_path
    cat = intake.open_esm_datastore(cat_url)

    directory = os.path.dirname(catalog_path)+"/"

    search_to_subcat(directory, output_name, cat, var_df)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])