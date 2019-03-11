
DROP TABLE IF EXISTS ToSync;
DROP TABLE IF EXISTS CsidIp;

CREATE TABLE ToSync (
    tosync_id INTEGER PRIMARY KEY AUTO INCREMENT,
    cs_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    --
    UNIQUE (cs_id, file_path),
    CHECK(LENGTH(file_path) > 0),
    CHECK(cs_id > 0)
);

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