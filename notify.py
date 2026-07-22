import sys
import datetime
import glob
import os
import smtplib
import socket
from email.message import EmailMessage

# meta-notification:
# we modified his notify.py from the similar notify.pys in neighboring repos


def getlogfile(logdir
              ,logtype):

    # ex get most recent qa-* log from a log dir with logs like
    # import.log
    # export-20210126-165353
    # qa-20210126-165300

    list_of_logs = glob.glob(os.path.join(logdir
                                         ,'{0}*.log'.format(logtype)))

    if not list_of_logs:
        raise ValueError('No logs found for type "{0}" in {1}'.format(
            logtype
           ,logdir))

    latest_log_path = max(list_of_logs, key=os.path.getmtime)

    with open(latest_log_path, 'r') as file:
        loglines = file.read()

    return loglines

def getspecialcontent(notification
                     ,baseurl='https://nyc.maps.arcgis.com/home/item.html?id='
                     ,wiki='https://appdevwiki.nycnet/appdev/index.php?title=GIS_Data_Maintenance_Scripts#CSCL_Publishing_To_NYCMaps'):

    # PRD: Replaced and QAd nycmaps cscl_pub.gdb item 9163b04952354da2bf748abe1788e985
    itemid = notification.split()[-1]

    scontent  = '{0}{1}'.format(baseurl
                               ,itemid)
    scontent += '{0}Running from {1}'.format(os.linesep
                                           ,socket.gethostname())
    scontent += '{0}See the wiki for more info-- {1}'.format(os.linesep,
                                                             wiki)
    
    return scontent


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('notify.py - Usage: notify.py "subject" recipients logtype '
              '[checklogfor]')
        sys.exit(2)

    notification = sys.argv[1]
    pemails = sys.argv[2]
    plogtype = sys.argv[3]  # ex 'qa' 'export' '*' (latest)

    if len(sys.argv) == 4:
        pchecklogfor = 'nothing'
    else:
        # pass in ERROR for example to only notify if ERROR appears in log
        pchecklogfor = sys.argv[4]

    logdir = os.environ['TARGETLOGDIR']
    emailfrom = os.environ['NOTIFYFROM']
    smtpfrom = os.environ['SMTPFROM']

    msg = EmailMessage()

    # notification is like "importing buildings onto dev.sde"
    msg['Subject'] = '{0}'.format(notification)

    content = '{0}{1}'.format(notification
                             ,os.linesep)

    content += 'at {0} {1}'.format(datetime.datetime.now()
                                  ,os.linesep)

    if 'fail' not in notification.lower():
        content += '{0}{1}'.format(getspecialcontent(notification)
                                  ,os.linesep)

    try:
        content += os.linesep + getlogfile(logdir
                                          ,plogtype)
    except ValueError:
        print('notify.py - No logs found for type "{0}" in {1}'.format(
            plogtype
           ,logdir))
        sys.exit(1)
    except OSError as e:
        print('notify.py - Failed to read log content: {0}'.format(e))
        sys.exit(1)

    msg.set_content(content)
    msg['From'] = emailfrom

    # this is headers only
    # if a string is passed to sendmail it is treated as one recipient
    msg['To'] = pemails

    should_send = (
        (pchecklogfor != 'nothing' and pchecklogfor in content)
        or pchecklogfor == 'nothing'
    )

    if not should_send:
        print('notify.py - Email skipped, "{0}" not found in content'.format(
            pchecklogfor))
        sys.exit(0)

    smtp = None

    try:
        smtp = smtplib.SMTP(smtpfrom)
        smtp.sendmail(msg['From']
                     ,msg['To'].split(",")
                     ,msg.as_string())
    except smtplib.SMTPRecipientsRefused:
        print('notify.py - Email not sent: recipients refused (relay denied).')
        sys.exit(1)
    except (smtplib.SMTPException, OSError) as e:
        print('notify.py - Email not sent: {0}'.format(e))
        sys.exit(1)
    finally:
        if smtp is not None:
            try:
                smtp.quit()
            except OSError:
                pass
