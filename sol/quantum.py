import sys
from bisect import bisect_right


def main():
    data = sys.stdin.read().split()
    p = 0
    n, m = int(data[p]), int(data[p + 1]); p += 2
    preds = [[] for _ in range(n + 1)]
    to_one = [False] * (n + 1)
    edges = set()
    for _ in range(m):
        u, v = int(data[p]), int(data[p + 1]); p += 2
        if v == 1:
            to_one[u] = True
        else:
            preds[v].append(u)
            edges.add(u * (n + 1) + v)
    k, q = int(data[p]), int(data[p + 1]); p += 2
    a = [0] + [int(x) for x in data[p:p + k]]; p += k
    occ = [[] for _ in range(n + 1)]
    for i in range(1, k + 1):
        occ[a[i]].append(i)
    by_l = [[] for _ in range(k + 2)]
    for qi in range(q):
        l, r = int(data[p]), int(data[p + 1]); p += 2
        by_l[l].append((r, qi))

    INF = k + 1
    t = [INF] * (n + 1)          # момент опустошения вершины при старте с l
    bit = [0] * (k + 2)

    def bit_add(i, d):
        while i <= k:
            bit[i] += d
            i += i & -i

    def bit_sum(i):
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s

    work = []

    def lower(v, val):
        old = t[v]
        if old <= k:
            bit_add(old, -1)
        bit_add(val, 1)
        t[v] = val
        work.append((v, old, val))

    ans = [0] * q
    for l in range(k, 0, -1):
        x = a[l]
        if to_one[x] and t[x] > l:
            lower(x, l)
        while work:
            v, old, new = work.pop()
            hi = min(old, k)
            if len(preds[v]) <= hi - new:
                for w in preds[v]:
                    if to_one[w]:
                        continue
                    oc = occ[w]
                    j = bisect_right(oc, new)
                    if j < len(oc) and oc[j] < t[w]:
                        lower(w, oc[j])
            else:
                base = v
                for i in range(new + 1, hi + 1):
                    w = a[i]
                    if i < t[w] and not to_one[w] and w * (n + 1) + base in edges:
                        lower(w, i)
        for r, qi in by_l[l]:
            ans[qi] = bit_sum(r)
    print('\n'.join(map(str, ans)))


main()
