import sys
import os
import lzma
import json
import numpy as np
from datetime import datetime, timedelta
from collections import OrderedDict
from pprint import pprint
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy import stats
import extractspread
import gc
DATA_DIR = 'data'
SUPP_DIR = 'supp'
FIG_DIR = 'figures'
# table of anchors that are in patient rooms
# maps badge -> (roomnumber,role) where role is one of "door",
#               "computer", "vitals", "sink"
AnchorTable = extractspread.getAnchors(SUPP_DIR)

careabout = "n pr ss vitals sink computer door anchor unknown".split()


def wornbadges(T):
    # make a set of all badges found in T
    S = set([])
    for moment in T:
        for badge in T[moment]:
            S.add(badge)
    return S


def hcwcount(T, tenminbucket, shift):
    hcwids = set()
    old = None
    for moment in T:  # moment is a one-second sample
        hour = moment.hour
        minuteslot = int(str(moment.minute)[0])
        tenminslot = 6*hour + minuteslot  # 240 slots in a day
        if old != tenminslot:
            # print("shift",shift,"bucket change",tenminslot)
            if old != None:
                tenminbucket[(shift, old)] = len(hcwids)
            hcwids = set()  # clear out old dict
            old = tenminslot
        for badge in T[moment]:
            if len(T[moment][badge]["contacts"]) > 0:
                hcwids.add(badge)
    # remember to record last bucket in shift
    if hcwids:
        tenminbucket[(shift, old)] = len(hcwids)
    return


def plotbybucket(shiftcount):
    # shiftcount is a dictionary  (shift,tenminslot) -> count
    count = dict()
    for shift, tenminslot in shiftcount:
        count[tenminslot] = shiftcount[(
            shift, tenminslot)] + count.get(tenminslot, 0)
    # from total to mean
    meancount = {h: count[h]/14.0 for h in count}
    print("periods for mean", list(sorted(meancount.keys())))
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_ylabel('mean number of badges', loc="center", fontsize=10)
    ax.set_xlabel('ten-minute period in day [0-147]')
    ax.set_xlim(0, 148)  # 148 = 24 * 6 because six ten-minute periods per hour
    x = list(range(7*6))  # 42 = six periods per hour, up to 7am.
    y = [meancount[h] for h in x]
    ax.plot(x, y, 's', color='b')
    x = list(range(19*6, 148))  # from 7pm to midnite
    y = [meancount[h] for h in x]
    ax.plot(x, y, 's', color='b')
    # plt.savefig("dayniteTen.png")
    x = list(range(7*6, 19*6))  # from 7am to 7pm
    y = [meancount[h] for h in x]
    ax.plot(x, y, 'o', color='c')
    savepath = f"{FIG_DIR}/dayniteTen.png"
    plt.savefig(savepath, dpi=300)
    print(f"Saved plot to {savepath}")


def make_shift(shift):
    # change fname as needed depending on your directory structure
    fname = "histories{0:02d}.json".format(shift)
    with lzma.open(f"{DATA_DIR}/histories/{fname}.xz", mode='rb') as F:
        T = json.load(F)
        K = [(eval(i.replace("datetime.datetime", "datetime")), j)
             for i, j in T.items()]
        T = OrderedDict(sorted(K))
    return T


if __name__ == "__main__":
    contactotals = dict()
    for i in range(1, 15):  # shift 1 through shift 14
        M = make_shift(i)
        print("got shift", i)
        # for each contact, for each second, add to hour bucket
        contactsummary = dict()
        hcwcount(M, contactsummary, i)
        contactotals.update(contactsummary)  # should not be conflict
        del M

    plotbybucket(contactotals)
