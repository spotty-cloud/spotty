from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.helpers.dm_client import DMClient


class ImageStack(object):

    def __init__(self, dm: DMClient):
        self._dm = dm

    def create_stack(self, deployment, output: AbstractOutputWriter):
        """Creates GCP deployment."""
        pass
