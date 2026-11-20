import sys


def main():
    data = sys.stdin.read().split()
    p = 0
    n, m = int(data[p]), int(data[p + 1]); p += 2
    adj = [[] for _ in range(n + 1)]
    for _ in range(m):
        u, v, w = int(data[p]), int(data[p + 1]), int(data[p + 2]); p += 3
        adj[u].append((w, v))
        adj[v].append((w, u))
    for v in range(1, n + 1):
        adj[v].sort(reverse=True)

    # Для каждой стартовой вершины моделируем мысль, пока состояние
    # (откуда пришли, где сейчас) не повторится.
    visited = [None] * (n + 1)
    for s in range(1, n + 1):
        seen_states = set()
        seen = {s}
        prev, cur = 0, s
        while (prev, cur) not in seen_states:
            seen_states.add((prev, cur))
            nxt = None
            for w, u in adj[cur]:
                if u != prev:
                    nxt = u
                    break
            if nxt is None:      # единственный сосед — тот, откуда пришли
                nxt = prev
            prev, cur = cur, nxt
            seen.add(cur)
        visited[s] = seen
    q = int(data[p]); p += 1
    out = []
    for _ in range(q):
        k = int(data[p]); p += 1
        need = [int(x) for x in data[p:p + k]]; p += k
        out.append(sum(1 for s in range(1, n + 1) if all(c in visited[s] for c in need)))
    print('\n'.join(map(str, out)))  # подзадачи 1-2 (n, m, q <= 1000)


main()
