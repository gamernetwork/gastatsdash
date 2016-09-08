Reports
=======

Overview
--------
The main function of the program is to aggregate and display the data in helpful html reports.
For each new report type there is a specific report class that inherits from the base Report class. 

Report Class
------------

The report class defines what each report contains. 
The parent class defines some base functions that all reports use:
get_subject() 
	creates the subject of the email, which is also the title of the report using the frequency and period variables.

get_freq_label()
	Creates a string to be used in templates for appearances. I.e. is the comparison WoW or MoM

check_data_availability()
	calls through to analytics. Returns true if data is available, false if not. If override is set to true, then it returns the name of the sites that have no data and must be overridden. 

send_email()
	simple function to send the html email.

Each child report class must define they're individual "generate_html" function which calculates and passes the data to the templates.


Templates
--------
Jinja 2


Add a new report
---------------

- new class



Run a report
------------

- preview report
- scheduler


 




