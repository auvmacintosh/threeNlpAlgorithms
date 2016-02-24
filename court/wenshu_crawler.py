#!/usr/bin/python
#coding: utf8

import sys
import os
import json
import datetime
import time
import re
import util
import logging
import traceback


LIST_URL = 'http://www.court.gov.cn/zgcpwsw/List/ListContent'
LIST_PAGE_SIZE = 20
LIST_PAGE_LIMIT = 20
DEFAULT_DAYS = 60
SAVEPATH_TEMPLATE = 'data/wenshu/%s'
FILENAME_TEMPLATE = '%s.txt'
PROVINCES = '北京市,天津市,河北省,山西省,内蒙古自治区,辽宁省,吉林省,黑龙江省,上海市,江苏省,浙江省,安徽省,福建省,江西省,山东省,河南省,湖北省,湖南省,广东省,广西壮族自治区,海南省,重庆市,四川省,贵州省,云南省,西藏自治区,陕西省,甘肃省,青海省,宁夏回族自治区,新疆维吾尔自治区,新疆维吾尔自治区高级人民法院生产建设兵团分院'.split(
  ',')
RETRY_TIMES = 3
BASE_PATH = os.path.split(os.path.realpath(__file__))[0]


class Wenshu:

  def __init__(self):
    self.cookie = {}

  def get_cookie(self):
    try:
      data, res = util.urlfetch(LIST_URL)
    except Exception, ex:
      logging.error("%s", ex)
      time.sleep(1)

    if res.code == 521:
      self.cookie = util.update_cookie(data, res)
      logging.info("Got 521, refresh cookie: %s", self.cookie)


  def crawl_page(self, page=1, page_size=LIST_PAGE_SIZE, province=None, date=None):
    params = [
      '裁判日期:{0} TO {0}'.format(date.strftime('%Y-%m-%d')) if date else None,
      ('法院地域:%s' % province) if province else None,
    ]
    param = {
      'Param': ','.join(filter(None, params)),
      'Index': str(page),
      'Page': page_size,
      'Order': '法院层级',
      'Direction': 'asc',
    }

    data = None
    for i in range(RETRY_TIMES):
      html = ''
      try:
        html, res = util.urlfetch(LIST_URL, data=param, cookie=self.cookie)
        data = json.loads(html)
        data = json.loads(data)
      except Exception, ex:
        logging.error("[TRY %d failed] %s", i, ex)
        if html:
          logging.error("RESPONSE: %s" % html[:100])
        traceback.print_exc()
        if ex.code == 521:
          self.get_cookie()
        continue
      print json.dumps(data, ensure_ascii=False)[:100]
      break

    if data:
      logging.info("[%s-%s-page%d] Got %d items, size: %d bytes" %
                   (province, date.strftime("%Y%m%d"), page, len(data) - 1, len(html)))
    else:
      logging.error('No json response')
    return data

  def crawl(self, days=7):
    for dday in range(days, 0, -1):
      date = datetime.datetime.now() - datetime.timedelta(days=dday)
      for p in PROVINCES:
        logging.info('Crawling [%s-%s]' % (p, date.strftime("%Y%m%d")))
        data = self.crawl_page(page=1, province=p, date=date)
        count = 0
        if data and len(data) > 0 and 'Count' in data[0]:
          logging.info("Count: %d" % int(data[0]['Count']))
          count = int(data[0]['Count'])
        else:
          logging.warning("illegal data, can't read 'Count' field")
          continue
        self._save_items(data[1:], p, date)

        if count <= LIST_PAGE_SIZE:
          continue
        # Continue download other pages
        total_pages = min(LIST_PAGE_LIMIT, count / LIST_PAGE_SIZE)
        logging.info("[%d] pages to download", total_pages)

        for i in range(2, total_pages):
          data = self.crawl_page(page=i, province=p, date=date)
          if not data:
            continue
          if len(data) == 1:
            logging.info("No more data for [%s-%s]" %
                         (p, date.strftime("%Y%m%d")))
          self._save_items(data[1:], p, date)

  def _save_items(self, items, province, date):
    save_dir = os.path.join(BASE_PATH, SAVEPATH_TEMPLATE %
                            (date.strftime("%Y%m%d")))
    if not os.path.exists(save_dir):
      try:
        os.makedirs(save_dir)
        logging.info("created dir [%s]" % save_dir)
      except Exception, ex:
        logging.error("failed to create dir [%s], ex" % (save_dir, ex))

    for item in items:
      if u"文书ID" not in item:
        logging.warning('"文书ID" not found in item. unable to save')
        continue
      filename = item[u'文书ID'] + ".txt"
      file_path = "%s/%s" % (save_dir.decode('utf8'), filename)
      overwrite = os.path.isfile(file_path)
      try:
        f = open(file_path, 'w')
        json_str = json.dumps(item, ensure_ascii=False,
                              encoding='utf8', indent=2)
        f.write(json_str.encode('utf8'))
        size = f.tell()
        f.close()
        logging.info('[%s] saved, %d bytes %s', file_path,
                     size, ", overwrite" if overwrite else '')
      except Exception, ex:
        logging.error("Failed to save file %s, ex: %s" % (file_path, ex))


def main():
  # amount of days will retrieve.
  days = DEFAULT_DAYS
  if len(sys.argv) >= 2:
    days = int(sys.argv[1])

  util.init_logging()
  logging.info("Wenshu Crawler started")
  c = Wenshu()
  c.get_cookie()
  c.crawl(days=days)

if __name__ == '__main__':
  main()
