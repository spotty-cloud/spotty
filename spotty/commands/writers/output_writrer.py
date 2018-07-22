from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class OutputWriter(AbstractOutputWriter):

    def write(self, msg: str):
        """Prints messages to STDOUT."""
        print(msg, flush=True)
