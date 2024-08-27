# Schwab_db

An application which creates and updates a database
for storing transactions and NLV using schwab individual API


Requirements:

- Python 3.10 (schwab-py requirement)
- schwab-py
- Pandas
- Matplotlib
- Seaborn

A schwab app with a port number from schwab developer portal.

# Features

1. Transaction database
   - Includes:
     - Equities
     - ETFs
     - Futures
     - Equity options
     - Futures options
2. NLV and buying power Tracking
2. Ability to store/read token using AWS dynamodb
3. streamlit interface
4. option to save transaction json files for:
   - record keeping
   - reparsing later with database updates
   - 

# Installations

1. Check python version and confirm >= 3.10 (latest at time of writing) 

```python --version``` 

2. If desired set up virtual environment (recommended)

    ```virtualenv venv```

3. Install packages

    Windows: ```pip install -r requirements.txt```

   Linux/Mac: ```pip install -r requirements.txt```

# Running
1. Get Auth Token (see below)
2. Start database (ideally a background process)
     Windows ```python schwab_db.py```
    Linux/mac ```python3 schwab_db.py```
   
    - if you wish to redownload a certain number of previous days run the script 1 time or everytime using ```--daysback #```

    ```python3 schwab_db.py --daysback 365```

3. Run interface to view if desired

    ```streamlit run streamlit_interface.py```

# Getting authtoken

#### Things you will need

1. Schwab app key
2. Schwab app secret
3. Schwab app callback uri (with port, ie https://127.0.0.1:8501)
4. Optional
   - Default account number (in string format)

1. Setup app config
2. 

### Known issues

- Transactions delay: The transactions api generally fills in trades with a delay,
but some fields are filled in later (i have observed ~7-10 day lag)
  - Workarounds: None
- Box spreads make us sad. Box spreads are processed as a option 
transaction but closed multiple different ways depending on ITM/OTM
  - Workarounds: Remove SPX and SPXW from ticker lists (where possible)
- 