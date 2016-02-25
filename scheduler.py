import sqlite3, os, traceback


from sqlite3 import OperationalError
from datetime import date, datetime, timedelta

import config
from config import LOGGING
from report_schedule import reports
from reporting import create_report
from dateutils import find_last_weekday, add_one_month, find_next_weekday

import logging, logging.config, logging.handlers


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

    def record_run(self, identifier, run_datetime=None):
        """
        Record the last run of a report given its unique identifier.
        """
        if not run_datetime:
            run_datetime = datetime.now()
        c = self.conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO report_runs VALUES (?, ?)", 
            (identifier, run_datetime)
        )
        self.conn.commit()

    def get_next_run(self, identifier, frequency, frequency_options={}):
        """
        When should the report run next.
        Returns a Date object
        """
        last_run = self.get_last_run(identifier)
        if last_run.year == 1:
            now = datetime.now() - timedelta(days=1)
            if frequency == 'DAILY':
                return now
            if frequency == 'WEEKLY':
                weekday = frequency_options.get('weekday', 'Monday')
                return find_next_weekday(now, weekday)
            if frequency == 'MONTHLY':
                day = frequency_options.get('day', 1)
                next_run = datetime(day=day, month=now.month, year=now.year)
                if next_run < now:
                    next_run = add_one_month(next_run)
                return next_run
        now = datetime.now() - timedelta(days=1)
        if frequency == 'DAILY':
        #if last run was over 2 days ago, set to yesterday 
            if (now - last_run).days >= 2:
              next_run = now  
            else:
              next_run = last_run + timedelta(days=1)     
        if frequency == 'WEEKLY':
            next_run = last_run + timedelta(days=7)
        if frequency == 'MONTHLY':
            next_run = add_one_month(last_run)
        return next_run


def _run():
    """
    The main loop.  Iterate over our report config and try to run reports that
    are scheduled to run now.
    """
    run_logger = RunLogger()
    
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger('report')

    for config in reports:
        identifier = config['identifier']
        frequency = config['frequency']
        frequency_options = config.get('frequency_options', {})
        report_class = config['report']
        next_run_date = run_logger.get_next_run(identifier, frequency, frequency_options).date()
        today = date.today()
        needs_run = next_run_date <= today
        print "%s next run: %s.  Needs run: %s" % (identifier, next_run_date, needs_run)
        if needs_run:
            report = create_report(report_class, config, next_run_date)
            data_available = report.data_available()
            print "%s next run: %s.  Data available: %s" % (identifier, next_run_date, data_available)
            if data_available:
                report.send_report()
                run_datetime = datetime(year=report.period.end_date.year, 
                    month=report.period.end_date.month, 
                    day=report.period.end_date.day,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=1
                ) 
                run_logger.record_run(identifier, run_datetime)

def run_schedule():
    print "** Running schedule at %s" % datetime.now().isoformat()
    try:
        _run()
    except Exception:
        traceback.print_exc()
    print "** Finished run at %s" % datetime.now().isoformat()

if __name__ == '__main__':
    run_schedule()
