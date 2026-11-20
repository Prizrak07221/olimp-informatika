import sys


def main():
    data = sys.stdin.read().split()
    p = 0
    n, m = int(data[p]), int(data[p + 1]); p += 2
    out_edges = [[] for _ in range(n + 1)]
    for _ in range(m):
        u, v = int(data[p]), int(data[p + 1]); p += 2
        out_edges[u].append(v)
    k, q = int(data[p]), int(data[p + 1]); p += 2
    a = [int(x) for x in data[p:p + k]]; p += k
    res = []
    for _ in range(q):
        l, r = int(data[p]) - 1, int(data[p + 1]) - 1
        p += 2
        # Электрон в v уходит, если у v есть ребро в вершину 1
        # или в вершину, из которой электрон уже ушёл.
        empty = {1}
        signals = 0
        for i in range(l, r + 1):
            v = a[i]
            if v in empty:
                continue
            if any(u in empty for u in out_edges[v]):
                empty.add(v)
                signals += 1
        res.append(signals)
    print('\n'.join(map(str, res)))  # O(q * k * deg): подзадачи 1-2


main()
