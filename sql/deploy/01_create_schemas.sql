-- Create processing schemas in the selected database.
-- The database must already exist.

CREATE SCHEMA IF NOT EXISTS
<% database %>.RAW;

CREATE SCHEMA IF NOT EXISTS
<% database %>.STAGING;

CREATE SCHEMA IF NOT EXISTS
<% database %>.ANALYTICS;
