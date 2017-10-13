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

IMG_PATH = u'images'
GARMIN_URL = 'http://biz.garmin.com.tw/introduction/index.asp'
GARMIN_LEAVE_URL = 'http://prod.garmin.com.tw/PyrWeb2/attendance/qryindirectorytoday.asp'
COOKIE_NAME = 'cookie.txt'
USER_NAME = 'tangquincy'

def get_leave_dict():
    """
    Parse leave html and return dict about employ leave information.
    """
    r = web.get(url=GARMIN_LEAVE_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html5lib", from_encoding="utf-8")

    leave_employs = dict()
    leave_table = soup.find_all('table')[1].find_all('tr')
    for e in leave_table:
        eid = e.contents[7].string.strip()
        if eid.isdigit():
            eid = int(e.contents[7].string.strip())
            # print e.contents[9].string
            # print e.contents[11].string
            start_date = e.contents[11].string.strip()
            start_time = e.contents[13].string.strip()
            start = datetime.strptime(start_date+start_time, '%Y%m%d%H%M')
            end_date = e.contents[15].string.strip()
            end_time = e.contents[17].string.strip()
            end = datetime.strptime(end_date+end_time, '%Y%m%d%H%M')
            info = dict()
            info['start'] = start
            info['end'] = end
            info['date'] = e.contents[19].string.strip()
            info['hour'] = e.contents[21].string.strip()
            info['type'] = u'請假'
            leave_employs[eid] = info

    business_table = soup.find_all('table')[3].find_all('tr')
    # print business_table.prettify()
    for e in business_table:
        eid = e.contents[7].string.strip()
        if eid.isdigit():
            eid = int(e.contents[7].string.strip())
            info = dict()
            # print eid
            start_list = e.contents[13].string.strip().split()
            end_list = e.contents[15].string.strip().split()
            start_time = None
            end_time = None
            if len(start_list) > 1:
                if start_list[1] == u'上午':
                    start_list[1] = u'AM'
                else:
                    start_list[1] = u'PM'
                start_time = datetime.strptime(start_list[0] + start_list[1] + start_list[2], '%Y/%m/%d%p%H:%M:%S')
            else:
                start_time = datetime.strptime(start_list[0], '%Y/%m/%d')

            if len(end_list) > 1:
                if end_list[1] == u'上午':
                    end_list[1] = u'AM'
                else:
                    end_list[1] = u'PM'
                end_time = datetime.strptime(end_list[0] + end_list[1] + end_list[2], '%Y/%m/%d%p%H:%M:%S')
            else:
                end_time = datetime.strptime(end_list[0], '%Y/%m/%d')

            info['start'] = start_time
            info['end'] = end_time
            info['peer'] = e.contents[17].string.strip()
            info['reason'] = e.contents[19].string.strip()
            info['type'] = u'公出'
            leave_employs[eid] = info
    return leave_employs

def get_employ_img(url):
    """
    Download employ image from url and save to IMG_PATH.
    """
    r = web.get(url=url, stream=True)
    file_name = url.split('/')[-1]
    r.save_to_path(IMG_PATH + "/" + file_name)

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

def parse_html(r):
    """
    Parse employ html and return dict about employ

    title
    img
    name
    name_tw
    id
    department
    costcenter
    extno
    org
    """
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
        employ['extno'] = employ_xml.contents[5].string.split(u':')[1].strip()
        employ['org'] = employ_xml.contents[6].string.split(u':')[1].strip()
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
            wf.add_item('Getting employ information from server',
                        valid=False,
                        icon=ICON_INFO)
            r = web.post(url=GARMIN_URL, cookies=co, data=params)
            r.raise_for_status()
            return parse_html(r)
        except urllib2.HTTPError, err:
            os.remove(COOKIE_NAME)

    employs = wf.cached_data(query, wrapper, max_age=6000)
    leave_employs = wf.cached_data('leave_table', get_leave_dict, max_age=6000)

    for e in employs:
        fname = e['img'].split('/')[-1]
        if not os.path.isfile(IMG_PATH + "/" + fname):
            get_employ_img(e['img'])
        title = e['name_tw'] + '(' + e['name'] + ')' + "  Ext:" + e['extno'] + "  ORG:" + e['org']
        subtitle = "ID:" + e['id'] + "  " + e['department'] + " (" + e['title'] + ")"

        leave_description = None
        if int(e['id']) in leave_employs:
            leave_employ = leave_employs[int(e['id'])]
            title = "[" + leave_employ['type'] + "] " + title
            if 'reason' in leave_employ:
                leave_description = u'終止日期:' + unicode(leave_employ['end'].strftime("%Y-%m-%d"))
                leave_description = leave_description + u' 原因:' + leave_employ['reason']
                if leave_employ['peer'] != "":
                    leave_description = leave_description + u' 同行:' + leave_employ['peer']
            else:
                leave_description = u'終止時間:' + unicode(leave_employ['end'].strftime("%Y-%m-%d %H:%M"))
                leave_description = leave_description + u' 天數:' + leave_employ['date']
                leave_description = leave_description + u' 時數:' + leave_employ['hour']

        item = wf.add_item(title=title,
                    subtitle=subtitle,
                    icon=IMG_PATH + "/" + fname,
                    valid=True,
                    type='file',
                    arg=wf.workflowfile(IMG_PATH + "/" + fname))
        item.add_modifier( "alt", subtitle=leave_description, arg=e['name_tw'] )
        item.add_modifier( "ctrl", subtitle=e['id'], arg=e['id'] )

    wf.send_feedback()

if __name__ == u"__main__":
    wf = Workflow3()
    sys.exit(wf.run(main))

