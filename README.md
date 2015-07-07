# MWRecentActivityNotifier

This simple-project sends according your settings a report of recent acitities from your Wiki (MediaWiki).

### Clone this repo
```
git clone https://github.com/renato-farias/MWRecentActivityNotifier.gti
```

### install all dependecies
```
pip install -r requirements.txt
```
 
### running the notifier
```
python notifier.py
```

### put it in your crontab:
```
crontab -e
```

```
# this example runs the notifier every monday at 9AM
0 9 * * 1 cd /PATH/MWRecentActivityNotifier/ && python notifier.py
```

### Settings
```yaml
database:
  hostname: DATABASE SERVER NAME/ADDRESS String !required
  username: DATABASE USER NAME String !required
  password: DATABASE USER'S PASSWORD String !required
  database: DATABASE BASE NAME String !required

report_from_days_ago: NUMBER OF DAYS AGO TO THE DATA COLLECTING Integer !required

email_report:
  from: EMAIL SENDER String !required
  to: EMAIL RECEIVER String !required
  subject: EMAIL SUBJECT String !required
  smtp_server: SMTP SERVER NAME/ADDRESS String !required
  smtp_port: SMTP SERVER PORT Integer !required
  smtp_auth: SMTP SERVER WITH AUTH Boolean [true|false] !required
  smtp_user: SMTP SERVER USER NAME String !not-required
  smtp_pass: SMTP SERVER USER PASS String !not-required
```
