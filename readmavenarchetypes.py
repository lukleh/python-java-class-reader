import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import io

import readjar


tree = ET.parse('archetype-catalog.xml')
root = tree.getroot()

with open('class_jars.txt', 'w') as class_jars:
    for archetype in root.iter('archetype'):
        arch = {child.tag: child.text for child in archetype}
        # if 'archetype' in arch['groupId'] or 'archetype' in arch['artifactId']:
        #     print('archetype, passing: %s %s %s' % (arch['groupId'], arch['artifactId'], arch['version']))
        #     continue
        url_template = "http://uk.maven.org/maven2/{group_id}/{artifactId}/{version}/{artifactId}-{version}.jar"
        url = url_template.format(group_id='/'.join(arch['groupId'].split('.')),
                                  version=arch['version'],
                                  artifactId=arch['artifactId'])
        print(url)
        try:
            resp = urllib.request.urlopen(url)
            if resp.getcode() == 200:
                if readjar.read_jar(io.BytesIO(resp.read()), parse=False) is True:
                    class_jars.write(url + '\n')
        except urllib.error.HTTPError:
            pass
