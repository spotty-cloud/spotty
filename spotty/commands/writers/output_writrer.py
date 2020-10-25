from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class OutputWriter(AbstractOutputWriter):

    def _write(self, msg: str, newline: bool = True):
        """Prints messages to STDOUT."""
        print(msg, end=('\n' if newline else ''), flush=True)
