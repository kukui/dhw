CREATE TABLE IF NOT EXISTS spaces (
    id VARCHAR(32) PRIMARY KEY
);

INSERT INTO SPACES(id)values('A');
INSERT INTO SPACES(id)values('B');

CREATE TABLE IF NOT EXISTS doorways (
    id VARCHAR(32) PRIMARY KEY
);
INSERT INTO doorways(id)values('X');
INSERT INTO doorways(id)values('Z');

CREATE TABLE IF NOT EXISTS dpus (
    id VARCHAR(32) PRIMARY KEY
);
INSERT INTO dpus(id)values('283');
INSERT INTO dpus(id)values('423');


CREATE TABLE IF NOT EXISTS dpu_location(
    dpu_id VARCHAR(32) REFERENCES dpus(id),
    space_id VARCHAR(32) REFERENCES spaces(id),
    doorway_id VARCHAR(32) REFERENCES doorways(id),
    installed TIMESTAMPTZ,
    current BOOLEAN,
    direction SMALLINT,
    UNIQUE(dpu_id, space_id, doorway_id,current, direction)
);

INSERT INTO dpu_location(dpu_id, space_id, doorway_id, current, direction)values('283','A','X',TRUE,1);
INSERT INTO dpu_location(dpu_id, space_id, doorway_id, current, direction)values('423','A','Z',TRUE,1);
INSERT INTO dpu_location(dpu_id, space_id, doorway_id, current, direction)values('423','A','Z',TRUE,-1);

COMMENT ON TABLE dpu_location IS 'this table is for tracking dpu location information';
COMMENT ON COLUMN dpu_location.space_id IS 'the space this dpu location record is associated with. There may be more than one current space association with a dpu';
COMMENT ON COLUMN dpu_location.doorway_id IS 'there can only be one current doorway associated with a dpu';
COMMENT ON COLUMN dpu_location.installed IS 'the time the dpu was installed at the location';
COMMENT ON COLUMN dpu_location.current IS 'boolean denoting the current installation location';
COMMENT ON COLUMN dpu_location.direction IS 'the sign associated with entering space_id';

CREATE TABLE dpu_log(
    created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    recorded TIMESTAMPTZ,
    dpu_id VARCHAR(32),
    direction SMALLINT
);

COMMENT ON TABLE dpu_log IS 'dpu telemetry data as received. the absence of foreign keys on here is intentional. TODO: consider using pg_cron or a trigger to auto-expire these records';
COMMENT ON COLUMN dpu_log.created IS 'the time of record insert';
COMMENT ON COLUMN dpu_log.recorded IS 'the time reported by the dpu';
COMMENT ON COLUMN dpu_log.direction IS '1 or -1. direction of motion relative to the sensor';

SELECT create_hypertable('dpu_log', 'recorded');

CREATE TABLE dpu_telemetry(
    created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    recorded TIMESTAMPTZ,
    reconciled TIMESTAMPTZ,
    dpu_id VARCHAR(32),
    direction SMALLINT,
    count INTEGER,
    reconciled_count INTEGER
);

SELECT create_hypertable('dpu_telemetry', 'recorded');

COMMENT ON TABLE dpu_telemetry IS 'dpu telemetry data with counts added. the absence of foreign keys on here is intentional.';
COMMENT ON COLUMN dpu_telemetry.created IS 'the time of record insert';
COMMENT ON COLUMN dpu_telemetry.recorded IS 'the time reported by the dpu';
COMMENT ON COLUMN dpu_telemetry.reconciled IS 'the time this record was corrected';
COMMENT ON COLUMN dpu_telemetry.dpu_id IS 'for the dpu_id';
COMMENT ON COLUMN dpu_telemetry.count IS 'this count is created by incrementing the count of the most recently created record for the dpu_id';
COMMENT ON COLUMN dpu_telemetry.reconciled_count IS 'this count is calculated by reprocessing/reconciliation.';


CREATE TABLE space_count(
    created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    recorded TIMESTAMPTZ,
    reconciled TIMESTAMPTZ,
    space_id VARCHAR(32),
    dpu_id VARCHAR(32),
    count INTEGER,
    reconciled_count INTEGER
);

