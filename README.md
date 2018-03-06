# Density API Homework Assignment - Kai Keliikuli


## Database Schema
1. [Timescaledb init script](./app/db/entrypoint/01-initialize.sh)
2. [Schema] (./app/db/entrypoint/01-schema.sql)


## Prototype Application

  The following commands build docker image for the app, start up docker containers(postgres, redis, flask app), 
  initialized the database and timescaledb extension, and create the schema. 

```bash
docker build -f Dockerfile.apihw -t apihw:latest .
docker-compose up
```

This command loads the sample data by executes requests to the send api endpoint.
### start executing requests to the /send endpoint 
```bash
docker exec -it  dhw_app_1 python3 /app/load.py
```


## Schema

  This file contains inline sql comments for tables and rows.
  [01-schema.sql](./app/db/entrypoint/01-schema.sql)

## Data ingress

When a datapoint arrives 
1. The realtime count and timestamp for the dpu is incremented in redis and a count field is added to the datapoint. 
The datapoint is then inserted in two tables dpu_log and dpu_telemetry. dpu_log is the data as received. 
dpu_telemetry includes additional fields that allow for reconciliation.

2. Counters for spaces are incremented in redis using the product of the dpu direction and the dpu/space direction. 

3. The count from (2) is added to a record for the space and inserted in the space_count table

## Real-time use cases
Real time counts are read from redis where the latest reading for a dpu and the latest count for a space are
continously updated. 

### Real time count queries
```bash
curl http://127.0.0.1:5000/?space=A

{'status': 'OK', 'count': 2}
```

### No data available
```bash
curl http://127.0.0.1:5000/?space=X

{'status': 'OK', 'count': null}
```

### Brief history storage in redis
Although not implemented in this assignment storage of a list of the most recent counts
would be easy to implement to prevent queries of recent datapoints from hitting the relational
database.  Determining the need for this feature could be done by analyzing traffic logs.

## Historical use cases 
Historical data is stored in the following tables
1. dpu_log: a raw historical record of datapoints as they are received
2. dpu_telemetry: historical record of datapoints augmented with counts and reconciliation timestamps
3. space_count: reporting table with space counts. 


### Historical count for a space 
The count returned for the space will be the nearest timestamp to the one sent in the request.
```bash
curl http://127.0.0.1:5000/count?space=a&timestamp=2018-02-24 17:24:25.493z
{'status': 'ok', 'count': 2}
```

### No data available
curl http://127.0.0.1:5000/count?space=a&timestamp=2018-02-24 17:24:25.493z
{'status': 'ok', 'count': null}


### Reconciled historical counts
The infrastructure is in place to support querying reconciled historical counts but the endpoint 
and reconciliation tasks are not implemented

### Data delivery issues. Reconciled counts
Provisions to support reconciled historical counts have been started but not yet implemented
1. Scheduled Reconciliation Tasks
2. columns for storing the reconciled count, and reconciliation timestamp alongside the realtime count
3. Storage of the raw dpu data and a separate table for reconciled data. 

### Movement of sensors.
The dpu_location table stores space, door, dpu relationships. Each record has an installed timestamp 
and a current flag - these columns make it possible to move dpus and ensure that historical telemetry record
queries are accurate. 

### Replay support
Data happens. For development, debugging, and forensics I always like to have the raw data logs available.
The data in dpu_log can be used to replay a time window by querying it sorted using the created column.
the dpu_telemetry table includes reconciliation schema features for reporting.
If space becomes an issue the raw logs can be rotated using an archival policy so that aging data is rotated out
RDS -> S3 -> Glacier -> deletion.


## Production Technology stacks

### Redis
 - redis is very well suited for, and frequently used for storing counters in the financial and analytics sectors. 
 - Redis makes hard guarantees of atomicity and has excellent transaction support.
 - Depending on budget and devops staffing the redis implementation could be self-managed or hosted.
 - AWS provides a great hosted implementation that scales adequately for Density's requirements.

### Messaging Queue and Scheduler

 - RedisQueue(RQ) and RQ Scheduler
 - Since we're using redis already this simple python based messaging queue system is a natural choice.  
 - RQ Scheduler allows us to add job sceduling to RQ - so that we can execute telemetry reconciliation tasks.
   We don't want to fire these everytime a reading is received out of order. 
 - There are a lot of messaging queue systems and schedulers out there. A great hosted alternative would be 
   amazon sqs and using a lambda to fire scheduled tasks

### Time series database 

   - Time series data has a lot of special requirements and a lot of work and thought
   has been put into how to process it. I strongly recommend using an existing time series dbms.

   - timescaledb is a postgres extension which provides a horizontally scalable solution for time series data.
   - Vertica is also based on postgres and has great customer support. However the learning curve is steep,
   the community is small and the price is high.

   - I am not aware of an AWS timeseries database. As far as I know the current options are
   1. roll my own time series functions and use a hosted RDBMS
   2. Use a timeseries RDBMS and support infrastructure for it  

   I'm not sure which direction to go on this one. I'm leaning towards (1) but I'd have to get a better picture
   of historical querying use cases 




