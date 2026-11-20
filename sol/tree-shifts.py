import sys
from collections import deque


def main():
    data = sys.stdin.read().split()
    p = 0
    T = int(data[p]); p += 1
    out = []
    for _ in range(T):
        n = int(data[p]); p += 1
        w = tuple(int(x) for x in data[p:p + n]); p += n
        g = []
        for v in range(n):
            k = int(data[p]); p += 1
            g.append([int(x) - 1 for x in data[p:p + k]])
            p += k
        L, R = int(data[p]) - 1, int(data[p + 1]) - 1
        p += 2

        def toughness(state):
            return sum(state[u] for v in range(L, R + 1) for u in g[v])

        # Полный перебор достижимых раскладок весов (для n <= 8)
        seen = {w}
        dq = deque([w])
        best = toughness(w)
        while dq:
            cur = dq.popleft()
            for v in range(n):
                nb = g[v]
                if len(nb) < 2:
                    continue
                nxt = list(cur)
                for i, u in enumerate(nb):
                    nxt[u] = cur[nb[(i + 1) % len(nb)]]
                nxt = tuple(nxt)
                if nxt not in seen:
                    seen.add(nxt)
                    dq.append(nxt)
                    best = max(best, toughness(nxt))
        out.append(best)
    print('\n'.join(map(str, out)))


main()
