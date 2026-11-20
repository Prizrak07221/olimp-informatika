import sys


def solve_case(n, w, g, L, R):
    """g — списки соседей (0-индексация), особые вершины L..R (0-индексация)."""
    coef = [0] * n
    for v in range(L, R + 1):
        for u in g[v]:
            coef[u] += 1
    # компоненты внутри доли: вершины, связанные общим соседом степени >= 2
    par = list(range(n))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for v in range(n):
        if len(g[v]) >= 2:
            for u in g[v][1:]:
                par[find(u)] = find(g[v][0])
    gens = {}
    for v in range(n):
        if len(g[v]) >= 2:
            gens.setdefault(find(g[v][0]), []).append(v)
    comps = {}
    for u in range(n):
        comps.setdefault(find(u), []).append(u)

    total = 0
    for root, verts in comps.items():
        gv = gens.get(root, [])
        if not gv:                                  # ничего не двигается
            total += sum(w[u] * coef[u] for u in verts)
        elif len(gv) == 1:                          # один цикл — только повороты
            cyc = g[gv[0]]
            k = len(cyc)
            best = max(sum(w[cyc[(i + s) % k]] * coef[cyc[i]] for i in range(k)) for s in range(k))
            total += best
        else:
            ws = sorted(w[u] for u in verts)
            byc = sorted(verts, key=lambda u: coef[u])
            cs = [coef[u] for u in byc]
            best = sum(x * y for x, y in zip(ws, cs))
            any_even = any(len(g[v]) % 2 == 0 for v in gv)   # цикл чётной длины — нечётная перестановка
            distinct = len(set(ws)) == len(ws) and len(set(cs)) == len(cs)
            if not any_even and distinct:
                # доступны только чётные перестановки: считаем чётность нужной
                target = {}                  # вершина -> какой вес должен на ней оказаться
                for u, x in zip(byc, ws):
                    target[u] = x
                where = {w[u]: u for u in verts}     # вес -> где он сейчас
                perm = {where[target[u]]: u for u in verts}  # откуда -> куда
                seen = set()
                cycles = 0
                for u in verts:
                    if u not in seen:
                        cycles += 1
                        x = u
                        while x not in seen:
                            seen.add(x)
                            x = perm[x]
                if (len(verts) - cycles) % 2 == 1:
                    loss = min((ws[i + 1] - ws[i]) * (cs[i + 1] - cs[i]) for i in range(len(ws) - 1))
                    best -= loss
            total += best
    return total


def main():
    data = sys.stdin.read().split()
    p = 0
    T = int(data[p]); p += 1
    out = []
    for _ in range(T):
        n = int(data[p]); p += 1
        w = [int(x) for x in data[p:p + n]]; p += n
        g = []
        for v in range(n):
            k = int(data[p]); p += 1
            g.append([int(x) - 1 for x in data[p:p + k]]); p += k
        L, R = int(data[p]) - 1, int(data[p + 1]) - 1; p += 2
        out.append(solve_case(n, w, g, L, R))
    print('\n'.join(map(str, out)))


if __name__ == '__main__':
    main()
