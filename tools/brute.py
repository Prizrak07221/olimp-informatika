"""Медленные, но заведомо верные решения для сверки на маленьких тестах."""
import itertools
from collections import deque
from functools import lru_cache

from common import mst_weight


def groups(inp):
    d = inp.split()
    n, A, B = map(int, d[:3])
    r = list(map(int, d[3:3 + n]))
    best = None

    def rec(i, gs):
        nonlocal best
        if i == n:
            if all(A <= len(g) <= B for g in gs):
                val = max(max(g) - min(g) for g in gs)
                if best is None or val < best:
                    best = val
            return
        for g in gs:
            if len(g) < B:
                g.append(r[i]); rec(i + 1, gs); g.pop()
        gs.append([r[i]]); rec(i + 1, gs); gs.pop()
    rec(0, [])
    return str(best)


def hanabi(inp):
    d = inp.split()
    q = int(d[0]); p = 1
    cards = []  # [ (c, v), set кандидатов ]
    out = []
    for _ in range(q):
        t = d[p]; x = d[p + 1]; p += 2
        if t == '1':
            cards.insert(0, [(x[0], int(x[1])), {(c, v) for c in 'ABCDE' for v in range(1, 6)}])
        elif t == '2':
            v = int(x)
            for (cv, cand) in cards:
                cand &= {z for z in cand if (z[1] == v) == (cv[1] == v)}
        elif t == '3':
            for (cv, cand) in cards:
                cand &= {z for z in cand if (z[0] == x) == (cv[0] == x)}
        else:
            out.append('YES' if len(cards[int(x) - 1][1]) == 1 else 'NO')
    return '\n'.join(out)


def _is_psp(t):
    bal = 0
    for ch in t:
        bal += 1 if ch == '(' else -1
        if bal < 0:
            return False
    return bal == 0 and len(t) > 0


def brackets(inp):
    s = inp.split()[1]
    seen = {s}
    dq = deque([s])
    while dq:
        cur = dq.popleft()
        L = len(cur)
        for i in range(L):
            for j in range(i + 2, L, 2):
                if not _is_psp(cur[i:j]):
                    continue
                for k in range(j + 2, L + 1, 2):
                    if _is_psp(cur[j:k]):
                        nxt = cur[:i] + cur[j:k] + cur[i:j] + cur[k:]
                        if nxt not in seen:
                            seen.add(nxt); dq.append(nxt)
    return str(len(seen) % (10**9 + 7))


def hurdles(inp):
    d = list(map(int, inp.split()))
    n, h, x, y = d[:4]
    a = d[4:4 + n]
    top = max(max(a), h)
    INF = float('inf')
    dp = {h: 0}
    for ai in a:
        nd = {}
        for hc, cost in dp.items():
            for H in range(hc, top + 1):
                c = cost + (H - hc) * x + max(0, ai - H) * y
                if nd.get(H, INF) > c:
                    nd[H] = c
        dp = nd
    return str(min(dp.values()))


def target_mst(inp):
    d = list(map(int, inp.split()))
    n, m, W = d[:3]
    edges, rng = [], []
    for i in range(m):
        u, v, l, r = d[3 + 4 * i:7 + 4 * i]
        edges.append((u, v)); rng.append(range(l, r + 1))
    for c in itertools.product(*rng):
        if mst_weight(n, edges, c) == W:
            return 'possible\n' + '\n'.join(map(str, c))
    return 'impossible'


def contact(inp):
    d = inp.split()
    n = int(d[0]); words = d[1:1 + n]
    res = []
    for s in words:
        cnt = 0
        for mask in range(1 << n):
            T = [words[i] for i in range(n) if mask >> i & 1]

            def can(k, rest):
                if k == len(s):
                    return not rest
                for i, w in enumerate(rest):
                    if w[:k] != s[:k]:
                        continue
                    nr = rest[:i] + rest[i + 1:]
                    if w == s:
                        if not nr:
                            return True
                        continue
                    if can(k + 1, nr):
                        return True
                return False
            if can(1, T):
                cnt += 1
        res.append(cnt)
    return '\n'.join(map(str, res))


def _grip_brute(c):
    best = -1
    for p in set(itertools.permutations(c)):
        best = max(best, min(p[i] + p[i + 1] for i in range(len(p) - 1)))
    return best


def akserek(inp):
    d = list(map(int, inp.split()))
    n, m = d[:2]
    a = tuple(sorted(d[2:2 + n])); b = tuple(sorted(d[2 + n:2 + n + m]))

    @lru_cache(None)
    def grip(S):
        return _grip_brute(S)

    @lru_cache(None)
    def go(S, rem):
        f = grip(S); best = 0
        for i, x in enumerate(rem):
            if x <= f and (i == 0 or rem[i - 1] != x):
                best = max(best, 1 + go(tuple(sorted(S + (x,))), rem[:i] + rem[i + 1:]))
        return best
    return str(go(a, b))


