import zipfile
import sys

import readclass


def read_jar(f, parse=True):
    has_classes = False
    with zipfile.ZipFile(f) as myzip:
        for zinfo in myzip.infolist():
            if zinfo.filename.endswith('.class'):
                print(zinfo.filename)
                has_classes = True
                if parse:
                    with myzip.open(zinfo.filename) as myfile:
                        try:
                            jc = readclass.JavaClass(myfile.read())
                            jc.decode()
                            #jc.print_out()
                        except Exception as e:
                            print(e)
    return has_classes

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        read_jar(f.read())
