import pandas, os, sys
import numpy as np

SUPP_DIR = 'supp'

class badge(object):
    def __init__(self, room=None, place=None, name=None):
        self.room = room
        self.place = place
        self.name = name

    def __repr__(self):
        return {"ID": self.name, "room": self.room, "place": self.place}.__repr__()


def getbadge_loc_table(homedir):
    df = pandas.read_excel(
        homedir + "/" + [e for e in os.listdir(homedir) if e.endswith("xlsx")][0]
    )
    seeknames = [
        e
        for e in df.columns
        if e.startswith("Badge") or e.startswith("Room") or e.startswith("Location")
    ]
    projectseek = df[seeknames]  # only the columns of interest
    # pull out just the rooms
    roomonly = list(projectseek["Room"])
    selflist = zip(range(len(roomonly)), roomonly)
    selrooms = [t for (t, r) in selflist if isinstance(roomonly[t], int)]
    roomlist = list()
    R = np.array((projectseek.iloc[selrooms]))
    for row in R:
        name, room, place = row
        if name == "x":
            name = "b047"  # until new spreadsheet
        roomlist.append(badge(room=room, place=place, name=name))
    return roomlist


def getAnchors(homedir):
    T = getbadge_loc_table(homedir)
    TypeTable = dict()  # map badge -> (room,place)
    for row in T:
        TypeTable[row.name] = (row.room, row.place)
    return TypeTable


if __name__ == "__main__":
    print(getAnchors(f"{SUPP_DIR}"))
