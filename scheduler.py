import sqlite3, os, traceback


from sqlite3 import OperationalError
from datetime import date, datetime, timedelta

import Statsdash.config as config
from Statsdash.report_schedule import reports
from Statsdash.report import AnalyticsCoreReport, AnalyticsSocialReport, YoutubeReport, AnalyticsSocialExport
import Statsdash.utilities as utils
from Statsdash.utilities import find_last_weekday, add_one_month, find_next_weekday

from Statsdash.config import LOGGING
import logging, logging.config, logging.handlers

class RunLogger(object):
    """
    Persistence layer for recording the last run of a report and querying
    whether a report can be run now, given a reporting frequency.
    """
    override_data = False
    
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

    def get_next_run(self, last_run, frequency, frequency_options={}):
        """
        When should the report run next.
        Returns a Date object
        last_run == report end date
        """
        today = date.today() - timedelta(days=1)
        now = datetime(today.year, today.month, today.day, 00, 00, 00, 01)  #returns now as datetime with time as 00 00 00 00001
        last_period_end = last_run
        
        if last_period_end.year == 1:
            if frequency == 'DAILY' or frequency == "WOW_DAILY":
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
       
        if frequency == 'DAILY' or frequency == "WOW_DAILY":
            #if last run was over 2 days ago, set to yesterday 
            next_run = last_period_end + timedelta(days=1)
            if (now - last_period_end).days >= 2:
              self.override_data = True
        if frequency == 'WEEKLY':
            next_run = last_period_end + timedelta(days=7)
        if frequency == 'MONTHLY':
            day = frequency_options.get("day")
            #add one day to last_period_end to get the first day of next month period 
            next_run = last_period_end + timedelta(days=1) 
            #needs to run at the end of the next period, so add one month
            next_run = add_one_month(last_period_end)
            #make sure set to be correct day 
            next_run = next_run.replace(day=day) 
            if (now - next_run).days >= 2:
              self.override_data = True

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
        last_run = run_logger.get_last_run(identifier)
        next_run_date = run_logger.get_next_run(last_run, frequency, frequency_options).date()
        today = date.today()
        needs_run = next_run_date <= today
        print "%s next run: %s.  Needs run: %s" % (identifier, next_run_date, needs_run)
        if needs_run:
            period = utils.StatsRange.get_period(next_run_date, frequency)
            report = config["report"](config["sites"], period, config["recipients"], config["frequency"], config["subject"])  
            if run_logger.override_data == True:
                data_available = report.check_data_availability(override=True)
                logger.warning("Overriding data availability and sending report anyway")
            else:
                data_available = report.check_data_availability()
            
            run_logger.override_data = False
            print "%s next run: %s.  Data available: %s" % (identifier, next_run_date, data_available)
            
            if data_available:
                html = report.generate_html()
                report.send_email(html)
                run_datetime = datetime(year=report.period.end_date.year, 
                    month=report.period.end_date.month, 
                    day=report.period.end_date.day,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=1
                )           
                run_logger.record_run(identifier, run_datetime)
            


"""
def _run():

    run_logger = RunLogger()
    
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger('report')

    for config in reports:
        identifier = config['identifier']
        frequency = config['frequency']
        frequency_options = config.get('frequency_options', {})
        report_class = config['report']
        last_run = run_logger.get_last_run(identifier)
        next_run_date = run_logger.get_next_run(last_run, frequency, frequency_options).date()
        today = date.today()
        needs_run = next_run_date <= today
        print "%s next run: %s.  Needs run: %s" % (identifier, next_run_date, needs_run)
        if needs_run:
            report = create_report(report_class, config, next_run_date)
            if run_logger.override_data == True:
                data_available = report.data_available(override=True)
                print "overriding data available", run_logger.override_data
                logger.warning("overriding data available and sending report anyway")
            else:
                data_available = report.data_available()

            run_logger.override_data = False
            print "%s next run: %s.  Data available: %s" % (identifier, next_run_date, data_available)
            if data_available:
            
                #if data available
                #try send report
                #except exeptioin
                #print/log exception
                #continue to next report
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

"""

def run_schedule():
    print "** Running schedule at %s" % datetime.now().isoformat()
    try:
        _run()
    except Exception:
        traceback.print_exc()
    print "** Finished run at %s" % datetime.now().isoformat()

if __name__ == '__main__':

    run_schedule()
