import intake,sys
import intake_esm
import pandas as pd

def main(catalog_path):
    cat = intake.open_esm_datastore(catalog_path)
    all_variables = set(cat.df['variable_id'])
    afiles = []
    dfiles = []

    for x in all_variables:
        d_df = cat.df[(cat.df['variable_id'] == x) & (cat.df['path'].str.contains("decp"))]
        a_df = cat.df[(cat.df['variable_id'] == x) & (cat.df['path'].str.contains("archive"))]
        if d_df.shape[0] > 0:
            dfiles.extend(d_df.path.to_list())
        else:
            afiles.extend(a_df.path.to_list())

    for i,x in enumerate(afiles):
        afiles[i] = x.replace("/archive/wfc/SPEAR/", "")
    for i,x in enumerate(dfiles):
        dfiles[i] = x.replace("/decp/SPEAR_MED/", "")

    pd.Series(afiles).to_csv("archive_files.txt", header=None, index=False)
    pd.Series(dfiles).to_csv("decp_files.txt", header=None, index=False)

if __name__ == "__main__":
    main(sys.argv[1])