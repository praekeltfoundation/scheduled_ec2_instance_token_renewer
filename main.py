import sys, os
import datetime
from botocore.utils import InstanceMetadataFetcher
from botocore.credentials import InstanceMetadataProvider
from apscheduler.schedulers.blocking import BlockingScheduler
from slack_webhook import Slack

def job(file_loc):
  scheduler.remove_job('job_id')
  scheduler.add_job(job, 'interval', id='job_id', seconds=credentials(file_loc), replace_existing=True)

# Read file contents for AWS EC2 Roles stored as Key-Value Pairs in the specified File location
def keys_read(file_loc):
  contents={}
  with open(file_loc,"r") as f:
    for i in f:
      key_value=i.split(":")
      contents[key_value[0].strip()]=key_value[1].strip()
  f.close()
  return (contents)

#Write to specified File location
def file_write(file_loc, file_contents):
  with open(file_loc, 'w') as f:
    for i in file_contents.keys():
      f.write( i + ": " +  file_contents[i] + '\n' )
  f.close()

def credentials(file_loc):
  if os.path.isfile(file_loc): # Delete any Credentials in the specified file location in order to write new credentials
    file = open(file_loc,"r+")
    file.truncate(0)
    file.close()
  now = datetime.datetime.utcnow() # Get UTC Time Now
  provider = InstanceMetadataProvider(iam_role_fetcher=InstanceMetadataFetcher(timeout=1000, num_attempts=2))
  creds = provider.load()
  file_contents = {'access_key':creds.access_key, 'secret_key':creds.secret_key, 'token':creds.token }
  file_write(file_loc, file_contents) #Write Tokens to file
  token_issue_time= datetime.datetime.strptime(now.strftime("%y/%m/%d %H:%M:%S"), "%y/%m/%d  %H:%M:%S" ) # Remove time awareness
  token_issue_expiry = datetime.datetime.strptime((creds._expiry_time).strftime("%y/%m/%d %H:%M:%S"), "%y/%m/%d  %H:%M:%S" ) # Time awa
  expiry_time_sec = (token_issue_expiry - token_issue_time).total_seconds() # Total Seconds before token expiry
  expiry_time_min = expiry_time_sec/60
  return (int(expiry_time_min - 15))

if __name__=="__main__":
   # Pass File Location as Absolute Path to Storage Location for Instance Credentials
  file_loc = os.path.abspath(os.getcwd())+"/r.txt"
  credentials(file_loc)
  try:
    if  bool(sys.argv[1].strip()):
      file_loc = sys.argv[1]
  except:
    pass

  sched = BlockingScheduler()

  # Fetch New Credentials 15 mins before expiry of the previous ones
  sched.add_job (job(file_loc), 'interval', id='job_id', seconds=credentials(file_loc), replace_existing=True)

  # Example Redshift Schedule  which Pulls Cluster Details as A CronJob
  # And publishes them if successful
  @sched.scheduled_job ('cron', month='2-4,11-12', day='3rd fri', hour='2-5')
  def publish_cluster():
    slack= Slack(url='https://hooks.slack.com/services/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')
    credentials = key_read(file_loc)
    # Code for Redshift Task
    try:
      session = boto3.Session(
               aws_access_key_id=credentials['access_key'] ,
               aws_secret_access_key=credentials['secret_key'],
               aws_session_token=credentials['token']
               )
      ddb = session.client('redshift', 'us-east-1')
      cluster_list = ddb.describe_clusters()
      slack.post(text="Describe Clusters Detail Successful") 
    except:
      slack.post("Invalid Credentials or EC2 Role")

  sched.start()
