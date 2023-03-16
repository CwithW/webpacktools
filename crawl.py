# crawl index.hash.js, pages.xxx.hash.js from index.html


import os
import re
import sys
import json
import time
import requests
import ast
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlparse
TIMESTAMP = str(int(time.time() * 1000))
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}
rs = requests.Session()
rs.headers.update(headers)
rs.verify = False
rs.verify = False
rs.trust_env = False
os.environ['CURL_CA_BUNDLE'] = ""  # or whaever other is interfering with
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

def make_safe_filename(s):
    def safe_char(c):
        if c.isalnum():
            return c
        else:
            return "_"
    return "".join(safe_char(c) for c in s).rstrip("_")

# download one file to projectName_TIMESTAMP/path


def download(projectName, absoluteUrl):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parsed_url = urlparse(absoluteUrl)
    # download path to target/path
    filepath = current_dir + os.path.sep + \
        make_safe_filename(projectName+"_"+TIMESTAMP) + \
        os.path.sep + parsed_url.path + parsed_url.params + parsed_url.query
    if(os.path.exists(filepath)):
        return filepath
    filedir = os.path.dirname(filepath)
    os.makedirs(filedir, exist_ok=True)
    logger.debug("Download %s => %s" % (absoluteUrl, filepath))
    response = requests.get(absoluteUrl)
    with open(filepath, 'wb') as f:
        f.write(response.content)
    return filepath


def ensureAbsoulteUrl(url, base_url):
    if url.startswith("http://") or url.startswith("https://"):
        return url
    elif url.startswith("/"): # js中 /xxx 一定是从根目录开始的
        # 将base_url的协议和域名提取出来
        parsed_url = urlparse(base_url)
        return parsed_url.scheme + "://" + parsed_url.netloc + url
    else:
        # 相对路径
        return base_url + url

def parseIndex(indexContent, base_url):
    result = []
    # find all pages.xxx.hash.js
    if not base_url.endswith("/"):
        base_url = base_url + "/"
    # TODO 做成动态匹配 s.src=function(e){return r.p+"static/js/"+({
    JS_PATH_PREFIX = "static/js/"
    JS_PATH_SEP = "."
    JS_PATH_SUFFIX = ".js"
    # 匹配那一大段pages
    regex_pages = r'\[e\]\|\|e\)\+"\."\+({.*})\[e\]\+"\.js"}'
    pages = re.findall(regex_pages, indexContent)
    if len(pages) == 0:
        logger.error("Can not found pages.xxx.hash.js")
        return result
    pages = pages[0]
    pages = ast.literal_eval(pages)
    # {"im-chat-chat~im-group-join-group~im-information-groupInfo~im-information-information~im-information-~6fb7ce4a":"c17e7960",... }
    for key in pages.keys():
        path = JS_PATH_PREFIX + key + JS_PATH_SEP + pages[key] + JS_PATH_SUFFIX
        logger.info("Found pages.js => %s" % path)
        result.append((base_url + path, key))
    return result


# parse index.html to found
# index.hash.js
# chunk-vendors
def crawl(base_url):
    project_name = base_url
    # what js we have found (absolute_path, name)
    founds = []
    logger.info("Fetch index.html => %s" % base_url)
    index_request = rs.get(base_url)
    # 检测如果302出现了 就要修改base_url
    if index_request.history:
        base_url = index_request.url
        # 检测 /h5/ 和 /h5/index.html 
        if not base_url.endswith("/"):
            base_url = base_url.rsplit('/',1)[0] + "/"
        logger.info("Base url is moved to %s" % base_url)
    page = index_request.text
    page = BeautifulSoup(page, 'html.parser')
    script_tags = page.find_all('script')
    # read src attribute of script tags
    for tag in script_tags:
        src = tag['src'] if 'src' in tag.attrs else None
        if src is None:
            continue
        if re.match(r'.*chunk-vendors\..*\.js$', src):
            # this is chunk-vendors.js
            logger.info("Found chunk-vendors.js => %s" % src)
            founds.append((ensureAbsoulteUrl(src, base_url), "chunk-vendors"))
        elif re.match(r'.*(?:index|app)\..*\.js$', src):
            # this is index.js
            logger.info("Found index.js => %s" % src)
            founds.append((ensureAbsoulteUrl(src, base_url), "index"))
    for item in founds:
        if item[1] == 'index':
            # download index.js
            with open(download(project_name, item[0])) as file:
                index = file.read()
            founds_page = parseIndex(index, base_url)
            founds.extend(founds_page)
    # download all if not
    logger.info("Downloading all files")
    for item in founds:
        print(item[1],end="\r")
        download(project_name, item[0])


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 crawler.py http://example.com/ (do not add index.html)")
        return
    target = sys.argv[1]
    # add log file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = current_dir + os.path.sep + \
        make_safe_filename(target+"_"+TIMESTAMP)
    os.mkdir(filepath)
    logger.addHandler(logging.FileHandler(filepath+os.path.sep+"log.txt"))
    crawl(target)


if __name__ == '__main__':
    main()
