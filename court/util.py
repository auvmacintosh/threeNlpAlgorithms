import urllib2
import logging
from bs4 import BeautifulSoup
from pyv8 import PyV8

DEFAULT_HEADERS = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  'Accept-Encoding': 'gzip, deflate, sdch',
  'Accept-Language': 'en,zh-CN;q=0.8,zh;q=0.6,zh-TW;q=0.4',
  'Cache-Control': 'no-cache',
  'Upgrade-Insecure-Requests': '1',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'
}

DEFAULT_TIMEOUT = 10

default_opener = urllib2.build_opener()


def urlfetch(url, data=None, cookie='', referer='', opener=default_opener, timeout=DEFAULT_TIMEOUT):
  logging.info("[url]:%s [data]:%s" % (url, data))
  headers = dict(DEFAULT_HEADERS)
  if cookie:
    headers['Cookie'] = cookie
  if referer:
    headers['Referer'] = referer

  req = urllib2.Request(url, data, headers)
  res = None
  html = ""
  try:
    res = opener.open(req, timeout=timeout)
    html = res.read()
  except urllib2.HTTPError, ex:
    return ex.read(), ex
  return html, res


def init_cookie():
  html, res = urlfetch('http://shixin.court.gov.cn/')
  return ' '.join([_resolve_521_html(html), res.headers['set-cookie'].split(' ')[0]])


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

if __name__ == '__main__':
  test_js = r"""var dc="";var t_d={hello:"world",t_c:function(x){if(x==="")return;if(x.slice(-1)===";"){x=x+" ";};if(x.slice(-2)!=="; "){x=x+"; ";};dc=dc+x;}};(function(a){eval(function(p,a,c,k,e,d){e=function(c){return(c<a?"":e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--)d[e(c)]=k[c]||e(c);k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1;};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p;}('b a=a.h(\'l\');b d=[4,2,5,1,3,0];b o=[];b p=0;g(b i=d.c;i--;){o[d[i]]=a[i]}o=o.m(\'\');g(b i=0;i<o.c;i++){u(o.q(i)===\';\'){s(o,p,i);p=i+1}}s(o,p,o.c);k s(t,r,n){j.A(t.B(r,n))};w("f.e=f.e.v(/[\\?|&]x-z/, \'\')",y);',38,38,'|||||||||||var|length||href|location|for|split||t_d|function|=S(mc|join||||charAt||||if|replace|setTimeout|captcha|1500|challenge|t_c|substring'.split('|'),0,{}));})('pires=Sat, 02-Jan-16 15:33=S(mctI02zf6%2BuMgoHau=S(mc:53 GMT;Path=/;=S(mcclearance=1451745233.497|0|aY=S(mcSpJ6v0rnCc%3D;Ex=S(mc__jsl_');document.cookie=dc;"""
  print _resolve_521_js(test_js)
