from datetime import datetime
from spotty.deployment.abstract_cloud_instance.resources.abstract_instance import AbstractInstance
from spotty.providers.gcp.helpers.ce_client import CEClient


class Instance(AbstractInstance):

    def __init__(self, ce: CEClient, data: dict):
        """
        Args:
            data (dict): Example:
               {'canIpForward': False,
                'cpuPlatform': 'Intel Haswell',
                'creationTimestamp': '2019-04-20T16:21:49.536-07:00',
                'deletionProtection': False,
                'description': '',
                'disks': [{'autoDelete': True,
                           'boot': True,
                           'deviceName': 'instance-1',
                           'guestOsFeatures': [{'type': 'VIRTIO_SCSI_MULTIQUEUE'}],
                           'index': 0,
                           'interface': 'SCSI',
                           'kind': 'compute#attachedDisk',
                           'licenses': ['https://www.googleapis.com/compute/v1/projects/debian-cloud/global/licenses/debian-9-stretch'],
                           'mode': 'READ_WRITE',
                           'source': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b/disks/instance-1',
                           'type': 'PERSISTENT'}],
                'id': '928537266896639843',
                'kind': 'compute#instance',
                'labelFingerprint': '42WmSpB8rSM=',
                'machineType': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b/machineTypes/n1-standard-1',
                'metadata': {'fingerprint': 'IoRxXrApBlw=',
                             'kind': 'compute#metadata'},
                'name': 'instance-1',
                'networkInterfaces': [{'accessConfigs': [{'kind': 'compute#accessConfig',
                                                          'name': 'External NAT',
                                                          'natIP': '34.73.140.188',
                                                          'networkTier': 'PREMIUM',
                                                          'type': 'ONE_TO_ONE_NAT'}],
                                       'fingerprint': 'COAWpxIgZx0=',
                                       'kind': 'compute#networkInterface',
                                       'name': 'nic0',
                                       'network': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/global/networks/default',
                                       'networkIP': '10.142.0.2',
                                       'subnetwork': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/regions/us-east1/subnetworks/default'}],
                'scheduling': {'automaticRestart': False,
                               'onHostMaintenance': 'TERMINATE',
                               'preemptible': True},
                'selfLink': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b/instances/instance-1',
                'serviceAccounts': [{'email': '293101887402-compute@developer.gserviceaccount.com',
                                     'scopes': ['https://www.googleapis.com/auth/devstorage.read_only',
                                                'https://www.googleapis.com/auth/logging.write',
                                                'https://www.googleapis.com/auth/monitoring.write',
                                                'https://www.googleapis.com/auth/servicecontrol',
                                                'https://www.googleapis.com/auth/service.management.readonly',
                                                'https://www.googleapis.com/auth/trace.append']}],
                'startRestricted': False,
                'status': 'RUNNING',
                'tags': {'fingerprint': '42WmSpB8rSM='},
                'zone': 'https://www.googleapis.com/compute/v1/projects/spotty-221422/zones/us-east1-b'}
        """
        self._ce = ce
        self._data = data

    @staticmethod
    def get_by_name(ce: CEClient, machine_name: str):
        """Returns an instance by its stack name."""
        res = ce.list_instances(machine_name)
        if not res:
            return None

        return Instance(ce, res[0])

    @property
    def name(self) -> str:
        return self._data['name']

    @property
    def is_running(self) -> bool:
        return self.status == 'RUNNING'

    @property
    def is_stopped(self) -> bool:
        # see Instance Life Cycle: https://cloud.google.com/compute/docs/instances/instance-life-cycle
        return self.status == 'TERMINATED'

    @property
    def public_ip_address(self) -> str:
        return self._data['networkInterfaces'][0]['accessConfigs'][0].get('natIP')

    @property
    def status(self) -> str:
        return self._data['status']

    @property
    def machine_type(self) -> str:
        return self._data['machineType'].split('/')[-1]

    @property
    def zone(self) -> str:
        return self._data['zone'].split('/')[-1]

    @property
    def creation_timestamp(self) -> datetime:
        # fix the format: '2019-04-20T16:21:49.536-07:00' -> '2019-04-20T16:21:49-0700'
        time_str = self._data['creationTimestamp'][:-10] + \
                   self._data['creationTimestamp'][-6:-3] + \
                   self._data['creationTimestamp'][-2:]
        return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S%z')

    @property
    def is_preemtible(self) -> bool:
        return self._data['scheduling']['preemptible']

    def terminate(self, wait: bool = True):
        self._ce.delete_instance(self.name, wait)

    def stop(self, wait: bool = True):
        self._ce.stop_instance(self.name, wait)
