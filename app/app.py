import copy
import pprint
from dateutil.parser import parse as parsedate
from flask import Flask, request
from flask_restful import Resource, Api
import redis

import dbpool
app = Flask(__name__)
api = Api(app)
FLASK_DEBUG=True

DPU_TELEM_SQL = '''
insert into dpu_telemetry(recorded, direction, dpu_id)
values(%(timestamp)s, %(direction)s, %(dpu_id)s)
'''

DPU_LOG_SQL = '''
insert into dpu_telemetry(recorded, direction, dpu_id)
values(%(timestamp)s, %(direction)s, %(dpu_id)s)
'''

SPACE_TELEM_SQL = '''
insert into space_count(recorded, dpu_id, space_id, count)
values(%(recorded)s, %(dpu_id)s, %(space_id)s, %(count)s)
'''

SPACE_COUNT_SQL = '''
select count, recorded,
@ extract(epoch from(recorded::timestamp - %(timestamp)s::timestamp)) as diff
from space_count where space_id='A'
group by count, recorded
order by diff asc, count desc
limit 1;
'''


class DPUTelemetryWriterResource(Resource):

    _dpu_spaces = None

    def __init__(self):
        self.redis_pool = redis.ConnectionPool(host='redis', port=6379, db=0)
        self.pg = dbpool

    def dpu_spaces(self, dpu_id=None):

        if self._dpu_spaces is None or self._dpu_spaces.get(dpu_id) is None:
            self._dpu_spaces = {}

            with self.pg.get_db_cursor(commit=True) as cursor:
                cursor.execute('select dpu_id, space_id, doorway_id, direction from dpu_location where current=TRUE')
                result = cursor.fetchall()
                for r in result:
                    self._dpu_spaces.setdefault(r['dpu_id'], []).append(r)

        return self._dpu_spaces.get(dpu_id, [])

    def _queue_reconciliation(self, dpu_id, timestamp):
        '''
        TODO: implement a system for flagging records which need to be
        handled by a scheduled reconciliation event
        '''
        pass

    def post(self):
        record = request.get_json(force=True)
        record['direction'] = int(record['direction'])
        r = redis.Redis(connection_pool=self.redis_pool)
        # TODO: verify timezone handling
        # TODO: use pub/sub to wrap the redis transaction and the postgres transaction?

        # begin redis transaction
        current_timestamp = parsedate(record['timestamp']).timestamp()
        previous_datetime = r.get('{}:timestamp'.format(record['dpu_id']))

        if previous_datetime:
            previous_timestamp = parsedate(previous_datetime).timestamp()
        else:
            previous_timestamp = current_timestamp

        transaction = r.pipeline()

        if previous_timestamp > current_timestamp:
            self._queue_reconciliation(record['dpu_id'], current_timestamp)

        spaces = self.dpu_spaces(record['dpu_id'])

        transaction.incr(record['dpu_id'])
        transaction.set('{}:timestamp'.format(record['dpu_id']), record['timestamp'])
        record['count'], _ = transaction.execute()

        transaction = r.pipeline()
        for space in spaces:
            transaction.incr('{}:count'.format(space['space_id']), space['direction'] * record['direction'])
        transaction.execute()

        # begin postgres transaction
        with self.pg.get_db_cursor(commit=True) as cursor:
            cursor.execute(DPU_LOG_SQL, record)
            cursor.execute(DPU_TELEM_SQL, record)

            # TODO: add handling for unmatched spaces
            for space in spaces:
                space_record = {
                    'recorded': record['timestamp'],
                    'space_id': space['space_id'],
                    'dpu_id': record['dpu_id'],
                    'count': record['count'] + space['direction'] * record['direction']
                }
                cursor.execute(SPACE_TELEM_SQL, space_record)
                print(cursor.query)
        return {'status': 'OK'}


class DPUTelemetryCounterResource(Resource):
    def __init__(self):
        self.redis_pool = redis.ConnectionPool(host='redis', port=6379, db=0)
        self.pg = dbpool

    def get(self):
        '''
        TODO: add exception handling. add a threshold
        '''
        print(request.args)
        timestamp = request.args.get('timestamp')
        space = request.args.get('space')

        if timestamp is None:
            r = redis.Redis(connection_pool=self.redis_pool)
            return {'status': 'OK', 'count': int(r.get('{}:count'.format(space)))}


        with self.pg.get_db_cursor(commit=True) as cursor:
            cursor.execute(SPACE_COUNT_SQL, {'space': space, 'timestamp': timestamp})
            result = cursor.fetchone()

        return {'status': 'OK', 'count': result['count']}



api.add_resource(DPUTelemetryWriterResource, '/send')
api.add_resource(DPUTelemetryCounterResource, '/count')


def main():
    r = redis.StrictRedis(host='redis', port=6379, db=0)
    # set some initial counts
    r.set('283', 10)
    r.set('423', 20)
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
