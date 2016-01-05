# coding:utf-8
import sys
import os
import urllib
from PIL import Image
import StringIO
import cgi
import datetime
import math
import time
import json
import logging

dir8 = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, 1], [1, -1], [-1, -1]]
bitcounter = None
basepos = [[7, 0], [20, 0], [33, 0], [46, 0]]


def exeTime(func):
  def newFunc(*args, **args2):
    t0 = time.time()
    back = func(*args, **args2)
    print "@ CAPTCHA %.3fs taken for {%s}" % (time.time() - t0, func.__name__)
    logging.info("CAPTCHA %.3fs" % (time.time() - t0))
    return back
  return newFunc


def colordist(a, b):
  dist = 0
  for i in range(3):
    dist += (a[i] - b[i]) * (a[i] - b[i])
  return math.sqrt(dist)


def countbit(x):
  global bitcounter
  if bitcounter == None:
    bitcounter = []
    for num in range(256):
      bit = 1
      count = 0
      for i in range(8):
        if bit & num:
          count += 1
        bit = bit << 1
      bitcounter.append(count)
  count = 0
  for i in range(3):
    onebyte = (x >> (8 * i)) & 255
    count += bitcounter[onebyte]

  return count


class Captcha(object):

  def __init__(self, im):
    self.im = im
    self.THRESHOLD = 40
    self.mask = {}
    self.chars = {}
    self.compareResult = ""
    self.filename = ""
    LoadDict()

  def printmask(self):
    for j in xrange(self.im.size[1]):  # ��
      for i in xrange(self.im.size[0]):  # ��
        if self.mask.has_key((i, j)):
          print self.mask[(i, j)],
        else:
          if i % 10 == 0:
            print ':',
          elif j % 10 == 0:
            print '~',
          else:
            print '.',
      print
    print

  def updateThreshold(self):
    minv = 165
    first_col = []
    for i in xrange(self.im.size[1]):
      p = self.im.getpixel((0, i))
      first_col.append(min(p[0], p[1], p[2]))
    first_col.sort()
    for i in range(4, len(first_col)):
      minv = min(minv, first_col[i])

    self.THRESHOLD = minv - self.THRESHOLD
    return minv

  def cutBackground(self):
    for i in xrange(self.im.size[0]):  # 列
      for j in xrange(self.im.size[1]):  # 行
        p = self.im.getpixel((i, j))
        if (p[0] + 40 < self.THRESHOLD or p[1] < self.THRESHOLD or p[2] < self.THRESHOLD) and (colordist([75, 190, 70], p) >= 40) and (colordist([135, 120, 150], p) >= 40):
          self.mask[(i, j)] = 1

  def im2bin(self):
    self.binim = []
    for i in xrange(self.im.size[0]):  # 列
      bin = 0
      bit = 1
      for j in xrange(self.im.size[1]):  # 行
        if self.mask.has_key((i, j)) and self.mask[(i, j)] == 1:
          bin |= bit
        bit = bit << 1
      self.binim.append(bin)

  @exeTime
  def process(self):
    self.updateThreshold()
    self.cutBackground()
    self.im2bin()

    result = ""
    for pos in basepos:
      better_trys = []
      for de in CAPTCHADICT:
        """
        if not FASTDICT.has_key(str(de['id'])):
            continue
        for di in FASTDICT[str(de['id'])]:
        """
        for di in range(-1, 2):
          for dj in range(2, 4):
            ti = pos[0] + di
            tj = pos[1] + dj
            rate = self.charmatch(de, ti, tj, 5)
            if rate > 0.35:
              better_trys.append((de, ti, tj, rate))

      maxrate = 0
      maxchar = ''
      maxbase = []
      maxdata = None
      for t in better_trys:
        rate = self.charmatch(t[0], t[1], t[2])
        if rate > maxrate:
          maxchar = t[0]['char']
          maxrate = rate
          maxdata = t
      #print maxrate, maxchar, maxbase
      result += maxchar

      """remove identified char from image(self.binim)"""
      self.removechar(maxdata[0], maxdata[1], maxdata[2])

    return result

  def charmatch(self, de, basei, basej, partly=False):
    matches = 0
    totals = 0
    r = []
    if not partly:
      r = range(len(de['dict']))
    else:
      r = range(1, len(de['dict']), partly)

    for i in r:
      key = de['dict'][i]
      if basej < 0:
        key = key >> (-basej)
      else:
        key = key << basej

      if i + basei < len(self.binim):
        binimg = self.binim[i + basei]
        binv = key & binimg
        match = countbit(binv)
        matches += match
        totals += (countbit(key) + countbit(binimg)) - match
    rate = matches * 1.0 / totals if totals > 0 else 0
    if not partly:
      rate *= (1 + de['count'] * 0.005)
    return rate

  def removechar(self, de, basei, basej):
    for i in range(len(de['dict'])):
      key = de['dict'][i]
      if basej < 0:
        key = key >> (-basej)
      else:
        key = key << basej

      if i + basei < len(self.binim):
        self.binim[i + basei] = key & ~self.binim[i + basei]

CAPTCHADICT = None
FASTDICT = None


def LoadDict():
  global CAPTCHADICT
  if CAPTCHADICT:
    return

  CAPTCHADICT = []
  path = os.path.split(os.path.realpath(__file__))[0]
  f = open(path + '/dict/dict.txt', 'r')
  a = f.read()
  f.close()
  cs = a.split('# ')
  for c in cs:
    if len(c) < 10:
      continue
    lines = c.replace(' ', '').split('\n')[1:]
    width = len(lines[0])
    d = {
      'char': c[0],
      'count': 0,
      'dict': [],
    }
    for col_id in range(width):
      bit = 1
      col_value = 0
      for row in lines:
        if len(row) > col_id and row[col_id] == '1':
          d['count'] += 1
          col_value ^= bit
        bit *= 2
      d['dict'].append(col_value)
    CAPTCHADICT.append(d)

if __name__ == '__main__':
  import util

  while True:
    im = None

    data = ''
    try:
      cookie = util.init_cookie()
      print cookie
      data, res = util.urlfetch(
        'http://shixin.court.gov.cn/image.jsp', cookie=cookie)
      print res.code
      im = Image.open(StringIO.StringIO(data))
    except Exception, ex:
      exit()
    filename = ""
    if not im:
      im = Image.open('image.jpg')

    c = Captcha(im)
    c.filename = filename
    result = c.process()

    c.printmask()
    print result
    print c.compareResult

    str = raw_input()
    if not str == "":
      c.makeDict(str)
