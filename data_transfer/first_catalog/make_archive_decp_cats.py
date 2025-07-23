import sys,os,math
import intake
import intake_esm
import pandas as pd

def combine_cats(directory, output_name):
    files = os.listdir(directory)
    dfs = []
    for x in files:
        if x.endswith('.json'):
            cat1 = intake.open_esm_datastore(directory+x)
            empty_cat = cat1.search()
            empty_cat.serialize(directory=directory, name=output_name, catalog_type="file")
            break
    for x in files:
        if x.endswith('.csv'):
            df1 = pd.read_csv(directory+x)
            df1 = df1[(df1['frequency'] != 'fx') & (df1['cell_methods'] == 'ts')]
            dfs.append(df1.copy(deep=True))
    concat_df = pd.concat(dfs, ignore_index=True)
    concat_df.to_csv(directory+output_name+".csv", header=False, index=None, mode='a')
    return

def main(directory):

    if not(os.path.isdir(directory)):
        os.system('mkdir {}'.format(directory))
    if not(os.path.isdir(directory+"/decp")):
        os.system('mkdir {}'.format(directory+"/decp"))
    if not(os.path.isdir(directory+"/archive")):
        os.system('mkdir {}'.format(directory+"/archive"))

    # load fre for catalog builder
    os.system('module load fre/2025.03')

    # make a catalog for each ensemble member, the folder numbering is weird
    # for i in range(1,31):
    # # for i in range(1,2):
    #     n = 3*math.floor((i-1)/3)
    #     n1 = str(n+1).zfill(2)
    #     n2 = str(n+3).zfill(2)
    #     ix = str((i-1)%3 + 1).zfill(2)
    #     iz = str(i).zfill(2)
    #     path1 = "/archive/wfc/SPEAR/SPEAR_c192_o1_Hist_AllForc_IC1921_K50_ens_{}_{}/pp_ens_{}".format(n1,n2,ix)
    #     path2 = "/archive/wfc/SPEAR/SPEAR_c192_o1_Scen_SSP585_IC2011_K50_ens_{}_{}/pp_ens_{}".format(n1,n2,ix)
    #     output1 = directory+"/archive/archive_hist_{}".format(iz)
    #     output2 = directory+"/archive/archive_scen_{}".format(iz)
    #     # print("{}_{}/{}".format(n1,n2,ix))
    #     os.system('fre catalog builder --overwrite {} {}'.format(path1,output1))
    #     os.system('fre catalog builder --overwrite {} {}'.format(path2,output2))
    
    # make the catalogs for the files on decp
    path1_decp = "/decp/SPEAR_MED/SPEAR_c192_o1_Hist_AllForc_IC1921_K50/"
    path2_decp = "/decp/SPEAR_MED/SPEAR_c192_o1_Scen_SSP585_IC2011_K50/"
    out1_decp = directory+"/decp/decp_hist"
    out2_decp = directory+"/decp/decp_SSP585"

    os.system('fre catalog builder --overwrite {} {}'.format(path1_decp,out1_decp))
    os.system('fre catalog builder --overwrite {} {}'.format(path2_decp,out2_decp))

    # combine all the cats

    # combine_cats(directory+"/archive/", "catalog_full")
    combine_cats(directory+"/decp/", "catalog_decp")

    # remove the individual catalogs
    for i in range(1,31):
        n = 3*math.floor((i-1)/3)
        n1 = str(n+1).zfill(2)
        n2 = str(n+3).zfill(2)
        ix = str((i-1)%3 + 1).zfill(2)
        iz = str(i).zfill(2)
        path1 = "/archive/wfc/SPEAR/SPEAR_c192_o1_Hist_AllForc_IC1921_K50_ens_{}_{}/pp_ens_{}".format(n1,n2,ix)
        path2 = "/archive/wfc/SPEAR/SPEAR_c192_o1_Scen_SSP585_IC2011_K50_ens_{}_{}/pp_ens_{}".format(n1,n2,ix)
        output1 = directory+"/archive/archive_hist_{}".format(iz)
        output2 = directory+"/archive/archive_scen_{}".format(iz)
        # print("{}_{}/{}".format(n1,n2,ix))
        os.system('rm {}.*'.format(output1))
        os.system('rm {}.*'.format(output2))
    os.system('rm {}.*'.format(out1_decp))
    os.system('rm {}.*'.format(out2_decp))

if __name__ == "__main__":
    main(sys.argv[1])