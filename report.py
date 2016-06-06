from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from render import get_environment

import config
from Youtube.aggregate_data import YoutubeData

class Report(object):
    #template = "Templates/base.html"
    """
    Report object
    Gathers data from analytics, renders and sends as an email
    """
	def __init__(self, channels, start, end, recipients, frequency, subject):
		self.channels = channels
		self.start = start
		self.end = end
		self.recipients = recipients
		self.frequency = frequency
		self.subject = subject
		
		env = get_environment()
		self.template = env.get_template("base.html")
        
	def get_subject(self):
    	"""
    	Return the subject of the email that includes the dates for this period
    	"""
		if self.frequency == 'daily':
			subject = ' '.join([self.subject, self.end.strftime("%a %d %b %Y")])
		elif self.frequency  == 'weekly':
			weekly_date = self.start.strftime("%a %d %b %Y") + ' - ' + self.end.strftime("%a %d %b %Y")
			subject = ' '.join([self.subject, weekly_date])
		elif self.frequency == 'monthly':
			subject = ' '.join([self.subject, self.start.strftime('%B %Y')])
		return subject
		
    def get_freq_label(self):
        """
        Returns label for the period of change 
        E.g. where frequency == "monthly", label == "MoM"
        """
        first_letter = self.frequency[0].upper()
        label = first_letter + "o" + first_letter
        return label
    

    def generate_html(self):
		"""
		Get formatted data and render to template
		"""
	
		html = self.template.render()
		return html        

	def send_email(self, html):
		"""
		Send html email using config parameters
		"""
		msg = MIMEMultipart('alternative')
		msg.set_charset('utf8')
		msg['Subject'] = self.subject
		msg['From'] = config.SEND_FROM
		msg['To'] = self.recipients
		text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
		html_part = MIMEText(html.encode("utf-8"), 'html')

		msg.attach(text_part)
		msg.attach(html_part)

		sender = smtplib.SMTP(config.SMTP_ADDRESS)
		sender.sendmail(config.SEND_FROM, self.recipients, msg.as_string())
		sender.quit()


class YoutubeReport(Report):
    
	def __init__(self, channels, start, end, recipients, frequency, subject):
		super(NetworkYoutubeReport, self).__init__(channels, start, end, recipients, frequency, subject)
		self.data = YoutubeData(self.channels, self.start, self.end)
		#check = self.data.check_available_data()
		#if not check['result']:
			#raise Exception("Data not available for %s" % check['channel'])
		
    def check_data_availability(self, override=False):
        """
        incomplete
        - could this be in main report
        - does it need override or in scheduler should it only be called if override is false? 
        - is there a better way than a function to call a function??
        """
		if override:
		    return True
        else:
            check = self.data.check_available_data()
    		if check['result']:
    			return True
            else:
                return False
	
	def generate_html(self):

		tableone = self.data.get_summary_table()
		tabletwo = self.data.get_stats_table()
		tablethree = self.data.get_geo_table()
		tablefour = self.data.get_top_videos_table()
		tablefive = self.data.get_traffic_source_table()
	
		html = self.template.render(
			subject=self.get_subject(),
			change=self.get_freq_label(),
			summary_table=tableone,
			stats_table=tabletwo,
			geo_table=tablethree,
			top_vids=tablefour,
			traffic=tablefive,		
		
		)
		return html			    

class AnalyticsCoreReport(Report):
    
 	def __init__(self, channels, start, end, recipients, frequency, subject):
		super(NetworkYoutubeReport, self).__init__(channels, start, end, recipients, frequency, subject)
		self.data = AnalyticsData(self.channels, self.start, self.end)

			
class AnalyticsSocialReport(Report):
    
 	def __init__(self, channels, start, end, recipients, frequency, subject):
		super(NetworkYoutubeReport, self).__init__(channels, start, end, recipients, frequency, subject)
		self.data = AnalyticsData(self.channels, self.start, self.end)    
		
		
		
		
		
		
		
		
		
		
