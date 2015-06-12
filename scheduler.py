import sqlite3, os

from sqlite3 import OperationalError
from datetime import date, datetime

import config
from report_schedule import reports

class RunLogger(object):
    """
    Persistence layer for recording the last run of a report and querying
    whether a report can be run now, given a reporting frequency.
    """
    
    def __init__(self):
        db_location = os.path.join(config.SCHEDULE_DB_LOCATION, "schedule.db")
        self.conn = sqlite3.connect(db_location)
        try:
            self.conn.execute("SELECT * FROM report_runs LIMIT 1")
        except OperationalError:
            self.bootstrap_db()

    def bootstrap_db(self):
        self.conn.execute(
            "CREATE TABLE report_runs " +
                "(identifier text unique, last_run datetime)"
        )

    def get_last_run(self, identifier):
        """
        Get the last run of a report given a unique identifier.
        """
        c = self.conn.cursor()
        c.execute(
            "SELECT last_run FROM report_runs " +
                "WHERE identifier='%s'" % identifier
        )
        result = c.fetchone()
        if result:
            last_run = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f")
            return last_run
        return datetime(1, 1, 1)

    def record_run(self, identifier):
        """
        Record the last run of a report given its unique identifier.
        """
        c = self.conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO report_runs VALUES (?, ?)", 
            (identifier, datetime.now())
        )
        self.conn.commit()

    def needs_run(self, identifier, frequency):
        """
        Can we run the report given an identifier and frequency.
        """
        last_run = self.get_last_run(identifier)
        today = date.today()
        if frequency == 'DAILY':
            threshold = datetime(year=today.year, month=today.month, 
                day=today.day)
        return last_run < threshold


def run_schedule():
    """
    The main loop.  Iterate over our report config and try to run reports that
    are scheduled to run now.
    """
    run_logger = RunLogger()
    for config in reports:
        identifier = config['identifier']
        frequency = config['frequency']
        report = config['report']
        needs_run = run_logger.needs_run(identifier, frequency)
        if needs_run and report.data_available():
            report.send_report()
            run_logger.record_run(identifier)

if __name__ == '__main__':
    run_schedule()