# encoding: utf-8

import urllib2
import os
import sys
import glob
import json
import html5lib
import cookielib
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, web, PasswordNotFound
from bs4 import BeautifulSoup

IMG_PATH = u'images'
GARMIN_URL = 'http://biz.garmin.com.tw/introduction/index.asp'
COOKIE_NAME = 'cookie.txt'
USER_NAME = 'tangquincy'

def get_employ_img(url):
    r = web.get(url=url, stream=True)
    file_name = url.split('/')[-1]
    r.save_to_path(IMG_PATH + "/" + file_name)

def get_recent_cookie_from(ext):
    CONST_HOSTNAME = "biz.garmin.com.tw"
    CONST_ASPSESSION_PREFIX = "ASPSESSION"
    CONST_BIGGIPSERVER_PREFIX = "BIGipServer"
    session_name = ""
    session_value = ""
    server_name = ""
    server_value = ""

    firefox_profile_path = '/Users/spider391tang/Library/Application Support/Firefox/Profiles'
    latest_cookie = max(glob.glob(firefox_profile_path  + '/*/*/recovery.' + ext), key=os.path.getctime)

    f = open(latest_cookie)
    data = json.load(f)
    cookie_found = False
    for window in data["windows"]:
        cookie_found = False
        for co in window["cookies"]:
            host = co["host"].strip()
            name = co["name"].strip()
            if host.find(CONST_HOSTNAME) != -1 and name.find(CONST_ASPSESSION_PREFIX) != -1:
                session_name = name
                session_value = co["value"].strip()
                cookie_found = True

            if host.find(CONST_HOSTNAME) != -1 and name.find(CONST_BIGGIPSERVER_PREFIX) != -1:
                server_name = name
                server_value = co["value"].strip()
                cookie_found = True
        if cookie_found:
            break
    if not cookie_found:
        return None
    cookies = {}
    cookies[session_name] = session_value
    cookies[server_name] = server_value
    return cookies

def login_create_cookie(wf):
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
    if os.path.exists(COOKIE_NAME):
        cookie = cookielib.MozillaCookieJar()
        cookie.load(COOKIE_NAME, ignore_discard=True, ignore_expires=True)
        return cookie
    else:
        return login_create_cookie(wf)

def parse_html(r):
    soup = BeautifulSoup(r.text, "html5lib")
    employ_table = soup.find_all('table')[-1].find_all('tr', bgcolor="")

    employs = []
    for e in employ_table:
        # print e.prettify()
        employ = {}
        employ['title'] = e.contents[0].a.string.strip()
        employ['img'] = e.contents[1].img['src']
        employ_xml = e.find_all('td')[3].ul
        # print employ_xml
        # case <font color="blue"><a href="mailto:quincy.tang@garmin.com">唐心磊</a>(Quincy Tang)</font>
        # print employ_xml.contents[0].font
        if not employ_xml.contents[0].font.string:
            employ['name'] = employ_xml.contents[0].font.contents[1].strip(u'()')
            employ['name_tw'] = employ_xml.contents[0].a.string.strip()
        # <font color="blue">謝玉</font>
        elif u"(" not in employ_xml.contents[0].font.string:
            employ['name'] = ""
            employ['name_tw'] = employ_xml.contents[0].font.string.strip()
        # case <font color="blue">蘇建輝(Kevin Su)</font>
        else:
            employ['name'] = employ_xml.contents[0].font.string.split(u'(')[1].strip(u')')
            employ['name_tw'] = employ_xml.contents[0].font.string.split(u'(')[0].strip()
        employ['id'] = employ_xml.contents[1].font.string.strip()
        employ['department'] = employ_xml.contents[2].string.split(u'：')[1].strip()
        employ['costcenter'] = employ_xml.contents[3].string.split(u':')[1].strip()
        employ['extno'] = employ_xml.contents[4].string.split(u':')[1].strip()
        employ['org'] = employ_xml.contents[5].string.split(u':')[1].strip()
        # print employ
        employs.append(employ)
    return employs

def main(wf):
    # build argument parser to parse script args and collect their
    # values
    parser = argparse.ArgumentParser()
    # add an optional (nargs='?') --setkey argument and save its
    # value to 'apikey' (dest). This will be called from a separate "Run Script"
    # action with the API key
    parser.add_argument('--setkey', dest='apikey', nargs='?', default=None)
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

    # Get query from Alfred
    if args.query == None:
        query = "jacky"
    else:
        query = args.query

    co = get_recent_cookie(wf)

    # params = dict(WorkType='5', cboEmpID1='12001')
    params = {}
    if query.isdigit():
        params = dict(WorkType='5', cboEmpID1=query)
    else:
        params = dict(WorkType='6', cboEmpName=query)
        if len(query) < 2:
            return

    def wrapper():
        """`cached_data` can only take a bare callable (no args),
        so we need to wrap callables needing arguments in a function
        that needs none.
        """
        try:
            r = web.post(url=GARMIN_URL, cookies=co, data=params)
            r.raise_for_status()
            return parse_html(r)
        except urllib2.HTTPError, err:
            os.remove(COOKIE_NAME)

    employs = wf.cached_data(query, wrapper, max_age=6000)

    for e in employs:
        fname = e['img'].split('/')[-1]
        if not os.path.isfile(IMG_PATH + "/" + fname):
            get_employ_img(e['img'])
        title = e['name_tw'] + '(' + e['name'] + ')' + "  Ext:" + e['extno'] + "  ORG:" + e['org']
        subtitle = "ID:" + e['id'] + "  " + e['department'] + " (" + e['title'] + ")"
        wf.add_item(title=title,
                    subtitle=subtitle,
                    icon=IMG_PATH + "/" + fname,
                    valid=True,
                    arg=e['id'])
    wf.send_feedback()

if __name__ == u"__main__":
    wf = Workflow()
    sys.exit(wf.run(main))

