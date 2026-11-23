CREATE TABLE position (
    id INTEGER PRIMARY KEY,
    x REAL,
    y REAL,
    z REAL
);

CREATE TABLE quaternion (
    id INTEGER PRIMARY KEY,
    x REAL,
    y REAL,
    z REAL,
    w REAL
);

CREATE TABLE pose (
    id INTEGER PRIMARY KEY,
    time REAL,
    frame TEXT,
    position_id INTEGER REFERENCES position (id),
    orientation_id INTEGER REFERENCES quaternion (id)
);
