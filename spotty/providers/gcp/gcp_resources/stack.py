import logging
from time import sleep
from httplib2 import ServerNotFoundError
from spotty.providers.gcp.helpers.dm_client import DMClient


class Stack(object):

    def __init__(self, dm: DMClient, data: dict):
        """
        Args:
            dm (DMClient): Deployment Manager client
            data (dict): Stack info. Example:
               {'fingerprint': 'vvtbwT7F953T0YC9tQ9CUg==',
                'id': '3128259442476717093',
                'insertTime': '2019-04-20T16:27:06.739-07:00',
                'name': 'spotty-instance-x11-test-i2',
                'operation': {'endTime': '2019-04-20T16:27:23.141-07:00',
                              'error': {'errors': [{'code': 'RESOURCE_ERROR',
                                                    'location': '/deployments/spotty-instance-x11-test-i2/resources/spotty-instance-x11-test-i2-disk-1',
                                                    'message': '{"ResourceType":"compute.v1.disk","ResourceErrorCode":"400","ResourceErrorMessage":{"code":400,"errors":[{"domain":"global","location":"zone","locationType":"parameter","message":"Invalid '
                                                               "value 'zones/us-east1-b'. "
                                                               'Values must match the '
                                                               'following regular expression: '
                                                               '\'[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?\'","reason":"invalidParameter"}],"message":"Invalid '
                                                               "value 'zones/us-east1-b'. "
                                                               'Values must match the '
                                                               'following regular expression: '
                                                               '\'[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?\'","statusMessage":"Bad '
                                                               'Request","requestPath":"https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/zones%2Fus-east1-b/disks","httpMethod":"POST"}}'}]},
                              'httpErrorMessage': 'BAD REQUEST',
                              'httpErrorStatusCode': 400,
                              'id': '1965130840716743717',
                              'insertTime': '2019-04-20T16:27:06.900-07:00',
                              'kind': 'deploymentmanager#operation',
                              'name': 'operation-1555802826515-586fe92d0a605-6166491c-7051043e',
                              'operationType': 'insert',
                              'progress': 100,
                              'selfLink': 'https://www.googleapis.com/deploymentmanager/v2/projects/spotty-221422/global/operations/operation-1555802826515-586fe92d0a605-6166491c-7051043e',
                              'startTime': '2019-04-20T16:27:06.908-07:00',
                              'status': 'DONE',
                              'targetId': '3128259442476717093',
                              'targetLink': 'https://www.googleapis.com/deploymentmanager/v2/projects/spotty-221422/global/deployments/spotty-instance-x11-test-i2',
                              'user': 'spotty@spotty-221422.iam.gserviceaccount.com'},
                'selfLink': 'https://www.googleapis.com/deploymentmanager/v2/projects/spotty-221422/global/deployments/spotty-instance-x11-test-i2',
                'update': {'manifest': 'https://www.googleapis.com/deploymentmanager/v2/projects/spotty-221422/global/deployments/spotty-instance-x11-test-i2/manifests/manifest-1555802826772'},
                'updateTime': '2019-04-20T16:27:23.107-07:00'}
        """
        self._dm = dm
        self._data = data

    @staticmethod
    def get_by_name(dm: DMClient, deployment_name: str):
        """Returns an instance by its stack name."""
        res = dm.get(deployment_name)
        if not res:
            return None

        return Stack(dm, res)

    @staticmethod
    def create(dm: DMClient, deployment_name: str, template: str):
        return dm.deploy(deployment_name, template)

    @property
    def name(self) -> str:
        return self._data['name']

    @property
    def status(self) -> str:
        return self._data.get('operation', {}).get('status')

    @property
    def is_running(self):
        return self.status == 'RUNNING'

    @property
    def is_done(self):
        """A deployment has the done status when it's successfully created or failed."""
        return self.status == 'DONE'

    @property
    def error(self) -> str:
        """Returns an error in the format: {'code': '...', 'message': '...'}."""
        return self._data.get('operation', {}).get('error', {}).get('errors', [None])[0]

    @property
    def fingerprint(self) -> str:
        return self._data['fingerprint']

    def stop(self):
        self._dm.stop(self.name, self.fingerprint)

    def delete(self):
        self._dm.delete(self.name)

    def wait_stack_deleted(self, delay=15):
        stack = True
        while stack:
            try:
                stack = self.get_by_name(self._dm, self.name)
            except (ConnectionResetError, ServerNotFoundError):
                logging.warning('Connection problem')
                continue

            sleep(delay)

    def wait_stack_done(self, delay=5):
        is_done = False
        while not is_done:
            try:
                stack = self.get_by_name(self._dm, self.name)
                is_done = stack.is_done
            except (ConnectionResetError, ServerNotFoundError):
                logging.warning('Connection problem')
                continue

            sleep(delay)
