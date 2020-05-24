"""A `dowel.logger.LogOutput` for CSV files."""
import csv
import os
import shutil
import tempfile

from dowel import TabularInput
from dowel.simple_outputs import FileOutput
from dowel.utils import colorize


class CsvOutput(FileOutput):
    """CSV file output for logger.

    :param file_name: The file this output should log to.
    """

    def __init__(self, file_name):
        super().__init__(file_name)
        self._writer = None
        self._fieldnames = None

    @property
    def types_accepted(self):
        """Accept TabularInput objects only."""
        return (TabularInput, )

    def record(self, data, prefix=''):
        """Log tabular data to CSV."""
        if isinstance(data, TabularInput):
            to_csv = data.as_primitive_dict

            if not to_csv.keys() and not self._writer:
                return

            if not self._writer:
                self._fieldnames = list(to_csv.keys())
                self._writer = csv.DictWriter(
                    self._log_file,
                    fieldnames=self._fieldnames,
                    extrasaction='ignore')
                self._writer.writeheader()

            if to_csv.keys() != self._fieldnames:
                new_keys = set(to_csv.keys()).difference(self._fieldnames)
                if new_keys:
                    # Move to beginning of log file 
                    self._log_file.seek(0)
                    # self._fieldnames = self._fieldnames.union(new_keys)
                    self._fieldnames += list(new_keys)
                    # Write corrected lines with new keyto a temporary file
                    temp_dir = os.path.dirname(self._log_file.name)
                    temp_file = tempfile.NamedTemporaryFile('w+', dir=temp_dir)
                    temp_writer = csv.DictWriter(
                        temp_file,
                        fieldnames=self._fieldnames)
                    temp_writer.writeheader()

                    # Skip header and read first line of data into line
                    self._log_file.readline()
                    line = self._log_file.readline()
                    while line:
                        # don't copy over old newline char and insert \n at end
                        temp_file.write(line[:-1] + (','*len(new_keys)) + '\n')
                        line = self._log_file.readline()

                    # Copy from temp file to log file 
                    self._log_file.seek(0)
                    temp_file.seek(0)
                    shutil.copyfileobj(temp_file, self._log_file)
                    temp_file.close()

            # fieldnames have been updated if necessary in if. Handles missing
            # fieldnames with default restval=''
            self._writer.writerow(to_csv)

            for k in to_csv.keys():
                data.mark(k)

            # Necessary to ensure old values aren't repeated for missing keys
            data.clear()
        else:
            raise ValueError('Unacceptable type.')
