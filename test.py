import pysnooper

@pysnooper.snoop(r'd:\test.log')
def strSplit(str):
    r = []
    for i in str:
        r.append(i)
    return r

s = strSplit('gyhthnf')
print('aaaa', s)