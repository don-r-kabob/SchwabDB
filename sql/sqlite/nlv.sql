CREATE TABLE IF NOT EXISTS nlv (
    timestamp REAL NOT NULL,
    accountNumber TEXT NOT NULL,
    initialNLV REAL,
    currentNLV REAL,
    aggregateNLV REAL,
    initialBP REAL,
    currentBP REAL,
    PRIMARY KEY (timestamp, accountNumber)
);