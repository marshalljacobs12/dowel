"""A `dowel.logger.LogOutput` for CSV files."""
import csv
import tempfile
# import warnings

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
                self._fieldnames = set(to_csv.keys())
                self._writer = csv.DictWriter(
                    self._log_file,
                    fieldnames=self._fieldnames,
                    extrasaction='ignore')
                self._writer.writeheader()

            if to_csv.keys() != self._fieldnames:

                new_keys = set(to_csv.keys()).difference(self._fieldnames)
                if new_keys:
                    """ Move to beginning of log file """
                    self._log_file.seek(0)
                    reader = csv.DictReader(
                        self._log_file, 
                        fieldnames=self._fieldnames)

                    self._fieldnames = self._fieldnames.union(new_keys)

                    """ Write corrected lines with new keyto a temporary file """
                    temp_file = tempfile.NamedTemporaryFile('w+', dir='.')
                    temp_writer = csv.DictWriter(
                        temp_file,
                        fieldnames=self._fieldnames)
                    temp_writer.writeheader()

                    """ Skip header """
                    next(reader)
                    for row in reader:
                        for k in new_keys:
                            row[k] = ''
                        temp_writer.writerow(row)

                    """ Delete log file contents """
                    self._log_file.truncate(0)
                    self._log_file.seek(0)

                    """ Read from temp file and write to log file """
                    temp_file.seek(0)
                    temp_reader = csv.DictReader(
                        temp_file,
                        fieldnames=self._fieldnames)

                    """ need to update fieldnames """
                    self._writer = csv.DictWriter(
                        self._log_file,
                        fieldnames=self._fieldnames)

                    """ Write headers to log file """
                    self._writer.writeheader()

                    """ Advance passed headers """
                    next(temp_reader)
                    for row in temp_reader:
                        self._writer.writerow(row)

                    """ Write new entry """
                    self._writer.writerow(to_csv)

                missing_keys = self._fieldnames.difference(set(to_csv.keys()))
                if missing_keys:
                    """ Insert blank values for missing keys """
                    for k in missing_keys:
                        to_csv[k] = ''
                    self._writer.writerow(to_csv)

            else:
                self._writer.writerow(to_csv)

            for k in to_csv.keys():
                data.mark(k)

            """ Necessary to ensure old values aren't repeated for missing keys """
            data.clear()
        else:
            raise ValueError('Unacceptable type.')
