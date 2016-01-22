import urllib2
import urllib
import sys
import os
import zlib
import logging
try:
  from bs4 import BeautifulSoup
except:
  import BeautifulSoup
try:
  from pyv8 import PyV8
except:
  import PyV8

DEFAULT_HEADERS = {
  'Accept': '*/*',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'en,zh-CN;q=0.8,zh;q=0.6,zh-TW;q=0.4',
  'Cache-Control': 'no-cache',
  'Referer': 'http://shixin.court.gov.cn/',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'
}

DEFAULT_TIMEOUT = 30
HOMEPAGE_URL = 'http://shixin.court.gov.cn/'

default_opener = urllib2.build_opener()


def urlfetch(url, data=None, cookie='', referer='', opener=default_opener, timeout=DEFAULT_TIMEOUT):
  logging.info("[url]:%s [data]:%s" % (url, data))
  headers = dict(DEFAULT_HEADERS)
  if cookie:
    if isinstance(cookie, dict):
      headers['Cookie'] = ' '.join(['%s=%s;' % x for x in cookie.items()])
    else:
      headers['Cookie'] = cookie
  if referer:
    headers['Referer'] = referer
  if isinstance(data, dict):
    data = urllib.urlencode(data)
  if data:
    headers['Content-Type'] = 'application/x-www-form-urlencoded'

  req = urllib2.Request(url, data, headers)
  #logging.debug("[req headers]: %s" % req.headers)
  res = None
  html = ""
  try:
    res = opener.open(req, timeout=timeout)
    html = res.read()
  except urllib2.HTTPError, ex:
    return ex.read(), ex

  if 'Content-Encoding' in res.headers and res.headers['Content-Encoding'] == 'gzip':
      try:
          html = zlib.decompress(html, 16 + zlib.MAX_WBITS)
      except:
          raise Exception('ungzip error')
  #logging.debug("[res headers]: %s" % res.headers)
  return html, res


def update_cookie(html=None, res=None, cookie=None):
  if html == None and res == None:
    html, res = urlfetch(HOMEPAGE_URL)

  if not cookie:
    cookie = {}
  cookie.update(dict((_resolve_521_html(html).strip(';').split('='),)))
  if 'set-cookie' in res.headers:
    cookie.update(
      dict((res.headers['set-cookie'].split(' ')[0].strip(';').split('='),)))
  return cookie


JS_PREFIX = """var document = {cookie:''};
function setTimeout(f) {}"""


def _resolve_521_html(html):
  soup = BeautifulSoup(html, "html.parser")
  script = soup.script.text
  return _resolve_521_js(script)


def _resolve_521_js(js):
  ctxt = PyV8.JSContext()
  ctxt.enter()
  return ctxt.eval(JS_PREFIX + str(js)).split(' ')[0]


def program_name():
    n = os.path.split(sys.argv[0])[1].split('.')[0]
    return n


def init_logging():
  rootLogger = logging.getLogger()
  formatter = logging.Formatter(
    '%(asctime)s[%(thread)d]%(levelname)s:%(filename)s:%(funcName)s(%(lineno)d): %(message)s')

  path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "log")
  if not os.path.exists(path):
    os.mkdir(path)
  filename = os.path.join(path, '%s.log' % program_name())
  fileHandler = logging.FileHandler(filename)
  fileHandler.setFormatter(formatter)
  rootLogger.addHandler(fileHandler)
  print "logging to: %s" % filename

  console = logging.StreamHandler()
  console.setFormatter(formatter)
  rootLogger.addHandler(console)

  rootLogger.setLevel(logging.DEBUG)
  logging.debug("logging inited")

  """
  from logging.handlers import TimedRotatingFileHandler
  hdlr = TimedRotatingFileHandler(filename,"midnight",1,2)
  if program_name() == 'gp_infoworker':
      hdlr = TimedRotatingFileHandler(filename,"H",1,2)
  hdlr.setFormatter(formatter)
  logging.getLogger('').addHandler(hdlr)
  """
if __name__ == '__main__':
  test_js = r"""var dc="";var t_d={hello:"world",t_c:function(x){if(x==="")return;if(x.slice(-1)===";"){x=x+" ";};if(x.slice(-2)!=="; "){x=x+"; ";};dc=dc+x;}};(function(a){eval(function(p,a,c,k,e,d){e=function(c){return(c<a?"":e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--)d[e(c)]=k[c]||e(c);k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1;};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p;}('b a=a.h(\'l\');b d=[4,2,5,1,3,0];b o=[];b p=0;g(b i=d.c;i--;){o[d[i]]=a[i]}o=o.m(\'\');g(b i=0;i<o.c;i++){u(o.q(i)===\';\'){s(o,p,i);p=i+1}}s(o,p,o.c);k s(t,r,n){j.A(t.B(r,n))};w("f.e=f.e.v(/[\\?|&]x-z/, \'\')",y);',38,38,'|||||||||||var|length||href|location|for|split||t_d|function|=S(mc|join||||charAt||||if|replace|setTimeout|captcha|1500|challenge|t_c|substring'.split('|'),0,{}));})('pires=Sat, 02-Jan-16 15:33=S(mctI02zf6%2BuMgoHau=S(mc:53 GMT;Path=/;=S(mcclearance=1451745233.497|0|aY=S(mcSpJ6v0rnCc%3D;Ex=S(mc__jsl_');document.cookie=dc;"""
  print _resolve_521_js(test_js)
