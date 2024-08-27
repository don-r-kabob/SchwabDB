CREATE TABLE IF NOT EXISTS futureTx (
    transactionId BIGINT NOT NULL,
    orderId BIGINT,
    assetType TEXT NOT NULL,
    symbol TEXT,
    description TEXT,
    quantity REAL,
    cost REAL,
    price REAL,
    positionEffect TEXT,
    expirationDate TEXT,
    expiration REAL,
    multiplier REAL,
    futureType TEXT,
    PRIMARY KEY (transactionId, symbol)
);