from datetime import datetime, timedelta
import sys, os, lzma, json, copy
from collections import OrderedDict
DATA_DIR = 'data'

"""
    Goal of this module is to convert raw badge data from the Instant-Trace 
    API call into contact intervals. This is rather simple from fulldata.xz 
    by these steps, repeated for each shift:
        1. convert character datetime to Python's datetime type
        2. filter through the raw data to extract only datetimes within 
             the specified shift
        3. eliminate any raw data that is a mutual anchor detected contact; any 
             such data is a bug during deployment (allowing anchors to be too close)
        4. sort by datetime and remove any duplicate records  
        5. create a new, empty ordered dictionary G for contact intervals 
        6. for each time T, copy records into G subject to:
             a. make one contact interval for matching start/end records
             b. for records with only start and no end, create a 
                    contact interval of just 10 seconds
             c. enforce symmetry for contact intervals by 
                    duplication with badge order reversed
        7. create a new ordered dictionary R from G which merges overlapping
             intervals (can come about because of symmetry forcing and imprecise
             badge clocks, so the same interval recorded by one badge differs 
             by a few seconds from the other)
        8. convert R to output, writing contact intervals to a file

    Input File: (adjust location above if needed) 
        fulldata.xz, which after decompression consists of a list
        of items, taken directly from instant-trace API calls, of 
        the form:
         (badge,otherbadge,datetime,distance,duration)
        where "interval" duration is a multiple of 15 (max 600) 
        distance in inches (but threshold by dashboard is 72 inches)
        datetime in UTC, with offset 5 hours (during daylight savings)
"""


def clean(Slot):
    """
    Slot is a list of tuples, all with the same datetime; some
    things in Slot should be removed -- such as tuples representing
    a start-of-contact where an end-of-contact is present in Slot.
    After removing all of these, still some start-of-contact might
    remain, but these are forced to have 10 second duration instead
    because Instant-Trace considered them to be fleeting contacts,
    but we know this is valuable information
    """
    newSlot = list()
    for item in Slot:
        badge, otherbadge, T, distance, duration = item
        if distance < 12:  # less than 12 inches is likely a
            # deployment error (handing out or collecting badges)
            continue
        similars = [e for e in Slot if e[0] == badge and e[1] == otherbadge]
        assert all(e[2] == T for e in similars)  # redundant; paranoid
        # this next test isolates end-of-contact record and skips over it
        if duration == 0 and any(e[4] != 0 for e in similars):
            continue  # skip
        else:
            newSlot.append(item)
    # now newSlot has only end-of-contact or orphan start-of-contact records
    for item in newSlot:
        badge, otherbadge, T, distance, duration = item
        if duration == 0:
            item[4] = 10  # force 10 second contact interval
    # theoretically, there might be duplicates?
    dedup = list()
    for item in newSlot:
        if item not in dedup:
            dedup.append(item)
    Slot[:] = list(sorted(dedup))  # we mutate original list


def enforceSymmetry(Slot):
    """
    Slot is a list of tuples, all with the same datetime;
    the goal here is just to ensure that each tuple is
    represented in both (badge,otherbadge) and (otherbadge,badge)
    order -- done by brute force

    Note: also eliminate any duplicates, which could be result
    of enforcing symmetry
    """
    newSlot, pairs = list(), set()
    for item in Slot:
        badge, otherbadge, T, distance, duration = item
        newSlot.append(item)
        newSlot.append([otherbadge, badge, T, distance, duration])
        pairs.add((badge, otherbadge))
    # highest duration for any pair
    for a, b in pairs:
        trim = [item for item in newSlot if item[0] == a and item[1] == b]
        if len(trim) < 2:
            continue  # no duplicate for (a,b)
        maxdur = max(item[4] for item in trim)
        # mangle any item for (a,b) which does not have max duration
        for item in newSlot:
            if item[0] != a or item[1] != b or item[4] != maxdur:
                continue
            item[0] = 0  # mangle as a flag to destroy later
        # remove mangled items
        newSlot = [item for item in newSlot if item[0] != 0]
    # deduplicate newSlot
    dedup = sorted(set([tuple(item) for item in newSlot]))  # sort needs tuples
    dedup = [list(item) for item in dedup]  # convert back to list type
    Slot[:] = dedup  # mutate original list


def intervalMerge(intvl, Slot):
    """
    intvl is a contact interval (has duration), Slot
    is some list of intervals which start after intvl.
    This function looks for an overlapping interval
    within Slot and attempts to merge with that
    """
    badge, otherbadge, T, distance, duration = intvl
    EndT = T + timedelta(seconds=duration)  # to detect overlap
    SlotRevised = False  # flag will become True if change needed
    for prospect in Slot:
        if intvl is prospect:
            continue  # leave self alone!
        if badge != prospect[0] or otherbadge != prospect[1] or EndT < prospect[2]:
            continue
        # prospect does overlap - remove it from Slot, but
        # only after adjusting EndT if appropriate
        otherEndT = prospect[2] + timedelta(seconds=prospect[4])
        if otherEndT > EndT:  # we can absorb the excess
            excess = int((otherEndT - T).total_seconds())
            intvl[4] = excess
            prospect[0], SlotRevised = 0, True  # invalidate other interval
    if SlotRevised:  # only needed rarely
        Slot[:] = [e for e in Slot if e[0] != 0]


