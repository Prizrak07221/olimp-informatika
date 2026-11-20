import sys
from collections import deque


def main():
    data = sys.stdin.read().split()
    p = 0
    n, q = int(data[p]), int(data[p + 1]); p += 2
    val = [0] + [int(x) for x in data[p:p + n]]; p += n
    adj = [set() for _ in range(n + 1)]
    for _ in range(n - 1):
        u, v = int(data[p]), int(data[p + 1]); p += 2
        adj[u].add(v)
        adj[v].add(u)
    out = []
    for _ in range(q):
        if data[p] == '1':
            v = int(data[p + 1]); p += 2
            nb = sorted(adj[v])
            if len(nb) > 1:
                keep = nb[0]
                for u in nb[1:]:
                    val[keep] += val[u]
                    for w in adj[u]:
                        if w != v:
                            adj[w].discard(u)
                            adj[w].add(keep)
                            adj[keep].add(w)
                    adj[v].discard(u)
                    adj[u] = set()
        else:
            v, u = int(data[p + 1]), int(data[p + 2]); p += 3
            # путь v -> u обходом в ширину, затем сумма значений на нём
            par = {v: 0}
            dq = deque([v])
            while dq:
                x = dq.popleft()
                if x == u:
                    break
                for y in adj[x]:
                    if y not in par:
                        par[y] = x
                        dq.append(y)
            s, x = 0, u
            while x != 0:
                s += val[x]
                x = par[x]
            out.append(s)
    print('\n'.join(map(str, out)))  # O(n) на запрос — подзадача N, Q <= 1000


main()
