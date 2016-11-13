
import unittest

try:
    import simplejson as json
except ImportError:
    import json

from alerta.app import app, db
from pymongo import MongoClient


class BlackoutsTestCase(unittest.TestCase):

    def setUp(self):

        MongoClient().drop_database(app.config['MONGO_DATABASE'])

        app.config['TESTING'] = True
        app.config['AUTH_REQUIRED'] = True
        app.config['CUSTOMER_VIEWS'] = True
        self.app = app.test_client()

        self.alert = {
            'event': 'node_marginal',
            'resource': 'node404',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'warning',
            'correlate': ['node_down', 'node_marginal', 'node_up']
        }

        self.admin_api_key = db.create_key('admin-api-key', type='read-write', text='demo-key')
        self.customer_api_key = db.create_key('customer-api-key', customer='Foo', type='read-write', text='demo-key')

    def tearDown(self):

        pass

    def test_suppress_alerts(self):

        self.headers = {
            'Authorization': 'Key %s' % self.admin_api_key,
            'Content-type': 'application/json'
        }

        # create alert
        response = self.app.post('/alert', data=json.dumps(self.alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)

        # create blackout
        response = self.app.post('/blackout', data=json.dumps({"environment": "Production"}), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))

        blackout_id = data['blackout']

        # suppress alert
        response = self.app.post('/alert', data=json.dumps(self.alert), headers=self.headers)
        self.assertEqual(response.status_code, 202)

        self.headers = {
            'Authorization': 'Key %s' % self.customer_api_key,
            'Content-type': 'application/json'
        }

        # create alert
        response = self.app.post('/alert', data=json.dumps(self.alert), headers=self.headers)
        self.assertEqual(response.status_code, 202)


        self.headers = {
            'Authorization': 'Key %s' % self.admin_api_key,
            'Content-type': 'application/json'
        }

        response = self.app.delete('/blackout/' + blackout_id, headers=self.headers)
        self.assertEqual(response.status_code, 200)
