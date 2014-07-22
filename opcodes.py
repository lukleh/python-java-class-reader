
import csv
import re

opcodes = dict()


with open('opcodes.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        val = int('0x' + row[0], 0)
        code = dict(name=row[1], desc=row[4], params=0)
        if not row[2]:
            pass
        elif re.match('\d:.*', row[2]):
            code['params'] = int(row[2][0])
        else:
            code['params'] = -1
            print row[2]
        opcodes[val] = code


def arr2int(arr):
    aval = 0
    for i, v in enumerate(arr.reverse()):
        aval += v << (i * 8)
    return aval


def decode(ba):
    out = []
    d = dict(pos=0)

    def bstream(barr):
        for bt in barr:
            d['pos'] += 1
            yield bt
    bs = bstream(ba)
    while True:
        try:
            b = bs.next()
        except StopIteration:
            break
        opc = opcodes[b]
        if opc['params'] == 0:
            out.append(opc['name'])
        elif opc['params'] > 0:
            att = [bs.next() for _ in xrange(opc['params'])]
            out.append([opc['name'], att])
        elif opc['params'] < 0:
            if b == 170:
                padd = [bs.next() for _ in xrange(d['pos'] % 4)]
                lh = [bs.next() for _ in xrange(12)]
                low = arr2int(lh[4:8])
                high = arr2int(lh[8:12])
                offsets = [bs.next() for _ in xrange(high - low + 1)]
                out.append([opc['name'], padd + lh + offsets])
            elif b == 171:
                padd = [bs.next() for _ in xrange(d['pos'] % 4)]
                dp = [bs.next() for _ in xrange(8)]
                npairs = arr2int(dp[4:8])
                offsets = [bs.next() for _ in xrange(npairs)]
                out.append([opc['name'], padd + dp + offsets])
            elif b == 196:
                op1 = bs.next()
                if op1 == 84:
                    att = [bs.next() for _ in xrange(4)]
                else:
                    att = [bs.next() for _ in xrange(2)]
                out.append([opc['name'], [op1] + att])
            else:
                raise Exception('cannot decode bytecode')
        else:
            raise Exception('cannot decode bytecode')

    return out
