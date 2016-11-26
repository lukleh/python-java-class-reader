from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import urllib.parse
import io

import readjar

class_jars = open('class_jars.txt', 'w')


def start(url):
    print("in", url)
    try:
        resp = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        return
    soup = BeautifulSoup(resp.read(), "html.parser")
    for u in soup("a"):
        next_url = urllib.parse.urljoin(url, u['href'])
        if next_url < url or next_url == url:
            continue
        if next_url.endswith('/'):
            start(next_url)
        elif next_url.endswith('.jar'):
            if not next_url.endswith('-javadoc.jar') and not next_url.endswith('-sources.jar'):
                print(next_url)
                try:
                    resp = urllib.request.urlopen(next_url)
                    if resp.getcode() == 200:
                        if readjar.read_jar(io.BytesIO(resp.read()), parse=False) is True:
                            class_jars.write(next_url + '\n')
                except urllib.error.HTTPError:
                    pass

start("https://repo1.maven.org/maven2/")
class_jars.close()
