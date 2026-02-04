from datetime import datetime, timedelta
from collections import OrderedDict
import sys, os, lzma, json
import extractspread
DATA_DIR = 'data'
SUPP_DIR = 'supp'
"""
Geography: get anchor information from spreadsheet, 
    and define some convenience functions for rooms and doors
"""
# table of anchors that are in patient rooms
# maps badge -> (roomnumber,role) where role is one of "door",
#               "computer", "vitals", "sink"
AnchorTable = extractspread.getAnchors(SUPP_DIR)


def roomOfDoor(door):
    # return room number for a given door
    assert door in AnchorTable
    room, role = AnchorTable[door]
    assert role == "door"
    return room


def getCloseDoor(T, moment, badge):
    # return closest doors in contact with badge for T[moment]
    # (return None if there is no such door)
    candidates = [e for e in T[moment][badge] if e.startswith("b")]
    doors = list()
    for e in candidates:
        if e not in AnchorTable:
            continue
        room, role = AnchorTable[e]
        if role == "door":
            doors.append(e)
    if len(doors) == 0:
        return None
    closedoor, distance = None, 1000
    for e in doors:
        d = T[moment][badge][e]
        if d < distance:
            closedoor, distance = e, d
    return closedoor


def getRoomAnchors(T, moment, badge, givenroom):
    # return list of anchors in contact for given (badge,room)
    candidates = [e for e in T[moment][badge] if e.startswith("b")]
    roomAnchors = list()
    for e in candidates:
        if e not in AnchorTable:
            continue
        room, role = AnchorTable[e]
        if role != "door" and givenroom == room:
            roomAnchors.append(e)
    return roomAnchors


def allRoomAnchors(givenroom):
    # return list of all the anchors of a given room
    R = list()
    for anchor in AnchorTable:
        room, role = AnchorTable[anchor]
        if room == givenroom:
            R.append(anchor)
    return R


"""
 Object-oriented history: for each second of time in history,
 there are objects mapping badges to states, where states 
 are represented as Python objects with attributes

 NOTE NOTE NOTE

 StateMap (see second line in class definition) is not
 an object attribute! It is a *class* attribute, so there
 is just one StateMap for the entire State class - its 
 use is to have history for an iterative construction of 
 history, so we can infer things from a previous StateMap
 when constructing a new one.
"""


# objects that map (worn) badge number to state, eg
#  State.StateMap["n005"].room -> number of patient room for recent contact
#    .inroom -> True/False for confirmed in-room status
#    .doortime -> datetime of most recent door contact in room
#    .door -> None or assigned door
#    .pending -> True/False for suspected room entry
#    .badge -> "n005"
class State(object):
    StateMap = dict()  # to be populated later

    def InitState(self, wornbadgelist):
        # class method (not instance method)
        # wornbadgelist can be a set, a list, or a StateMap
        State.StateMap.clear()
        if isinstance(wornbadgelist, dict):
            State.StateMap = wornbadgelist
            return
        for badge in wornbadgelist:  # set or list
            State.StateMap[badge] = State(badge)

    def fullcopy(self):
        # class method (not instance method)
        clone = State.StateMap.copy()
        for item in clone:
            clone[item] = State.StateMap[item].copy()
        return clone

    def __init__(self, badge):
        self.badge = badge
        self.room = self.doortime = self.door = None
        self.inroom = self.pending = False

    def __repr__(self):
        msg = "badge {0} room {1} doortime {2} pending {3} inroom {4} door {5}"
        return msg.format(
            self.badge, self.room, self.doortime, self.pending, self.inroom, self.door
        )

    def copy(self):
        new = State(self.badge)
        new.room, new.doortime, new.door = self.room, self.doortime, self.door
        new.inroom, new.pending = self.inroom, self.pending
        return new


