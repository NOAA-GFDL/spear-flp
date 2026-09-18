import polars as pl 
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import numpy as np

catalog_gfdl = "catalog_blue.csv"
catalog_cmip = "catalog_cmip.csv"

allowed_keys = ["variable_id", "experiment_id", "time_range", "member_id"]

def string_to_list(x):
    return [y.strip() for y in x.strip('[] ').split(',')]

def convert_timerange(gfdl_timerange):
    times = gfdl_timerange.split('-')
    for i,t in enumerate(times):
        if len(t) == 4:
            times[i] = t + '0101'
        elif len(t) == 6:
            times[i] = t + '01'
        elif len(t) > 8:
            times[i] = t[:8] + 'T' + t[8:]
    return [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in times]

def test_timeranges(true_times, reported_times):
    truths = np.zeroes(len(true_times), dtype=bool)
    for i,tt in enumerate(true_times):
        for rt in reported_times:
            truths[i] |= (
                (rt[0] <= tt[0] < rt[1]) &
                (rt[0] < tt[1] < (rt[1] + relativedelta(years=1)))
            )
    return truths

def parse_body(input_string):
    var_dict = {}
    in_strings = [strip(x) for x in input_string.split('\n')][[2,6,10,14,18]]
    
    var_dict['variable_id'] = in_strings[0]
    var_dict['frequency'] = in_strings[1]

    if in_strings[2] != 'all':
        var_dict['experiment_id'] = in_strings[2]
    
    if in_strings[3] != "_No response_":
        var_dict['time_range'] = convert_timerange(in_strings[3])

    if in_strings[4] == 'Yes':
        pass_qc = True
    elif in_strings[4] == 'No':
        pass_qc = False
    
    return var_dict, pass_qc

def update_qc(df, var_dict, qc_status, qc_reporter):
    return df.with_columns(
        pass_qc = pl.when(**var_dict)
            .then(True)
            .otherwise(pl.col('pass_qc')),

        who_qc = pl.when(**var_dict)
            .then(qc_reporter)
            .otherwise(pl.col('who_qc'))
    )

def main(submitter, input_string):
    df_gfdl = pl.read_csv(catalog_gfdl)
    df_cmip = pl.read_csv(catalog_cmip)

    param_dict, pass_qc = parse_body(input_string)

    