#!/bin/bash

psql --username "$POSTGRES_USER" <<EOF
CREATE DATABASE $POSTGRES_DATABASE WITH OWNER $POSTGRES_USER;
GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DATABASE TO $POSTGRES_USER;

\c $POSTGRES_DATABASE
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

EOF