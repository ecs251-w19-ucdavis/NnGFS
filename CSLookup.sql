
-- Table to look up ip and port of a chunkserver given cs_id
CREATE TABLE CsidIp (
	cs_id INTEGER NOT NULL PRIMARY KEY,
	ip TEXT NOT NULL,
	port INTEGER NOT NULL,
	--
	UNIQUE(ip, port),
	CHECK(LENGTH(ip) > 0),
	CHECK(cs_id > 0),
	CHECK(port > 0)
);