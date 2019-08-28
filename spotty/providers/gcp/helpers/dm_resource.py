from spotty.providers.gcp.helpers.dm_client import DMClient


class DMResource(object):

    def __init__(self, dm: DMClient, data: dict):
        """
        Args:
            dm (DMClient): Deployment Manager client
            data (dict): Stack info.
                Example #1:
                {'id': '1760655646875625396',
                 'insertTime': '2019-08-25T16:27:23.544-07:00',
                 'name': 'x11-test-i2-docker-waiter',
                 'type': 'runtimeconfig.v1beta1.waiter',
                 'update': {'finalProperties': 'failure:\n'
                                               '  cardinality:\n'
                                               '    number: 1\n'
                                               '    path: /failure\n'
                                               'parent: '
                                               'projects/spotty-221422/configs/x11-test-i2-docker-status\n'
                                               'success:\n'
                                               '  cardinality:\n'
                                               '    number: 1\n'
                                               '    path: /success\n'
                                               'timeout: 1800s\n'
                                               'waiter: x11-test-i2-docker-waiter\n',
                            'intent': 'CREATE_OR_ACQUIRE',
                            'manifest': 'https://www.googleapis.com/deploymentmanager/v2/projects/spotty-221422/global/deployments/spotty-instance-x11-test-i2/manifests/manifest-1566775635906',
                            'properties': 'failure:\n'
                                          '  cardinality:\n'
                                          '    number: 1\n'
                                          '    path: /failure\n'
                                          'parent: $(ref.x11-test-i2-docker-status.name)\n'
                                          'success:\n'
                                          '  cardinality:\n'
                                          '    number: 1\n'
                                          '    path: /success\n'
                                          'timeout: 1800s\n'
                                          'waiter: x11-test-i2-docker-waiter\n',
                            'state': 'IN_PROGRESS'},
                 'updateTime': '2019-08-25T16:27:23.544-07:00'}

                Example #2:
                {'finalProperties': 'config: x11-test-i2-docker-status\n'
                                    'description: Docker status\n',
                 'id': '314866945194106123',
                 'insertTime': '2019-08-25T17:12:20.140-07:00',
                 'manifest': 'https://www.googleapis.com/deploymentmanager/v2/projects/spotty-221422/global/deployments/spotty-instance-x11-test-i2/manifests/manifest-1566778333272',
                 'name': 'x11-test-i2-docker-status',
                 'properties': 'config: x11-test-i2-docker-status\n'
                               'description: Docker status\n',
                 'type': 'runtimeconfig.v1beta1.config',
                 'updateTime': '2019-08-25T17:12:30.254-07:00',
                 'url': 'https://runtimeconfig.googleapis.com/v1beta1/projects/spotty-221422/configs/x11-test-i2-docker-status'}
        """
        self._dm = dm
        self._data = data

    @staticmethod
    def get_by_name(dm: DMClient, deployment_name: str, resource_name: str):
        """Returns an instance by its stack name."""
        res = dm.get_resource(deployment_name, resource_name)
        if not res:
            return None

        return DMResource(dm, res)

    @property
    def is_created(self) -> bool:
        return 'finalProperties' in self._data

    @property
    def error_message(self) -> str:
        if 'error' not in self._data.get('update', {}):
            return None

        return self._data['update']['error']['errors'][0]['message']

    @property
    def state(self) -> str:
        return self._data['update']['state'] if 'state' in self._data.get('update', {}) else None

    @property
    def is_in_progress(self) -> bool:
        return self.state == 'IN_PROGRESS'

    @property
    def is_failed(self) -> bool:
        # an error occurred or the resource is in an unexpected status
        return self.error_message or (self.state is not None and
                                      self.state not in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'IN_PREVIEW'])
