import urllib2
import urllib
import httplib
httplib.HTTPConnection.debuglevel = 1
import sys
import os
import zlib
import logging
from bs4 import BeautifulSoup
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

DEFAULT_TIMEOUT = 120
HOMEPAGE_URL = 'http://shixin.court.gov.cn/'


def urlfetch(url, data=None, cookie={}, referer='', opener=None, timeout=DEFAULT_TIMEOUT):
  logging.info("[url]:%s [data]:%s" % (url, data))
  headers = dict(DEFAULT_HEADERS)
  if cookie:
    headers['Cookie'] = ' '.join(['%s=%s;' % x for x in cookie.items()])
  if referer:
    headers['Referer'] = referer
  if isinstance(data, dict):
    data = urllib.urlencode(data)
  if data:
    headers['Content-Type'] = 'application/x-www-form-urlencoded'

  if not opener:
    opener = urllib2.build_opener(SmartRedirectHandler(cookie))
  req = urllib2.Request(url, data, headers)
  #logging.debug("[req headers]: %s" % req.headers)
  res = None
  html = ""
  try:
    res = opener.open(req, timeout=timeout)
    html = res.read()
  except urllib2.HTTPError, ex:
    if 'Set-Cookie' in ex.headers:
      cookie.update(_cookie_to_dict([ex.headers['set-cookie']]))
    logging.debug("encounter a HTTPErrpr: %s" % ex)
    return ex.read(), ex

  if 'Content-Encoding' in res.headers and res.headers['Content-Encoding'] == 'gzip':
      try:
          html = zlib.decompress(html, 16 + zlib.MAX_WBITS)
      except:
          raise Exception('ungzip error')
  if 'Set-Cookie' in res.headers:
    cookie.update(_cookie_to_dict([res.headers['set-cookie']]))
  #logging.debug("[res headers]: %s" % res.headers)
  return html, res


class SmartRedirectHandler(urllib2.HTTPRedirectHandler):

  def __init__(self, cookie):
    self.cookie = cookie

  def http_error_302(self, req, fp, code, msg, headers):
    if 'Set-Cookie' in headers:
      print _cookie_to_dict([headers['set-cookie']])
      self.cookie.update(_cookie_to_dict([headers['set-cookie']]))
      req.headers['Cookie'] = ' '.join(['%s=%s;' % x for x in self.cookie.items()])
    result = urllib2.HTTPRedirectHandler.http_error_302(
      self, req, fp, code, msg, headers)
    result.status = code
    return result


def update_cookie(html=None, res=None, cookie=None):
  if html == None and res == None:
    html, res = urlfetch(HOMEPAGE_URL)

  if not cookie:
    cookie = {}
  cookie.update(_resolve_521_html(html))
  if 'set-cookie' in res.headers:
    cookie.update(_cookie_to_dict([res.headers['set-cookie']]))
  return cookie


JS_PREFIX = """var document = {cookies:[]};
Object.defineProperty(document, "cookie", { set: function (x) { this.cookies.push(x); } })
function setTimeout(f) {};
window = {
  innerWidth: 1024, innerHeight: 768,
  screenX: 10, screenY: 10,
  screen: {width:800, height:600}
};"""

def _cookie_to_dict(cookie_array):
  cookies = map(lambda x: x.split('; ')[0], cookie_array)
  cookies = map(lambda x: x.split('=', 1), cookies)
  return dict(cookies)


def _resolve_521_html(html):
  soup = BeautifulSoup(html, "html.parser")
  script = soup.script.text
  return _resolve_521_js(script)


