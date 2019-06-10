#!/usr/bin/python

import argparse
import requests
import sqlite3
import os
from slackconfig import *
import json
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--singleurl', help='Single URL to add. E.g: http://google.com', dest='singleurl')
parser.add_argument('-ul', '--urlslist', help='File with new urls to add. E.g: urls.txt', dest='urlslist')
parser.add_argument('-rm', '--remove', help='URL to remove from database. E.g: http://google.com', dest='urltoremove')
parser.add_argument('-d', '--display', help='Display all monitored URLs', required =  False, nargs='?', const="True", dest='displayurls')
args = parser.parse_args()

def db_install():
    if (os.path.isfile('./keye.db')) == False:
        db = sqlite3.connect('keye.db')
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE urls(id INTEGER PRIMARY KEY, url TEXT,
                               contentlength INTEGER)''')
        db.commit()
        db.close()
    else:
        pass

def addsingleurl():
    url = args.singleurl
    request(url)

def addurlsfromlist():
    urlslist = open(args.urlslist, "r")
    for url in urlslist:
        url = url.rstrip()
        request(url)

# Get the content length from the 'content-length' header or calculate it from the response's body.
def getcontentlength(url):
    response = requests.get(url, allow_redirects=True, verify=False, timeout=5)
    return response.headers['content-length'] if 'content-length' in response.headers else len(response.content)

def request(url):
    try:
        if not "http" in url:
            url = "http://" + url
        contentlength = getcontentlength(url)
        try:
            committodb(url, contentlength)
            print("We have successfully added the URL to be monitored.")
        except Exception as e:
            print(e)

    except:
        try:
            url = url.replace("http://", "https://")
            contentlength = getcontentlength(url)
            committodb(url, contentlength)
            print("We have successfully added the URL to be monitored.")
        except Exception as e:
            print("We could not connect to {} due to following error: {}".format(url, e))

def committodb(url, contentlength):
    try:
        cursor.execute('''INSERT INTO urls(url, contentlength)
                          VALUES(?,?)''', (url, contentlength))
        db.commit()
    except Exception as e:
        print(e)

def getfromdb():
    try:
        cursor.execute('''SELECT id, url, contentlength FROM urls''')
        all_rows = cursor.fetchall()
        for row in all_rows:
            id = row[0]
            url = row[1]
            contentlength = str(row[2])
            connect(id, url, contentlength)
    except Exception as e:
        print(e)

def connect(id, url, contentlength):
    try:
        newcontentlength = getcontentlength(url)
        if newcontentlength == contentlength:
            pass
        else:
            notify(url)
            cursor.execute('''UPDATE urls SET contentlength = ? WHERE id = ? ''', (newcontentlength, id))
            db.commit()
    except Exception as e:
        print("We could not connect to {} due to following error: {}".format(url, e))

def removefromdb():
    urltoremove = args.urltoremove
    try:
        cursor.execute('''DELETE FROM urls WHERE url = ? ''', (urltoremove,))
        db.commit()
        print("\nWe have successfully removed the URL from the database.")
    except Exception as e:
        print(e)

def displayurls():
    try:
        cursor.execute('''SELECT url from urls''')
        all_rows = cursor.fetchall()
        for row in all_rows:
            print(row[0])
    except Exception as e:
        print("We couldn't retrieve URLs due to following error {}".format(e))


def notify(url):
    webhook_url = posting_webhook
    slack_data = {'text': 'Changes detected on: ' + url}
    sendnotification = requests.post(webhook_url, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})

db_install()
db = sqlite3.connect('keye.db')
cursor = db.cursor()

if args.singleurl:
    addsingleurl()
elif args.urlslist:
    addurlsfromlist()
elif args.urltoremove:
    removefromdb()
elif args.displayurls:
    displayurls()
else:
    getfromdb()

db.close()
