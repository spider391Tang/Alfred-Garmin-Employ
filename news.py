# encoding: utf-8

import urllib2
import os
import sys
import glob
import json
import html5lib
import cookielib
import argparse
import datetime
from datetime import datetime
from workflow import Workflow3, ICON_INFO, ICON_WEB, ICON_WARNING, web, PasswordNotFound
from bs4 import BeautifulSoup

GARMIN_URL = 'http://biz.garmin.com.tw/introduction/index.asp'
GARMIN_NEWS = 'http://intranet.garmin.com.tw/forum1/note2/forms.asp'
GARMIN_LEAVE_URL = 'http://prod.garmin.com.tw/PyrWeb2/attendance/qryindirectorytoday.asp'
COOKIE_NAME = 'cookie.txt'
USER_NAME = 'tangquincy'

def login_create_cookie(wf):
    """
    Use account to login and return cookie information.
    """
    url = "http://passport.garmin.com.tw/passport/login.aspx?Page=http://biz.garmin.com.tw/introduction/index.asp&Qs="

    pwd = wf.get_password('employ_password')
    r = web.get(url=url, auth=(USER_NAME, pwd))
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html5lib")
    cookie = cookielib.MozillaCookieJar(COOKIE_NAME)
    result = web.get(soup.body.a['href'], cookies=cookie)
    result.raise_for_status()
    cookie.save(ignore_discard=True, ignore_expires=True)
    return cookie

def get_recent_cookie(wf):
    """
    Get cookie if exist or call login_create_cookie to get.
    """
    if os.path.exists(COOKIE_NAME):
        cookie = cookielib.MozillaCookieJar()
        cookie.load(COOKIE_NAME, ignore_discard=True, ignore_expires=True)
        return cookie
    else:
        return login_create_cookie(wf)

def parse_reply(r):
    html = wf.cached_data(r, max_age=0)
    news_li = html.find_all('li')
    news_list = []
    for new in news_li:
        news = {}
        news['title'] = new.find_all('a')[0]['title']
        news['href'] = new.find_all('a')[0]['href']
        news['author'] = new.find('b').contents[0].string.strip()
        news['reply'] = new.find('ul')
        news_list.append(news)
    return news_list 


def parse_html(r):
    """
    Parse employ html and return dict about employ

    title
    """
    soup = BeautifulSoup(r.text, "html5lib")

    news_li = soup.find_all('li','sub-tit')
    wf.logger.debug('print news_li')
    
    news_list = []
    for new in news_li:
        news = {}
        news['title'] = new.find_all('a')[1]['title']
        news['href'] = new.find_all('a')[1]['href']
        news['author'] = new.find('b').contents[0].string.strip()
        news['reply'] = new.find('ul')
        # wf.logger.debug('Quincy:' + str(type(news['reply'])))
        # print new.find('b')
        news_list.append(news)
    return news_list 

def main(wf):
    # build argument parser to parse script args and collect their
    # values
    parser = argparse.ArgumentParser()
    # add an optional (nargs='?') --setkey argument and save its
    # value to 'apikey' (dest). This will be called from a separate "Run Script"
    # action with the API key
    parser.add_argument('--setkey', dest='apikey', nargs='?', default=None)
    parser.add_argument('--checkreply', dest='checkreply', nargs='?', default=None)
    # add an optional query and save it to 'query'
    parser.add_argument('query', nargs='?', default=None)
    # parse the script's arguments
    args = parser.parse_args(wf.args)


    ####################################################################
    # Save the provided API key
    ####################################################################

    # decide what to do based on arguments
    if args.apikey:  # Script was passed an API key
        # save the key
        # wf.settings['api_key'] = args.apikey
        wf.save_password('employ_password', args.apikey)
        return 0  # 0 means script exited cleanly


    ####################################################################
    # Check that we have an API key saved
    ####################################################################

    try:
        api_key = wf.get_password('employ_password')
    except PasswordNotFound:  # API key has not yet been set
        wf.add_item('No password set.',
                    'Please use emaccount to set your password.',
                    valid=False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    wf.logger.debug('Quincy:' + args.query)
    q = args.query.strip()
    # Get query from Alfred
    if q == '':
        co = get_recent_cookie(wf)
        def wrapper():
            """`cached_data` can only take a bare callable (no args),
            so we need to wrap callables needing arguments in a function
            that needs none.
            """
            try:
                r = web.get(url=GARMIN_NEWS, cookies=co)
                r.raise_for_status()
                return parse_html(r)
            except urllib2.HTTPError, err:
                os.remove(COOKIE_NAME)
        news = wf.cached_data('news', wrapper, max_age=600)

        for new in news:
            item = wf.add_item(title=new['title'],
                    subtitle=new['author'],
                    quicklookurl="http://intranet.garmin.com.tw/forum1/note2/" + new['href'],
                    icon='icon_replymail.png' if new['reply'] is not None else 'icon_mail.png',
                    arg=new['href'] if new['reply'] is not None else None,
                    valid=True)
            def wrapper2():
                return new['reply']
            if new['reply'] is not None:
                # wf.logger.debug('Quincy cached_data:' + str(type(new['reply'])))
                wf.cached_data(new['href'], wrapper2, max_age=600)
        wf.send_feedback()
    else:
        news = parse_reply(q)
        for new in news:
            wf.add_item(title=new['title'],
                    subtitle=new['author'],
                    quicklookurl="http://intranet.garmin.com.tw/forum1/note2/" + new['href'],
                    icon='icon_mail.png',
                    valid=True)
        wf.add_item(' Back',
                    valid=True,
                    arg="Back",
                    icon='icon_return.png')
        wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow3()
    sys.exit(wf.run(main))