def makecontactintervals(Raw, Shift=None, filename=None):
    """
    Input:
        Raw is the full list of tuples from fulldata.xz, modified
        only by type conversion of datetime fields
        Shift is a number in range(1,15) specifying the shift
        number; odd shift numbers are evenings; the first shift
        is April 18th.
        filename is where to store the output json
    Output:
        an ordered dictionary mapping datetime to a contact interval;
        all contact intervals from the specified shift are included
    Each item of Raw is a list of the form:
     [ "n043", "pr017", "datetime(2023, 4, 19, 0, 2, 27)", 62, 15 ]
    that is, badge, otherbadge, datetime, distance, duration

    IMPORTANT NOTES: Shift 0 was for the walk-through validation only
                                     Shift 1 data is incomplete because we did not
                                         distribute badges at the start of the night
                                         shift (7pm); they were handed out later.
                                     Shift 15 is not valid because we were removing
                                         anchors during that time.
    """
    ShiftTable = {
        0: datetime(2023, 4, 17, 12, 0),
        1: datetime(2023, 4, 17, 19, 0),
        2: datetime(2023, 4, 18, 7, 0),
        3: datetime(2023, 4, 18, 19, 0),
        4: datetime(2023, 4, 19, 7, 0),
        5: datetime(2023, 4, 19, 19, 0),
        6: datetime(2023, 4, 20, 7, 0),
        7: datetime(2023, 4, 20, 19, 0),
        8: datetime(2023, 4, 21, 7, 0),
        9: datetime(2023, 4, 21, 19, 0),
        10: datetime(2023, 4, 22, 7, 0),
        11: datetime(2023, 4, 22, 19, 0),
        12: datetime(2023, 4, 23, 7, 0),
        13: datetime(2023, 4, 23, 19, 0),
        14: datetime(2023, 4, 24, 7, 0),
        15: datetime(2023, 4, 24, 19, 0),
    }
    start = ShiftTable[Shift]  # min datetime in shift
    limit = ShiftTable[Shift + 1]  # limit beyond shift datetime
    # Step 2: filter to just the desired shift
    ShiftData = [e for e in Raw if start <= e[2] < limit]
    # Step 3: eliminate anchor-anchor records
    ShiftData = [
        e for e in ShiftData if (not e[0].startswith("b")) or (not e[1].startswith("b"))
    ]
    # Steps 4 and 5: sort, put in OrderedDictionary; duplicates will be removed later, I hope
    ShiftData = sorted(ShiftData, key=lambda e: e[2])
    G = OrderedDict()
    for item in ShiftData:
        badge, otherbadge, T, distance, duration = (
            item[0],
            item[1],
            item[2],
            item[3],
            item[4],
        )
        if T not in G:
            G[T] = list()  # prep empty list as needed
        G[T].append(item)  # could introduce duplication, de-dupe later
    # Step 6 is kind of a mess: clean up the list for G[T]
    for T in sorted(G.keys()):
        clean(G[T])  # careful not to use assignment on dictionary!
        enforceSymmetry(G[T])
        # Step 8 is to merge overlapping intervals, which is done by
        # looking at current/future intervals only, and for at most 15 seconds
        for delta in range(16):  # 0 .. 15 seconds
            I = T + timedelta(seconds=delta)
            for item in G[T]:
                if I in G.keys():
                    intervalMerge(item, G[I])
    # Step 9 converts G to JSON and writes to file
    R = list()
    for T in sorted(G.keys()):
        for item in G[T]:
            stritem = copy.deepcopy(item)
            stritem[2] = repr(stritem[2]).replace("datetime.datetime", "datetime")
            R.append(stritem)
    with lzma.open(filename, "wb") as F:
        S = json.dumps(R, indent=4)
        B = S.encode("utf-8")
        F.write(B)


if __name__ == "__main__":
    # Unit test
    # with lzma.open(f"{DATA_DIR}/fulldata.xz", "r") as F:
    #     S = F.read().decode("utf-8")
    #     U = S.split("\n")
    #     Raw = json.loads(S)
    #     for i in range(len(Raw)):
    #         if Raw[i][2].startswith("datetime"):
    #             Raw[i][2] = eval(Raw[i][2])
    # makecontactintervals(Raw, Shift=2, filename="debug.json.xz")

    # open full data file, decompress and convert datetimes
    with lzma.open(f"{DATA_DIR}/fulldata.xz", "r") as F:
        S = F.read().decode("utf-8")
        U = S.split("\n")
        Raw = json.loads(S)
        for i in range(len(Raw)):
            if Raw[i][2].startswith("datetime"):
                Raw[i][2] = eval(Raw[i][2])

    # iterate over shifts 1 .. 14 making separate files
    if not os.path.exists(f'{DATA_DIR}/contact_intervals'):
        os.makedirs(f'{DATA_DIR}/contact_intervals')

    for n in range(1, 15):
        shiftfilename = f"{DATA_DIR}/contact_intervals/intervals{n:02d}.json.xz"
        makecontactintervals(Raw, Shift=n, filename=shiftfilename)
        print("saved shift", n, "contact intervals")
