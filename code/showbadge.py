"""
This module shows how to read two files and produce images
showing badge locations in the MICU for the April 2023 study.
The file placement005.yaml has coordinates of badges, in
pixel units, and the file iculayout.png is an adaptation of
a CAD file of the architecture of the MICU. We used this
program to make a figure for papers and presentations; from
the numbers in the files, the locations of each badge can
be calculated with respect to the architecture.
"""

import sys  # for debugging only
import cv2
import skimage.exposure
import yaml

SUPP_DIR = 'supp'
FIG_DIR = 'figures'

with open(f"{SUPP_DIR}/placement005.yaml") as F:
    R = yaml.load(F, Loader=yaml.FullLoader)
anchorlist = R["anchors"]


def anchordots():
    # produce anchordots.png showing location of anchors
    iculayout = cv2.imread(f"{FIG_DIR}/iculayout.png")
    height, width, depth = iculayout.shape
    minx = int(min(anchorlist[badge]["x"] for badge in anchorlist))
    miny = int(min(anchorlist[badge]["y"] for badge in anchorlist))
    for badge in anchorlist:
        x, y = int(anchorlist[badge]["x"]), int(anchorlist[badge]["y"])
        x = (
            x - minx + 50
        )  # strange numbers owing to Java program used to create yaml file
        y = y - miny + 50
        cv2.circle(iculayout, (x, y), 5, (0, 0, 255), -1)
    savepath = f"{FIG_DIR}/anchordots.png"
    cv2.imwrite(savepath, iculayout.astype('uint8'))
    print(f"Saved anchordots image to {savepath}")

def selectedarea():
    # produce enlarged portion of icu layout to show badge names
    iculayout = cv2.imread(f"{FIG_DIR}/iculayout.png")
    height, width, depth = iculayout.shape
    # pre-treatment to get lighter background
    iculayout = skimage.exposure.rescale_intensity(
        iculayout, in_range=(0, 8), out_range=(172, 255)
    )
    # produce enlarged portion of icu layout to show badge names
    minx = int(min(anchorlist[badge]["x"] for badge in anchorlist))
    miny = int(min(anchorlist[badge]["y"] for badge in anchorlist))
    # make a cropped version, quarter size, of upper left area
    cropped = iculayout[0 : int(height / 2), 0 : int(width / 2)]
    cropped = cv2.resize(cropped, (width, height))
    # show badge names in cropped area
    for badge in anchorlist:
        x, y = int(anchorlist[badge]["x"]), int(anchorlist[badge]["y"])
        x = (
            x - minx + 50
        )  # strange numbers owing to Java program used to create yaml file
        y = y - miny + 50
        if x < width / 2 and y < height / 2:
            cv2.putText(
                cropped,
                badge,
                (2 * x, 2 * y),
                cv2.FONT_HERSHEY_PLAIN,
                1.25,
                (255, 0, 255),
                2,
            )
    savepath = f"{FIG_DIR}/cropped.png"
    cv2.imwrite(savepath, cropped.astype('uint8'))
    print(f"Saved cropped image to {savepath}")


if __name__ == "__main__":
    anchordots()
    selectedarea()
