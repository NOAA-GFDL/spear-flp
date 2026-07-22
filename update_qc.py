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