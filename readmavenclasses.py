import urllib.request
import urllib.error
import io

import readjar


with open('class_jars.txt', 'r') as class_jars:
    for url in class_jars:
        print(url)
        try:
            resp = urllib.request.urlopen(url)
            if resp.getcode() == 200:
                readjar.read_jar(io.BytesIO(resp.read()), parse=True)
        except urllib.error.HTTPError:
            pass