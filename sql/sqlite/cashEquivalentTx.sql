CREATE TABLE IF NOT EXISTS cashEquivalentTx (
    transactionId BIGINT NOT NULL,
    orderId BIGINT,
    assetType TEXT NOT NULL,
    symbol TEXT,
    description TEXT,
    quantity REAL,
    cost REAL,
    price REAL,
    positionEffect TEXT,
    instrumentType TEXT,
    PRIMARY KEY (transactionId, symbol)
);