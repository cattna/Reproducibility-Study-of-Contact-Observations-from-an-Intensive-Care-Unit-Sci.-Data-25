"""
This is a demonstration program showing how to work with the
contact interval files, and with datetime and timedelta objects.

The output shows that the number of badges observed in a night
shift is inflated because there is some small overlap of personnel
in going between day and night (or night and day) shifts. The
count of badges, for example, is smaller if we only look at
the middle 8 hours of a 12 hour shift.
"""

from datetime import datetime, timedelta
from collections import OrderedDict
import sys, os, lzma, json
from pprint import pprint

DATA_DIR = 'data'

def hcplist(contactintervalfile, centerhours=12):
    """
    Input:
        1. a compressed file of contact intervals
        2. a "center" portion size from a 12 hour shift
    Output:
        a dictionary of the form:
            R = {"nurse":{...},"provider":{...},"support":{...}}
        where R["nurse"] is the set of badges observed
        and R["dayofweek"] is a string for the day of the week
        when the shift started
    """

    # read the compressed file and reconstitute datetime objects
    with lzma.open(contactintervalfile, "r") as F:
        U = F.read().decode("utf-8")
    T = json.loads(U)
    K = [[item[0], item[1], eval(item[2]), item[3], item[4]] for item in T]

    # filter the shift by the "center" time window
    startofshift = min(e[2] for e in K)  # start of shift as a datetime object
    endofshift = max(e[2] for e in K)  # start of shift as a datetime object
    lengthofshift = round(
        (endofshift - startofshift).total_seconds() / (60 * 60)
    )  # difference in hours
    assert lengthofshift == 12  # all shifts are 12 hours long
    # make offset to "center" what we will look at
    #  -- this is mainly just a demonstration of how
    # Python's datetime arithmetic works
    offsethour = timedelta(hours=(lengthofshift - centerhours) // 2)
    start = startofshift + offsethour
    end = endofshift - offsethour
    J = [e for e in K if start <= e[2] <= end]

    # summarize badges observed and return as output
    R = {"nurse": set(), "provider": set(), "support": set()}
    for badge, other, timestamp, distance, duration in J:
        if badge.startswith("n"):
            R["nurse"] |= {badge}
        if badge.startswith("p"):
            R["provider"] |= {badge}
        if badge.startswith("s"):
            R["support"] |= {badge}
    daytable = "Mon Tue Wed Thu Fri Sat Sun".split()
    R["dayofweek"] = daytable[startofshift.weekday()]
    return R


# Unit test
if __name__ == "__main__":
    for i in range(1, 15):  # process shifts 1-14
        nightday = "day  " if i % 2 == 0 else "night"
        contactintervalfile = f"{DATA_DIR}/contact_intervals/intervals{i:02d}.json.xz"
        R = hcplist(contactintervalfile, centerhours=12)
        S = hcplist(contactintervalfile, centerhours=2)
        b = len(R["nurse"]) + len(R["provider"]) + len(R["support"])
        c = len(S["nurse"]) + len(S["provider"]) + len(S["support"])
        print(
            "HCP badge count shift",
            i,
            "(",
            R["dayofweek"],
            nightday,
            ")\t in full shift:",
            b,
            ", in middle 2 hours:",
            c,
        )
