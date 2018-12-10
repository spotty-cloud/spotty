from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class NullOutputWriter(AbstractOutputWriter):

    def _write(self, msg: str):
        """Does nothing."""
        pass