def bitcount(inp):
    d = list(map(int, inp.split()))
    n, k = d[:2]; a = d[2:2 + n]
    bits = max(a).bit_length()
    return str(min(sum(bin(v + s).count('1') ** k for v in a) for s in range(1 << (bits + 3))))


def perm_sort(inp):
    d = list(map(int, inp.split()))
    n = d[0]; p = d[1:1 + n]; q = d[1 + n]
    qs = [(d[2 + n + 2 * i] - 1, d[3 + n + 2 * i] - 1) for i in range(q)]

    def solve(p):
        start = (tuple(p), 0)
        dist = {start: 0}; dq = deque([start])
        target = tuple(sorted(p))
        while dq:
            cur, mask = dq.popleft()
            if cur == target:
                return dist[(cur, mask)]
            for i in range(n - 1):
                if not mask >> i & 1:
                    c = list(cur); c[i], c[i + 1] = c[i + 1], c[i]
                    st = (tuple(c), mask | 1 << i)
                    if st not in dist:
                        dist[st] = dist[(cur, mask)] + 1; dq.append(st)
        return -1
    out = [solve(p)]
    for x, y in qs:
        p[x], p[y] = p[y], p[x]
        out.append(solve(p))
    return '\n'.join(map(str, out))


def table_area(inp):
    d = list(map(int, inp.split()))
    n = d[0]; row = d[1:1 + n]; col = d[1 + n:1 + 2 * n]
    # перебираем высоты/ширины: h0 — делитель A[0][0]
    a00 = row[0]
    for h0 in range(1, a00 + 1):
        if a00 % h0:
            continue
        w = [x // h0 for x in row]
        if any(x % h0 for x in row):
            continue
        if any(c % w[0] for c in col):
            continue
        h = [c // w[0] for c in col]
        return '\n'.join(' '.join(str(h[i] * w[j]) for j in range(n)) for i in range(n))


def animals(inp):
    L, H = map(int, inp.split())
    for c in range(0, L // 4 + 1):
        for hs in range(0, L // 4 + 1):
            if 4 * (c + hs) == L and 2 * c == H:
                return f'{c} {hs}'


def alchemy(inp):
    """Поиск в ширину по состояниям (массив, оставшиеся числа b)."""
    d = inp.split()
    n, m = int(d[0]), int(d[1])
    a = tuple(map(int, d[2:2 + n]))
    b = frozenset(map(int, d[2 + n:2 + n + m]))
    start = (a, b)
    dist = {start: 0}
    dq = deque([start])
    while dq:
        arr, rest = dq.popleft()
        if all(arr[i] < arr[i + 1] for i in range(len(arr) - 1)):
            return str(dist[(arr, rest)])
        for rem in {min(arr), max(arr)}:
            base = tuple(x for x in arr if x != rem)
            for x in rest:
                for pos in range(len(base) + 1):
                    nxt = (base[:pos] + (x,) + base[pos:], rest - {x})
                    if nxt not in dist:
                        dist[nxt] = dist[(arr, rest)] + 1
                        dq.append(nxt)
    return '-1'


def nauryz(inp):
    """НВП по всей последовательности из m копий (n·m элементов)."""
    from bisect import bisect_left
    d = list(map(int, inp.split()))
    n, m = d[:2]
    a = d[2:2 + n]
    tails = []
    for pos in range(n * m):
        k = bisect_left(tails, a[pos % n])
        if k == len(tails):
            tails.append(a[pos % n])
        else:
            tails[k] = a[pos % n]
    return f'{len(tails)}\n'


import sys


def _tree_shifts_main():
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


def tree_shifts(inp):
    """Перебор всех достижимых раскладок весов (BFS)."""
    import io as _io, sys as _sys, contextlib as _cl
    old = _sys.stdin
    _sys.stdin = _io.StringIO(inp)
    buf = _io.StringIO()
    try:
        with _cl.redirect_stdout(buf):
            _tree_shifts_main()
    finally:
        _sys.stdin = old
    return buf.getvalue()


BRUTE = {
    'tree-shifts': tree_shifts,
    'nauryz': nauryz,
    'alchemy': alchemy,
    'groups': groups, 'hanabi': hanabi, 'brackets': brackets, 'hurdles': hurdles,
    'target-mst': target_mst, 'contact': contact, 'akserek': akserek,
    'bitcount': bitcount, 'perm-sort': perm_sort, 'table-area': table_area,
    'animals': animals,
}