def _resolve_521_js(js):
  ctxt = PyV8.JSContext()
  ctxt.enter()
  ctxt.eval(JS_PREFIX)
  ctxt.eval(str(js))
  cookies = ctxt.eval('document.cookies')
  return _cookie_to_dict(cookies)


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
  #test_js = r"""var dc="";var t_d={hello:"world",t_c:function(x){if(x==="")return;if(x.slice(-1)===";"){x=x+" ";};if(x.slice(-2)!=="; "){x=x+"; ";};dc=dc+x;}};(function(a){eval(function(p,a,c,k,e,d){e=function(c){return(c<a?"":e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--)d[e(c)]=k[c]||e(c);k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1;};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p;}('b a=a.h(\'l\');b d=[4,2,5,1,3,0];b o=[];b p=0;g(b i=d.c;i--;){o[d[i]]=a[i]}o=o.m(\'\');g(b i=0;i<o.c;i++){u(o.q(i)===\';\'){s(o,p,i);p=i+1}}s(o,p,o.c);k s(t,r,n){j.A(t.B(r,n))};w("f.e=f.e.v(/[\\?|&]x-z/, \'\')",y);',38,38,'|||||||||||var|length||href|location|for|split||t_d|function|=S(mc|join||||charAt||||if|replace|setTimeout|captcha|1500|challenge|t_c|substring'.split('|'),0,{}));})('pires=Sat, 02-Jan-16 15:33=S(mctI02zf6%2BuMgoHau=S(mc:53 GMT;Path=/;=S(mcclearance=1451745233.497|0|aY=S(mcSpJ6v0rnCc%3D;Ex=S(mc__jsl_');document.cookie=dc;"""
  test_js = r"""eval(function(p,a,c,k,e,d){e=function(c){return(c<a?'':e(parseInt(c/a)))+((c=c%a)>32?String.fromCharCode(c+32):c.toString(33))};if(!''.replace(/^/,String)){while(c--)d[e(c)]=k[c]||e(c);k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p}('15 D="k";15 1a="i";15 1b="l";15 11=d;15 F = "e+/=";J g(10) {15 U, N, R;15 o, p, q;R = 10.S;N = 0;U = "";17 (N < R) {o = 10.s(N++) & 6;O (N == R) {U += F.r(o >> 9);U += F.r((o & 1) << b);U += "==";n;}p = 10.s(N++);O (N == R) {U += F.r(o >> 9);U += F.r(((o & 1) << b) | ((p & 5) >> b));U += F.r((p & 4) << 9);U += "=";n;}q = 10.s(N++);U += F.r(o >> 9);U += F.r(((o & 1) << b) | ((p & 5) >> b));U += F.r(((p & 4) << 9) | ((q & 3) >> c));U += F.r(q & 2);}W U;}J H(){15 16= 19.Q||B.C.u||B.m.u;15 K= 19.P||B.C.t||B.m.t;O (16*K <= 8) {W 14;}15 1d = 19.Y;15 1e = 19.Z;O (1d + 16 <= 0 || 1e + K <= 0 || 1d >= 19.X.18 || 1e >= 19.X.M) {W 14;}W G;}J h(){15 12 = 1a+1b;15 L = 0;15 N = 0;I(N = 0; N < 12.S; N++) {L += 12.s(N);}L *= a;L += 7;W "j"+L;}J f(){O(H()) {} E {15 A = "";  A = "1c="+g(11.13()) + "; V=/";B.w = A; 15 v = h();A = "1a="+g(v.13()) + "; V=/";B.w = A; 19.T=D;}}f();',59,74,'0|0x3|0x3f|0xc0|0xf|0xf0|0xff|111111|120000|2|23|4|6|8|ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789|HXXTTKKLLPPP5|KTKY2RBD9NHPBCIHV9ZMEQQDARSLVFDU|QWERTASDFGXYSF|RANDOMSTR1440|WZWS_CONFIRM_PREFIX_LABEL8|/findd|STRRANDOM1440|body|break|c1|c2|c3|charAt|charCodeAt|clientHeight|clientWidth|confirm|cookie|cookieString|document|documentElement|dynamicurl|else|encoderchars|false|findDimensions|for|function|h|hash|height|i|if|innerHeight|innerWidth|len|length|location|out|path|return|screen|screenX|screenY|str|template|tmp|toString|true|var|w|while|width|window|wzwschallenge|wzwschallengex|wzwstemplate|x|y'.split('|'),0,{}))"""
  print _resolve_521_js(test_js)
