-- fixedIncomeTx.sql
CREATE TABLE IF NOT EXISTS fixedIncomeTx (
    transactionId BIGINT NOT NULL,
    orderId BIGINT,
    assetType TEXT NOT NULL,
    symbol TEXT,
    description TEXT,
    quantity REAL,
    cost REAL,
    price REAL,
    positionEffect TEXT,
    factor REAL,
    maturityDate TEXT,
    multiplier REAL,
    type TEXT,
    variableRate REAL,
    PRIMARY KEY (transactionId, symbol)
);