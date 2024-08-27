CREATE TABLE IF NOT EXISTS transactions (
    activityId INTEGER PRIMARY KEY,
    time REAL,
    description TEXT,
    accountNumber TEXT,
    type TEXT,
    status TEXT,
    tradeDate REAL,
    netAmount REAL,
    orderId INTEGER DEFAULT NULL,
    totalFees REAL DEFAULT 0.0
);