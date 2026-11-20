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
    # ориентированные рёбра: id(u -> v)
    eid = {}
    tail, head = [], []
    for u in range(1, n + 1):
        for _, v in adj[u]:
            eid[(u, v)] = len(tail)
            tail.append(u)
            head.append(v)
    E = len(tail)
    # переход: из ребра (u -> v) в (v -> лучший сосед v, кроме u; если сосед один — обратно)
    nxt = [0] * E
    for e in range(E):
        u, v = tail[e], head[e]
        nb = adj[v]
        if len(nb) == 1:
            w = u
        else:
            w = nb[0][1] if nb[0][1] != u else nb[1][1]
        nxt[e] = eid[(v, w)]
    # циклы функционального графа
    state = [0] * E          # 0 — не видели, 1 — в текущем пути, 2 — готово
    on_cycle = [False] * E
    for s in range(E):
        if state[s]:
            continue
        path = []
        x = s
        while state[x] == 0:
            state[x] = 1
            path.append(x)
            x = nxt[x]
        if state[x] == 1:        # нашли новый цикл
            i = path.index(x)
            for y in path[i:]:
                on_cycle[y] = True
        for y in path:
            state[y] = 2
    # обратный лес: дети ребра e — рёбра, из которых переходят в e (кроме ребёр цикла)
    children = [[] for _ in range(E)]
    for e in range(E):
        if not on_cycle[e]:
            children[nxt[e]].append(e)
    tin = [0] * E
    tout = [0] * E
    comp_l = [0] * E          # отрезок компоненты (для рёбер на цикле)
    comp_r = [0] * E
    is_start = [0] * E        # ребро — первый шаг мысли из какой-то вершины
    for s in range(1, n + 1):
        is_start[eid[(s, adj[s][0][1])]] = 1
    order = []
    seen = [False] * E
    timer = 0
    for c in range(E):
        if not on_cycle[c] or seen[c]:
            continue
        cyc = []
        x = c
        while not seen[x]:
            seen[x] = True
            cyc.append(x)
            x = nxt[x]
        start = timer
        for root in cyc:
            stack = [(root, 0)]
            while stack:
                x, st = stack.pop()
                if st == 0:
                    tin[x] = timer
                    order.append(x)
                    timer += 1
                    stack.append((x, 1))
                    for ch in children[x]:
                        stack.append((ch, 0))
                else:
                    tout[x] = timer - 1
        for x in order[start:timer]:
            comp_l[x], comp_r[x] = start, timer - 1
    pref = [0] * (E + 1)
    for i, x in enumerate(order):
        pref[i + 1] = pref[i] + is_start[x]

    def good_intervals(c):
        """Отрезки обхода, из которых мысль проходит через вершину c."""
        res = []
        for k in range(min(2, len(adj[c]))):
            e = eid[(c, adj[c][k][1])]
            if on_cycle[e]:
                res.append((comp_l[e], comp_r[e]))
            else:
                res.append((tin[e], tout[e]))
        return res

    def normalize(iv):
        iv = sorted(set(iv))
        out = []
        for l, r in iv:
            if out and l <= out[-1][1]:
                out[-1] = (out[-1][0], max(out[-1][1], r))
            else:
                out.append((l, r))
        return out

    q = int(data[p]); p += 1
    ans = []
    for _ in range(q):
        k = int(data[p]); p += 1
        cs = [int(x) for x in data[p:p + k]]; p += k
        cur = normalize(good_intervals(cs[0]))
        for c in cs[1:]:
            other = normalize(good_intervals(c))
            new = []
            for a, b in cur:
                for x, y in other:
                    l, r = max(a, x), min(b, y)
                    if l <= r:
                        new.append((l, r))
            cur = normalize(new)
            if not cur:
                break
        ans.append(sum(pref[r + 1] - pref[l] for l, r in cur))
    print('\n'.join(map(str, ans)))


main()