def genstate(T, moment, badge, oldstatemap):
    """
    This function is intended for iterative update of State.StateMap;
    for specified moment, and having a copy of the previous State.StateMap
    in oldstatemap, it updates State.StateMap[badge] with new information,
    if possible; otherwise the new State.StateMap will just be the same
    as oldstatemap. For this idea to be correct, genstate will need to
    be invoked on all badges for the specified moment.
    """
    assert badge in oldstatemap
    assert badge in T[moment]
    current, previous = State.StateMap[badge], oldstatemap[badge]
    entry = T[moment][badge]

    # debugging:
    candidates = [e for e in T[moment][badge] if e.startswith("b")]
    if current.inroom and len(candidates) == 0:
        # print("note:",badge,"in room but no anchors in contact",moment)
        pass

    # complicated code upcoming! the idea is to follow a badge
    # as it goes through stages entering, being in, and leaving a
    # patient room (hence we have attributes door, doortime,
    # pending, and inroom)
    if current.inroom:
        interior = getRoomAnchors(T, moment, badge, current.room)
        closedoor = getCloseDoor(T, moment, badge)
        if closedoor and roomOfDoor(closedoor) == current.room:
            interior.append(closedoor)
        if len(interior) > 0:
            return  # maintain current.inroom
        # if no anchors for current.room exist, either timeout or invalidate
        candidates = [e for e in T[moment][badge] if e.startswith("b")]
        if len(candidates) == 0:
            # curious case -- no reason to quit room except for timeout
            elapsed = (moment - current.doortime).total_seconds()
            if elapsed > 60:
                # print(badge,"timeout/left room",moment)
                current.room = current.doortime = current.door = None
                current.inroom = current.pending = False
                return
        if len(candidates) > 0:
            # handle like timeout unless a candidate is another room
            # print(badge,"in-room, but maybe left room",moment)
            if not any(e in AnchorTable for e in candidates):
                current.room = current.doortime = current.door = None
                current.inroom = current.pending = False
                return
            # we have a possible transition -- fall through to next case
    if not current.inroom and not current.pending:
        # NOTE: this case is where a badge gets pending and doortime
        # attributes and a tentative assignment of which patient room
        current.room = current.doortime = current.door = None
        door = getCloseDoor(T, moment, badge)
        if not door:
            return
        current.pending = True
        current.doortime = moment
        current.room = roomOfDoor(door)
        # print("badge",badge,"pending for",current.room,"at",moment)
        # fall through to next case, which tests for sink/vitals/computer
    elapsed = 0
    if current.doortime:
        elapsed = (moment - current.doortime).total_seconds()
    if not current.inroom and current.pending and elapsed > 180:  # cutoff at 3 mins
        current.room = current.doortime = current.door = None
        current.inroom = current.pending = False
        return
    if not current.inroom and current.pending:  # elapsed <= 180
        # NOTE: here is a case where being in a room (inroom attribute)
        # can be falsified: test visible anchors to see if any belongs outside room
        candidates = [e for e in T[moment][badge] if e.startswith("b")]
        if any(
            e in AnchorTable and AnchorTable[e][0] != current.room for e in candidates
        ):
            # print(badge,"false alarm",moment,"for room",current.room)
            current.room = current.doortime = current.door = None
            current.inroom = current.pending = False
            return
        # liberalize previous test to include anchors NOT in a room
        if any(e not in AnchorTable for e in candidates):
            current.room = current.doortime = current.door = None
            current.inroom = current.pending = False
            return
        interior = getRoomAnchors(T, moment, badge, current.room)
        if interior:  # doesn't matter which one
            # NOTE: here is the case where tentatively being in a room
            # becomes validated by detecting an in-room anchor
            current.pending = False
            current.inroom = True

    # after all the case logic above, State.StateMap[badge]
    # for the specified (moment,badge) has been updated. Nothing
    # to return (output is in the State object).
    return


"""
    Goal of this module is to convert one shift of raw badge data 
    into a chronological history: a map from datetime objects to
    a map from badge to state objects. 
"""


def history(records):
    """
    Input:
        each item of records is contact interval of the form
         (badge,otherbadge,datetime,distance,duration)
        see contactinterval.py to learn how this was computed
    Output:
        an ordered dictionary mapping local datetime -> badge status
        where badge status is a dictionary from badgeId to a list of other
        badges that were "close" to badgeId at the specified datetime
        Example: an entry like
         Key: (datetime.datetime(2022, 6, 5, 16, 40, 36)
         Value: {'n002': {}, 'n003': {'b002': 40}, 'n004': {}})
        means that at 06/05/2022 16:40:36 badge n003 is near b002
        with a distance of 40 inches
    """
    H = OrderedDict()  # will become history mapping local datetime -> badge status

    # set up time points in history
    mindate = min(t[2] for t in records)
    maxdate = max(t[2] for t in records)
    # establish H as dictionary from datetime to empty dictionary
    for second in range(
        (maxdate - mindate).seconds + 600
    ):  # +600 to account for possible last interval
        H.setdefault(mindate + timedelta(seconds=second), dict())

    # set up status of badges throughout history, for each badge
    badgeset = set(t[0] for t in records) | set(t[1] for t in records)
    badgelist = sorted(badgeset)
    for key in H.keys():  # at each point in history, there is a dictionary of the badges
        for badge in badgeset:
            if not badge.startswith("b"):  # ignore anchors as primary contacts in history
                H[key].setdefault(badge, dict())  # map badge to empty list, later to become dict of others who are near

    # traverse contact intervals and use them to fill history
    for r in records:
        reltime = (r[2] - mindate).seconds  # relative time in history
        duration = r[4]  # duration of badge-to-badge close proximity
        for t in range(duration):  # step through each second of interval
            histime = mindate + timedelta(seconds=t) + timedelta(seconds=reltime)  # identify second in history
            if histime not in H: continue  # if went beyond end of history, ignore
            if r[0].startswith('b'): continue  # ignore anchors in history
            H[histime][r[0]][r[1]] = r[3]  # record distance value from record for that second in time

    return H


