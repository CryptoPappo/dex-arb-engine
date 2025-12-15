CREATE TABLE IF NOT EXISTS pools (
	chain TEXT,
	dex TEXT,
	address TEXT,
	token0 TEXT,
	token1 TEXT,
	fee INT,
	created_block BIGINT,
	create_timestamp TIMESTAMP
);
