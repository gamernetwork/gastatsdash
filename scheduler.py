from datetime import date, datetime, timedelta
from sqlite3 import OperationalError
from tendo import singleton
import argparse
import logging, logging.config, logging.handlers
import os
import sqlite3
import sys
import traceback

from Statsdash import config
from Statsdash.config import LOGGING
from Statsdash.mailer import send_email
from Statsdash.report_schedule import reports
from Statsdash.stats_range import StatsRange
from Statsdash.utils import Frequency
from Statsdash.utils.date import add_one_month, find_next_weekday


class RunLogger:
    """
    Persistence layer for recording the last run of a report and querying
    whether a report can be run now, given a reporting frequency.
    """
    override_data = False
    
    def __init__(self):
        """
        Build `report_runs` table if it doesn't already exist.
        """
        db_location = os.path.join(config.SCHEDULE_DB_LOCATION, 'schedule.db')
        self.conn = sqlite3.connect(db_location)
        try:
            # Check if the `report_runs` table exists.
            self.conn.execute('SELECT * FROM report_runs LIMIT 1')
        except OperationalError:
            # Build `report_runs` table if it doesn't exist.
            self.bootstrap_db()

    def bootstrap_db(self):
        self.conn.execute(
            'CREATE TABLE report_runs ' +
            '(identifier text unique, last_run datetime)'
        )

    def get_last_run_end(self, identifier):
        """
        Get the datetime of the end of the last run of a report given a unique 
        identifier.

        Yields datetime(1,1,1) if a report with that identifier has never been 
        recorded.
        """
        print(identifier)
        c = self.conn.cursor()
        c.execute(
            f'SELECT last_run FROM report_runs WHERE identifier="{identifier}"'
        )
        result = c.fetchone()
        if result:
            last_run = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
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
            'INSERT OR REPLACE INTO report_runs VALUES (?, ?)',
            (identifier, run_datetime)
        )
        self.conn.commit()

    # TODO clean up this method
    def get_next_run(self, last_run_end, frequency, frequency_options={}):
        """
        When should the report run next.
        Returns a Date object
        last_run_end == report end date
        """
        today = date.today() - timedelta(days=1)
        now = datetime(today.year, today.month, today.day, 00)

        if last_run_end.year == 1:
            if frequency in [Frequency.DAILY, Frequency.WOW_DAILY]:
                return now
            if frequency == Frequency.WEEKLY:
                weekday = frequency_options.get('weekday', 'Monday')
                return find_next_weekday(now, weekday)
            if frequency in {Frequency.MONTHLY, Frequency.YOY_MONTHLY}:
                day = frequency_options.get('day', 1)
                next_run = datetime(day=day, month=now.month, year=now.year)
                if next_run < now:
                    next_run = add_one_month(next_run)
                return next_run

        if frequency in [Frequency.DAILY, Frequency.WOW_DAILY]:
            #if last period end was over 2 days ago, set to yesterday
            next_run = last_run_end + timedelta(days=1)
            if (now - last_run_end).days >= 2:
                # NOTE why is this set to True?
                self.override_data = True
        if frequency == Frequency.WEEKLY:
            weekday = frequency_options.get('weekday', 'Monday')
            # Next run is the next matching weekday *after* the last run
            # So if we run every Monday, our last_run_end will be on a Sunday - 
            #   so add one day
            next_run = find_next_weekday(last_run_end + timedelta(days=1), weekday, force_future=True)
        if frequency in {Frequency.MONTHLY, Frequency.YOY_MONTHLY}:
            day = frequency_options.get('day')
            #add one day to last_run_end to get the first day of next month period
            next_run = last_run_end + timedelta(days=1) 
            #needs to run at the end of the next period, so add one month
            next_run = add_one_month(next_run)
            #make sure set to be correct day 
            next_run = next_run.replace(day=day) 
            if (now - next_run).days >= 2:
                self.override_data = True

        return next_run


class Errors:

    errors = []

    def get_errors(self):
        """
        Return list of current errors
        """
        return self.errors
    
    def add_error(self, error):
        """
        Add to list of errors
        """
        self.errors.append(error)
        
    def send_errors(self):
        """
        Send html email using config parameters
        """
        message = '\n'.join(self.errors)
        subject = 'Statsdash Errors'
        send_from = config.SEND_FROM
        recipients = config.ERROR_REPORTER
        send_email(None, message, subject, send_from, recipients)


def _run(dryrun=False):
    """
    The main loop.  Iterate over our report config and try to run reports that
    are scheduled to run now.
    """
    try:
        singleton.SingleInstance()
    except SystemExit:
        print("** Quitting run at %s" % datetime.now().isoformat())
        sys.exit(-1)
        
    run_logger = RunLogger()
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger('report')

    for report_conf in reports:
        identifier = report_conf['identifier']
        frequency = report_conf['frequency']

        frequency_options = report_conf.get('frequency_options', {})

        last_run_end = run_logger.get_last_run_end(identifier)
        next_run_date = run_logger.get_next_run(last_run_end, frequency, frequency_options).date()

        today = date.today()
        needs_run = next_run_date <= today
        print("%s next run: %s.  Needs run: %s" % (identifier, next_run_date, needs_run))

        if needs_run:
            period = StatsRange.get_period(next_run_date, frequency)
            # Create report instance with given period.
            report = report_conf['report'](report_conf['sites'], period, report_conf['frequency'], report_conf['subject'])
            if run_logger.override_data:
                data_available = True
                no_data_site = report.check_data_availability()
                logger.warning("Overriding data availability and sending report anyway")
                error_list.add_error("There is no data, or a lack of data available for the site: %s between %s - %s. This is being overridden to send the report %s anyway." % (no_data_site, period.start_date, period.end_date, identifier))

            else:
                data_available = report.check_data_availability()
            
            run_logger.override_data = False
            print("%s next run: %s.  Data available: %s" % (
            identifier, next_run_date, data_available))
            if dryrun:
                print("last run's end %s" % (last_run_end))
                print("period for run: %s - %s" % (
                period.start_date, period.end_date))
            if data_available:
                try:
                    if not dryrun:
                        html = report.generate_html()
                        send_email(html, '', report.subject, config.SEND_FROM, report_conf['recipients'], report.img_data)
                        run_datetime = datetime(
                            year=report.period.end_date.year,
                            month=report.period.end_date.month,
                            day=report.period.end_date.day,
                            hour=0,
                            minute=0,
                            second=0,
                            microsecond=1
                        )
                        run_logger.record_run(identifier, run_datetime)
                except Exception:
                    print("Error in generating report %s" % identifier)
                    error_list.add_error("Error in generating report %s : \n %s" % (identifier, traceback.format_exc()))
                    traceback.print_exc()
                    continue


def run_schedule(dryrun=False):
    print("** Running schedule at %s" % datetime.now().isoformat())
    try:
        _run(dryrun)
    except Exception:
        traceback.print_exc()
    print("** Finished run at %s" % datetime.now().isoformat())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="test run", action="store_true")
    args = parser.parse_args()
    error_list = Errors()
    
    if args.test:
        print("**Dry Run**")
    run_schedule(args.test)
    
    if error_list.get_errors():
        error_list.send_errors()
