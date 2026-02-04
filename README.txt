Data (under `data` folder): 
    - File `fulldata.xz` was manually created by running python scripts using the
        Instant-Trace API to collect records, then catenating all of these into
        fulldata, and finally running xz to compress.  Each record in fulldata 
        is the raw detection from the Instant-Trace database

    - Folder `contact_intervals` has the contact intervals derived from fulldata. 
    
    - Folder `histories` has the histories derived from contact intervals. 
        Each history is a list of contact intervals for a shift.

Supplementary materials (under `supp` folder): 
    - File `badgelocation.xlsx` has the notes entered during the deployment.

    - File `placement005.yaml` has pixel coordinates of all
        the anchors with respect to `iculayout.png`. 


Figures (under `figures` folder):
    - Figure `iculayout.png` was derived from CAD files of the MICU architecture. 


Code (under `code` folder):
    - Module `extractspread.py` parses the spreadsheet to know what are anchors 
        in patient rooms, etc. 

    - Module `make_intervals.py` reads fulldata and constructs a contact 
        interval for a shift; saving each shift's contact intervals in the directory 
        `data/contact_intervals`, in compressed form. 
        To run this module: `python code/make_intervals.py`

    - Module `make_history.py` contains code to create a history for each shift, 
        saving the result in the `data/histories`, in compressed form.
        To run this module: `python code/make_histories.py` (required to run module
        `make_intervals.py` first)

    - Notebook `IowaMICU2023.ipynb` documents running `code/hcplist.py`, which demonstrates
        ways of counting badges in each shift by reading and filtering files 
        in `data/contact_intervals`.

    - Module `code/showbadge.py` is a demonstration of reading iculayout 
        and placement005 to produce one of the images used in the paper.   

    - Module `code/validation.py` includes code to validate the provided data
        by visualizing the average number of active HCP badges during the day.
        To run this module: `python code/validation.py` (required to run module
        `make_histories.py` first)

