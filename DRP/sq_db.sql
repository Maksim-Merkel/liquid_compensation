CREATE TABLE IF NOT EXISTS bases (
id integer PRIMARY KEY AUTOINCREMENT,
base_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
case_ID integer,
base_name_id integer,
well_name text NOT NULL,
name_of_the_field TEXT,
date TEXT,
P FLOAT,
S FLOAT,
case_status text
);

