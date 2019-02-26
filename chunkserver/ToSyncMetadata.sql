
CREATE TABLE ToSync (
	cs_id INTEGER NOT NULL,
	file_name TEXT NOT NULL,
	chunk_id INTEGER NOT NULL,
	--
	PRIMARY KEY(cs_id, file_name, chunk_id),
	CHECK(LENGTH(file_name) > 0),
	CHECK(cs_id > 0),
	CHECK(chunk_id >= 0)
);