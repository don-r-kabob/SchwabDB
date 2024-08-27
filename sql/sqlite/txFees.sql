CREATE TABLE IF NOT EXISTS txFees (
    activityId BIGINT NOT NULL,
    feeType TEXT NOT NULL,
    amount REAL NOT NULL,
    PRIMARY KEY (activityId, feeType)
);