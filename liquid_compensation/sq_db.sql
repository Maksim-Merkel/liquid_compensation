CREATE TABLE IF NOT EXISTS bases (
id integer PRIMARY KEY AUTOINCREMENT,
base_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS wells (
base_name_id integer,
well_name text NOT NULL,
date DATETIME,
nature TEXT,
condition TEXT,
liquid_extraction FLOAT,
oil_production FLOAT,
water_intake FlOAT
);

CREATE TABLE IF NOT EXISTS trajectories (
base_name_id integer,
well_name text NOT NULL,
depth FLOAT,
absolute_mark FLOAT,
x FLOAT,
y FLOAT,
breakdown text
);