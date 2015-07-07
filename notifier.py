#!/usr/bin/python
# -*- coding: utf-8 -*-

import yaml
import smtplib
import MySQLdb
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

config = yaml.load(open('config/config.yaml'))

today=datetime.today().strftime('%Y%m%d%H%M%S')
delta=datetime.today()-timedelta(days=config['report_from_days_ago'])
days_ago=delta.strftime('%Y%m%d%H%M%S')

new_articles = {}
edited_articles = {}
top_writer_period = {}
top_writer_total = {}

db = MySQLdb.connect(host=config['database']['hostname'],
                     user=config['database']['username'],
                     passwd=config['database']['password'],
                     db=config['database']['database'])

cur = db.cursor() 
cur.execute("SELECT rc_user_text, rc_source, rc_cur_id, rc_title\
             FROM recentchanges \
             WHERE rc_minor = 0 \
             AND rc_timestamp >= %s \
             AND rc_timestamp <= %s" % (days_ago, today))

for row in cur.fetchall():
    if row[1] == 'mw.edit':
        if str(row[2]) not in edited_articles.iterkeys():
            edited_articles[str(row[2])] = {'title': None, 'users': []}
        if not edited_articles[str(row[2])]['title']:
            edited_articles[str(row[2])]['title'] = row[3]
        if len(edited_articles[str(row[2])]['users']) == 0:
            edited_articles[str(row[2])]['users'] = [row[0]]
        else:
            if row[0] not in edited_articles[str(row[2])]['users']:
                edited_articles[str(row[2])]['users'].append(row[0])

    elif row[1] == 'mw.new':
        if str(row[2]) not in new_articles.iterkeys():
            new_articles[str(row[2])] = {'title': row[3], 'user': row[0]}


def containsnonasciicharacters(str):
    return not all(ord(c) < 128 for c in str)   


def generate_last_article(articles):
    ulist = '<ul>\n'
    for a in articles:
        ulist += '      <li>\n'
        ulist += '        <a href="https://wiki.cloudopen.com.br/index.php/%s">%s</a>\n' % \
                                      (articles[str(a)]['title'], articles[str(a)]['title'])
        ulist += '        (por: %s)\n' % articles[str(a)]['user']
        ulist += '      </li>\n'                           
    ulist += '    </ul>\n'
    return ulist


def generate_last_edited(articles):
    ulist = '<ul>\n'
    for a in articles:
        ulist += '      <li>\n'
        ulist += '        <a href="https://wiki.cloudopen.com.br/index.php/%s">%s</a>\n' % \
                                      (articles[str(a)]['title'], articles[str(a)]['title'])
        ulist += '        (colaboradores: %s)\n' % ', '.join(articles[str(a)]['users'])
        ulist += '      </li>\n'                           
    ulist += '    </ul>\n'
    return ulist


def generate_tops(query_result):
    user_points = {}
    for row in query_result:
        if row[0] not in user_points.iterkeys():
            user_points[row[0]] = {row[1]: row[2]}
        else:
            # this condintions applies a way to get the better view of user's editions.
            # A lot of users never apply the simple changes as minor changes, thus, I am
            # counting just one point for the amount of edits for a single article
            if row[1] == 'mw.edit' and row[1] in user_points[row[0]].iterkeys():
                user_points[row[0]][row[1]] += 1
            elif row[1] == 'mw.edit':
                user_points[row[0]][row[1]] = 1
            elif row[1] == 'mw.new' and row[1] in user_points[row[0]].iterkeys():
                user_points[row[0]][row[1]] += row[2]
            elif row[1] == 'mw.new':
                user_points[row[0]][row[1]] = row[2]

    user_totals = {}
    for u in user_points:
        u_total = 0
        for up in user_points[u]:
            u_total += user_points[u][up]
            if str(u) in user_totals.iterkeys():
                user_totals[str(u)][str(up)] = user_points[u][up]
            else:
                user_totals[str(u)] = {str(up): user_points[u][up]}
        user_totals[str(u)]['total'] = u_total
    
    sorted_user_totals = sorted(user_totals.items(), key=lambda k: k[1]['total'], reverse=True)

    ulist = '<ol>\n'
    for k,v in sorted_user_totals:
        t = 0
        n = 0
        e = 0
        if 'total' in v.iterkeys():
            t = v['total']
        if 'mw.new' in v.iterkeys():
            n = v['mw.new']
        if 'mw.edit' in v.iterkeys():
            e = v['mw.edit']
        ulist += '      <li><strong>%s</strong> (Total: %s, Novos Artigos: %s, Artigos Atualizados: %s)</li>\n' % \
                                                                                      (k, t, n, e)
    ulist += '    </ol>\n'
    return ulist




def generate_top_total():
    cur.execute("SELECT rc_user_text, rc_source, count(rc_source) \
                 FROM recentchanges \
                 WHERE rc_minor = 0 \
                 AND rc_source IN ('mw.edit', 'mw.new') \
                 GROUP BY rc_user_text, rc_source, rc_cur_id")
    return generate_tops(cur.fetchall())


def generate_top_period(b,e): 
    cur.execute("SELECT rc_user_text, rc_source, count(rc_source) \
                 FROM recentchanges \
                 WHERE rc_minor = 0 \
                 AND rc_source IN ('mw.edit', 'mw.new') \
                 AND rc_timestamp >= %s \
                 AND rc_timestamp <= %s \
                 GROUP BY rc_user_text, rc_source, rc_cur_id" % (b, e))
    return generate_tops(cur.fetchall())

 
# Construct email
msg = MIMEMultipart('alternative')
msg['To'] = config['email_report']['to']
msg['From'] = config['email_report']['from']
msg['Subject'] = config['email_report']['subject']
 
# Create the body of the message (a plain-text and an HTML version).
#text = "This is a test message.\nText and html."
html = """\
<html>
  <head></head>
  <body>
    <h3>Confira as atualizações da Wiki dos últimos %s dias.</h3>
    <p>Os últimos artigos criados:</p>
    %s
    <p>Veja também os últimos artigos que foram modificados:</p>
    %s
    <p>Os que mais contribuiram nos últimos %s dias:</p>
    %s
    <p>Os que mais contribuiram desde o ínicio do universo:</p>
    %s
  </body>
</html>
""" % (str(config['report_from_days_ago']), generate_last_article(new_articles),
       generate_last_edited(edited_articles), str(config['report_from_days_ago']),
       generate_top_period(days_ago, today), generate_top_total())
 
# Record the MIME types of both parts - text/plain and text/html.
#part1 = MIMEText(text, 'plain')
if containsnonasciicharacters(html):
    part2 = MIMEText(html, 'html', 'utf-8')
else:
    part2 = MIMEText(html, 'html')  
#part2 = MIMEText(html, 'html')
 
# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
#msg.attach(part1)
msg.attach(part2)
 
# Send the message via an SMTP server
s = smtplib.SMTP(config['email_report']['smtp_server'],
                 config['email_report']['smtp_port'])
if config['email_report']['smtp_auth']:
    s.login(config['email_report']['smtp_user'],
            config['email_report']['smtp_pass'])
s.sendmail(config['email_report']['from'],
           config['email_report']['to'],
           msg.as_string())
s.quit()

#print html