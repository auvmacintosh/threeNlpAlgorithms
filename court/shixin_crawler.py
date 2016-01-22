#!/usr/bin/python
#coding: utf8

import os
import time
import re
import util
import logging
import sqlite3
from StringIO import StringIO
from captcha import Captcha
from PIL import Image
try:
  from bs4 import BeautifulSoup
except:
  import BeautifulSoup


LIST_URL = 'http://shixin.court.gov.cn/findd'
DETAIL_URL = 'http://shixin.court.gov.cn/findDetai?id=%s&pCode=%s'
CAPTCHA_URL = 'http://shixin.court.gov.cn/image.jsp'
LIST_PAGE_SIZE = 1000
LIST_FILE = 'data/shixin_list.txt'
DETAIL_FILE = 'data/shixin/%s.txt'
DB = 'data/shixin.db'
RETRY_TIMES = 3
MESSAGE_CAPTCHA_ERROR = '验证码错误，请重新输入'


class CaptchaError(Exception):
    pass


class Shixin:

  def __init__(self):
    self.cookie = {}
    self.randcode = ''
    self.conn = sqlite3.connect(os.path.join(
      os.path.split(os.path.realpath(__file__))[0], DB))

  def get_captcha(self):
    data = res = None
    for i in range(RETRY_TIMES):
      try:
        data, res = util.urlfetch(CAPTCHA_URL, cookie=self.cookie)
      except Exception, ex:
        logging.error("%s", ex)
        time.sleep(1)
        continue

      if res.code == 521:
        time.sleep(1)
        self.cookie = util.update_cookie(data, res, self.cookie)
        logging.info("Got 521, refresh cookie: %s", self.cookie)
      if res.code == 200:
        break

    try:
      im = Image.open(StringIO(data))
      c = Captcha(im)
      result = c.process()
      c.printmask()
      logging.info("Captcha: [%s]" % result)
      self.randcode = result

      if 'Set-Cookie' in res.headers:
        new_cookie = res.headers['Set-Cookie'].split(' ')[0]
        self.cookie.update(dict((new_cookie.strip(';').split('='),)))
        logging.info("Got cookie with captcha: %s", new_cookie)
    except Exception, ex:
      logging.error(str(ex))

  def list_crawler(self, ranges):
    self.get_captcha()
    cur = self.conn.cursor()
    for p in ranges:
      items = total_pages = None
      for i in range(RETRY_TIMES):
        try:
          items, total_pages = self._list_page_crawler(p)
        except CaptchaError:
          logging.warning("Captcha expired")
          self.get_captcha()
        except:
          continue

        if items:
          logging.info("Got [%d] items from page [%d] (total page: [%d])" % (
            len(items), p, total_pages))
        else:
          logging.info("Failed to get items from page [%d] (total page: [%d])" % (
            p, total_pages))
        break
      cur.execute('SELECT count(*) FROM shixin')
      data = cur.fetchone()
      before_item_count = data[0]
      logging.info("[%d] lines in Database" % data[0])
      if not items:
        logging.error("failed to get items.")
        continue
      for item in items:
        cur.execute(
          "INSERT OR IGNORE INTO shixin (id, number, name, date) VALUES(%s, '%s', '%s', '%s')" % item)
      self.conn.commit()

      cur.execute('SELECT count(*) FROM shixin')
      data = cur.fetchone()
      logging.info("[%d] lines in Database after add [%d] items. [%d] NEW." %
                   (data[0], len(items), int(data[0]) - int(before_item_count)))

  def _list_page_crawler(self, page=1, page_size=LIST_PAGE_SIZE):
    data = {
      'pName': '',
      'pCardNum': '',
      'pProvince': '0',
      'pCode': self.randcode,
      'currentPage': str(page),
      'pageSize': page_size,
    }
    html, res = util.urlfetch(LIST_URL, cookie=self.cookie, data=data)
    if '验证码' in html:
      logging.error('wrong captcha')
      raise CaptchaError()

    soup = BeautifulSoup(html, "html.parser")
    trs = soup.find('tbody').findAll('tr')
    items = []
    for tr in trs:
      if not tr.find('td'):
        continue
      tds = tr.findAll('td')

      name = tds[1].text
      date = tds[2].text
      number = tds[3].text
      id_ = tds[4].a['id']
      items.append((id_, number, name, date))

    last_page_soup = soup.find('a', text='尾页')
    pages = re.search(r'gotoPage\((\d\d+)\)',
                      last_page_soup['onclick']).group(1)

    return items, int(pages)

  def _update_downloaded_state(self, cur, id, state):
    cur.execute("UPDATE shixin SET downloaded=%s WHERE id=%s" % (state, id))
    self.conn.commit()

  def detail_crawler(self):
    self.get_captcha()
    cur = self.conn.cursor()

    # Download new items.
    cur.execute("SELECT id FROM shixin WHERE downloaded=0")
    data = cur.fetchall()
    logging.info("[%d] new items to download" % len(data))

    success = 0
    for row in data:
      if self._detail_item_crawler(row[0]):
        success += 1
        self._update_downloaded_state(cur, row[0], 1)
        logging.info("Successfully downloaded detail (id=%s)  [%d] item downloaded." % (
          row[0], success))
      else:
        self._update_downloaded_state(cur, row[0], -1)
        logging.error("Failed to download detail (id=%s)" % row[0])

        self.get_captcha()
    logging.info("[REPORT] [%s] new items to download, [%d] succeed, [%d] failed." % (
      len(data), success, len(data) - success))

    cur.execute("SELECT id FROM shixin WHERE downloaded=0")
    data = cur.fetchall()
    logging.info("[%d] new items to download" % len(data))

    # retry failed items.
    cur.execute("SELECT id FROM shixin WHERE downloaded=-1")
    data = cur.fetchall()
    logging.info("[%d] failed items to retry download" % len(data))

    success = 0
    for row in data:
      if self._detail_item_crawler(row[0]):
        success += 1
        self._update_downloaded_state(cur, row[0], 1)
        logging.info("Successfully downloaded detail (id=%s)  [%d] item downloaded." % (
          row[0], success))
      else:
        self._update_downloaded_state(cur, row[0], -2)
        logging.error("Failed to download detail (id=%s)" % row[0])

        self.get_captcha()
    logging.info("[REPORT] [%s] failed items to retry download, [%d] succeed, [%d] failed." % (
      len(data), success, len(data) - success))

  def _detail_item_crawler(self, id):
    url = DETAIL_URL % (id, self.randcode)
    html = res = None
    try:
      html, res = util.urlfetch(url, cookie=self.cookie)
    except Exception, ex:
      logging.error('Error %s' % ex)
      return False
    if res.code != 200:
      print res
      logging.error('Server error [%s]' % res.code)
      return False
    if MESSAGE_CAPTCHA_ERROR in html:
      logging.error('Captcha error')
      return False
    detail_filepath = os.path.join(os.path.split(
      os.path.realpath(__file__))[0], DETAIL_FILE % id)
    f = open(detail_filepath, 'w')
    f.write(html)
    f.close()
    return True


def main():
  util.init_logging()
  logging.info("Shixin Crawler started")
  c = Shixin()
  c.list_crawler(range(1, 10))
  c.detail_crawler()

if __name__ == '__main__':
  main()