def inroomhist(T):
    """
    Create and return a dictionary from datetimes to distinct
    copies of StateMap (attribute of State class): this dictionary
    will be useful to have a relevant memory of recent interactions
    of a badge as it moves around.
    """
    # Phase 1: build initial state table for history T
    # (input T is created by history(records))
    wornbadgeset = set()
    for moment in T:
        for badge in T[moment]:
            if badge.startswith("b"): continue
            wornbadgeset.add(badge)
            for other in T[moment][badge]:
                if other.startswith("b"): continue
                wornbadgeset.add(other)
    State.InitState(None, wornbadgeset)
    # henceforth, State.StateMap["n005"] should have meaning

    # Phase 2: construct a mapping from moments in T to
    # StateMaps (each will be a copy of StateMap for that moment)
    previous = None
    StateMapHistory = OrderedDict()
    for moment in T:
        if not previous:
            State.InitState(None, wornbadgeset)
            previous = State.fullcopy(None)
        for badge in T[moment]:
            if badge.startswith("b"): continue  # for full symmetry, we could do more!
            genstate(T, moment, badge, previous)
        previous = State.StateMap
        StateMapHistory[moment] = State.fullcopy(None)

    # return the mapping moment -> StateMap
    return StateMapHistory


def combineRoomHist(T, V):
    """
    Return a map that combines maps of contact history with
    a dictionary of attributes for inferences about a badge being in a room
    """
    R = OrderedDict()
    for moment in T:
        entry = dict()
        for badge in T[moment]:
            contacts = list(T[moment][badge].keys())
            entry[badge] = {"contacts": contacts}
            state = V[moment][badge]
            if not state.room:
                entry[badge]["state"] = None
            else:
                entry[badge]["state"] = dict()
                if state.room:
                    entry[badge]["state"]["room"] = state.room
                if state.inroom:
                    entry[badge]["state"]["inroom"] = state.inroom
                if state.pending:
                    entry[badge]["state"]["pending"] = state.pending
        R[moment] = entry
    return R


def makehistory(contactintervalfile, filename):
    # given a file of JSON-encoded contact intervals
    # sorted order by datetime, make a history and
    # write its JSON to the specified file
    with lzma.open(contactintervalfile, "r") as F:
        U = F.read().decode("utf-8")
    T = json.loads(U)
    K = [[item[0], item[1], eval(item[2]), item[3], item[4]] for item in T]
    T = history(K)
    V = inroomhist(T)
    R = combineRoomHist(T, V)
    # convert R to list of item with datetime objects as strings
    S = dict(
        (repr(k).replace("datetime.datetime", "datetime"), v) for k, v in R.items()
    )
    with lzma.open(filename, "wb") as F:
        U = json.dumps(S, indent=4)
        B = U.encode("utf-8")
        F.write(B)

if __name__ == "__main__":
    # Unit test
    # contactintervalfile = f"{DATA_DIR}/contact_intervals/intervals02.json.xz"
    # makehistory(contactintervalfile,"debug.json.xz")

    # iterate over shifts 1 .. 14 making separate files
    if not os.path.exists(f'{DATA_DIR}/histories'):
        os.makedirs(f'{DATA_DIR}/histories')

    for n in range(1, 15):
        contactintervalsfile = f"{DATA_DIR}/contact_intervals/intervals{n:02d}.json.xz"
        historyfile = f"{DATA_DIR}/histories/histories{n:02d}.json.xz"
        makehistory(contactintervalsfile, historyfile)
        print("saved shift", n, "histories")
