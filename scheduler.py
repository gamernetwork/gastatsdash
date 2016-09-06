import sqlite3, os, traceback

from sqlite3 import OperationalError
from datetime import date, datetime, timedelta
import argparse
import Statsdash.config as config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

import Statsdash.config as config
from Statsdash.report_schedule import reports
from Statsdash.report import AnalyticsCoreReport, AnalyticsSocialReport, YoutubeReport, AnalyticsSocialExport
import Statsdash.utilities as utils
from Statsdash.utilities import find_last_weekday, add_one_month, find_next_weekday

from Statsdash.config import LOGGING
import logging, logging.config, logging.handlers
from tendo import singleton
import sys

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

    def get_next_run(self, last_period_end, frequency, frequency_options={}):
        """
        When should the report run next.
        Returns a Date object
        last_run == report end date
        """
        today = date.today() - timedelta(days=1)
        now = datetime(today.year, today.month, today.day, 00, 00, 00, 01)  #returns now as datetime with time as 00 00 00 00001
        
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
            #if last period end was over 2 days ago, set to yesterday 
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
            next_run = add_one_month(next_run)
            #make sure set to be correct day 
            next_run = next_run.replace(day=day) 
            if (now - next_run).days >= 2:
              self.override_data = True

        return next_run


class Errors(object):
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
        msg = MIMEMultipart('alternative')
        msg.set_charset('utf8')
        msg['Subject'] = "Statsdash Errors"
        msg['From'] = config.SEND_FROM
        msg['To'] = config.ERROR_REPORTER
        
        message = ""
        for error in self.errors:
            message += error + "\n"
        
        text_part = MIMEText(message, 'plain')      
        msg.attach(text_part)
        
        sender = smtplib.SMTP(config.SMTP_ADDRESS)
        sender.sendmail(config.SEND_FROM, config.ERROR_REPORTER, msg.as_string())
    
        sender.quit()  
            

def _run(dryrun=False):
    """
    The main loop.  Iterate over our report config and try to run reports that
    are scheduled to run now.
    """   
    try:
        me = singleton.SingleInstance()
    except SystemExit:
        print "** Quitting run at %s" % datetime.now().isoformat()   
        sys.exit(-1)
        
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
                data_available = True
                no_data_site = report.check_data_availability(override=True)
                logger.warning("Overriding data availability and sending report anyway")
                error_list.add_error("There is no data, or a lack of data available for the site: %s between %s - %s. This is being overridden to send the report %s anyway." % (no_data_site, period.start_date, period.end_date, identifier)))
            else:
                data_available = report.check_data_availability()
            
            run_logger.override_data = False
            print "%s next run: %s.  Data available: %s" % (identifier, next_run_date, data_available)
            if dryrun == True:
                print "last run %s" %(last_run)
                print "period for run: %s - %s" % (period.start_date, period.end_date)               
            if data_available:
                try:
                    if dryrun == False:
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
                except Exception:
                    print "Error in generating report %s" % identifier
                    error_list.add_error("Error in generating report %s : \n %s" % (identifier, traceback.format_exc()))
                    traceback.print_exc()
                    continue


def run_schedule(dryrun=False):
    print "** Running schedule at %s" % datetime.now().isoformat() 
    try:
        _run(dryrun)
    except Exception:
        traceback.print_exc()
    print "** Finished run at %s" % datetime.now().isoformat()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="test run", action="store_true")
    args = parser.parse_args()
    error_list = Errors()
    
    run_schedule(args.test)
    
    if error_list.get_errors():
        error_list.send_errors()
        
