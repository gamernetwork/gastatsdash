Scheduling Reports
===================

.. _using-scheduler:

Using the scheduler
--------------------

Scheduler's work flow in pseudo code ::

    for report in report_schedule.reports:
        last_run = get_last_run_from_database(report.identifier)
        next_run = get_next_run(last_run)
        if next_run <= date.today():
	    data_available = report.get_data_available()
	    if data_available == True:
                report.run()
	    else:
		continue
        else:
            continue

To test a schedule run without generating reports or storing dates use this command ::

    python scheduler.py --test

The scheduler is set up as a singleton. This is because if you set a cron to run the scheduler every hour, there is a chance the reports may take longer than an hour to generate. If this happens, you don't want the cron to start another instance of the scheduler to potentially re-run the report and take up memory. The singleton instance means it will quit immediately if there is already an instance running.

Data Availability
++++++++++++++++++

Often with analytics services data is not ready to be queried immediately, so we make checks for when the data is available.

For example, Google Analytics has a `processing latency <https://support.google.com/analytics/answer/1070983?hl=en>`_ of 24-48 hours.

This can mean reports will want to send when the data isn't ready. We have a check set up to make reports wait until the data is ready.

Each analytics class has a data availability check function set up. See :ref:`youtube <youtube-data-available>` and :ref:`ga <ga-data-available>` reference.


Errors
+++++++

This class creates a list of errors when the scheduler is run, i.e. when the report is being overridden and errors are thrown from generating the report.

These errors can then be emailed to relevant parties to notify of an issue immediately.

Schedule Database 
------------------

Report run dates are stored in SQLite database ``schedule.db``

   The date that is stored is the **period end date**. *Not* the date the report was run.

Run Logger
++++++++++

The *RunLogger* class defines functions that connect to the database and retrieve the data about when the reports have last been run and uses this to find when the report should be run next.

get_next_run() 
    | Calculates when the report should run next
    | Dependent on the frequency of the report and when it ran last
    | Also sets the override to True if the next run is set to be over 2 days ago




