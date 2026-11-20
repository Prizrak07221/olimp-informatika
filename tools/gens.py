"""Генераторы входных данных. Каждая функция: (rng, **параметры) -> строка входа."""


def animals(rng, maxc=100):
    c, h = rng.randint(0, maxc), rng.randint(0, maxc)
    while 4 * (c + h) > 1000 or 2 * c > 500:
        c, h = rng.randint(0, maxc), rng.randint(0, maxc)
    return f'{4 * (c + h)}\n{2 * c}\n'


def table_area(rng, n=3, maxv=30, equal=False):
    if equal:
        v = rng.randint(1, maxv)
        h = [1] * n; w = [v] * n
    else:
        h = [rng.randint(1, maxv) for _ in range(n)]
        w = [rng.randint(1, maxv) for _ in range(n)]
    row = [h[0] * x for x in w]
    col = [x * w[0] for x in h]
    return f'{n}\n{" ".join(map(str, row))}\n{" ".join(map(str, col))}\n'


def groups(rng, n=6, maxr=20, eq=False):
    while True:
        A = rng.randint(2, max(2, n))
        B = A if eq else rng.randint(A, max(A, n))
        if any(A * k <= n <= B * k for k in range(1, n + 1)):
            break
    r = [rng.randint(1, maxr) for _ in range(n)]
    return f'{n} {A} {B}\n{" ".join(map(str, r))}\n'


def hanabi(rng, q=12, only14=False, queries_last=False):
    ops = []
    cnt = 0
    body = []
    for i in range(q - 1):
        t = rng.choice([1, 1, 2, 3, 4]) if not only14 else rng.choice([1, 4])
        if queries_last:
            t = rng.choice([1, 2, 3])
        if cnt == 0:
            t = 1
        if t == 1:
            body.append(f'1 {rng.choice("ABCDE")}{rng.randint(1, 5)}'); cnt += 1
        elif t == 2:
            body.append(f'2 {rng.randint(1, 5)}')
        elif t == 3:
            body.append(f'3 {rng.choice("ABCDE")}')
        else:
            body.append(f'4 {rng.randint(1, cnt)}')
    if cnt == 0:
        body.append('1 A1'); cnt = 1
    tail = []
    if queries_last:
        while len(body) + len(tail) < q + 5:
            tail.append(f'4 {rng.randint(1, cnt)}')
    else:
        tail.append(f'4 {rng.randint(1, cnt)}')
    ops = body + tail
    return f'{len(ops)}\n' + '\n'.join(ops) + '\n'


def _rand_tree_str(rng, nodes, lib=None):
    """Случайная ПСП из nodes пар скобок; иногда повторяем одинаковые куски."""
    if nodes == 0:
        return ''
    if lib and rng.random() < 0.5:
        piece = rng.choice(lib)
        if len(piece) // 2 <= nodes:
            return piece + _rand_tree_str(rng, nodes - len(piece) // 2, lib)
    inner = rng.randint(0, nodes - 1)
    return '(' + _rand_tree_str(rng, inner, lib) + ')' + _rand_tree_str(rng, nodes - 1 - inner, lib)


def brackets(rng, n=6, depth2=False):
    lib = ['()', '(())', '()()', '(()())', '((()))']
    if depth2:
        s = ''.join(rng.choice(['()', '(())', '(()())', '(()()())']) for _ in range(n))
        s = s[:]
        # обрежем до ровно нужной длины не нужно: n — число кусков
    else:
        s = _rand_tree_str(rng, n, lib)
    return f'{len(s) // 2}\n{s}\n'


def hurdles(rng, n=6, maxa=12, maxh=8, maxx=6, eq=False, same=False):
    x = rng.randint(1, maxx)
    y = x if eq else rng.randint(1, x)
    h = rng.randint(0, maxh)
    if same:
        v = rng.randint(1, maxa); a = [v] * n
    else:
        a = [rng.randint(1, maxa) for _ in range(n)]
    return f'{n} {h} {x} {y}\n{" ".join(map(str, a))}\n'


def target_mst(rng, n=4, m=5, maxw=5, fixed=False, zero_l=False, tree=False):
    from common import mst_weight
    if tree:
        m = n - 1
    edges = [(i, rng.randint(1, i - 1)) for i in range(2, n + 1)]
    have = {tuple(sorted(e)) for e in edges}
    while len(edges) < m:
        u, v = rng.randint(1, n), rng.randint(1, n)
        if u != v and tuple(sorted((u, v))) not in have:
            have.add(tuple(sorted((u, v)))); edges.append((u, v))
        if len(have) == n * (n - 1) // 2:
            break
    m = len(edges)
    rng.shuffle(edges)
    L, R = [], []
    for _ in range(m):
        l = 0 if zero_l else rng.randint(0, maxw)
        r = l if fixed else rng.randint(l, l + maxw)
        L.append(l); R.append(r)
    lo, hi = mst_weight(n, edges, L), mst_weight(n, edges, R)
    W = rng.randint(max(0, lo - 1), hi + 1)
    lines = [f'{n} {m} {W}'] + [f'{u} {v} {L[i]} {R[i]}' for i, (u, v) in enumerate(edges)]
    return '\n'.join(lines) + '\n'


def contact(rng, n=5, maxlen=4, alpha='ab'):
    possible = sum(len(alpha) ** L for L in range(1, maxlen + 1))
    n = min(n, possible)  # иначе разных слов не хватит
    words = set()
    while len(words) < n:
        words.add(''.join(rng.choice(alpha) for _ in range(rng.randint(1, maxlen))))
    words = list(words)
    rng.shuffle(words)
    return f'{n}\n' + '\n'.join(words) + '\n'


def akserek(rng, n=4, m=3, maxv=15):
    a = [rng.randint(1, maxv) for _ in range(n)]
    b = [rng.randint(1, 2 * maxv) for _ in range(m)]
    return f'{n} {m}\n{" ".join(map(str, a))}\n{" ".join(map(str, b))}\n'


def bitcount(rng, n=5, k=None, bits=6):
    k = k or rng.randint(1, 2)
    a = [rng.randint(0, (1 << bits) - 1) for _ in range(n)]
    return f'{n} {k}\n{" ".join(map(str, a))}\n'


def _valid_block_perm(rng, n):
    p = list(range(1, n + 1))
    i = 0
    while i < n:
        size = rng.randint(1, min(4, n - i))
        ops = list(range(i, i + size - 1))
        rng.shuffle(ops)
        for o in ops:
            p[o], p[o + 1] = p[o + 1], p[o]
        i += size
    return p


def perm_sort(rng, n=5, q=4, identity=False):
    if identity:
        p = list(range(1, n + 1))
    elif rng.random() < 0.7:
        p = _valid_block_perm(rng, n)
    else:
        p = list(range(1, n + 1)); rng.shuffle(p)
    qs = []
    used = set()
    for _ in range(q):
        while True:
            x, y = rng.sample(range(1, n + 1), 2)
            if not identity or (x not in used and y not in used):
                break
            if len(used) >= n - 1:
                x, y = rng.sample(range(1, n + 1), 2); break
        used |= {x, y}
        qs.append(f'{x} {y}')
    return f'{n}\n{" ".join(map(str, p))}\n{q}\n' + ''.join(s + '\n' for s in qs)


# ---------- частично решённые задачи (тесты только для малых подзадач) ----------

def alchemy(rng, n=4, m=1, maxv=20, nearly=False):
    vals = rng.sample(range(1, max(maxv, n + m) + 1), n + m)
    a, b = vals[:n], vals[n:]
    if nearly:  # почти отсортированный массив: длинные возрастающие серии интереснее
        a.sort()
        for _ in range(rng.randint(1, 4)):
            i, j = rng.randrange(n), rng.randrange(n)
            a[i], a[j] = a[j], a[i]
    return f'{n} {m}\n{" ".join(map(str, a))}\n{" ".join(map(str, b))}\n'


def tree_shifts(rng, T=2, n=6, maxw=9, star=False, path=False, single=False):
    parts = [str(T)]
    for _ in range(T):
        if star:
            par = [None, None] + [1] * (n - 1)
        elif path:
            par = [None, None] + [i - 1 for i in range(2, n + 1)]
        else:
            par = [None, None] + [rng.randint(1, i - 1) for i in range(2, n + 1)]
        g = [[] for _ in range(n + 1)]
        for v in range(2, n + 1):
            g[v].append(par[v]); g[par[v]].append(v)
        for v in range(1, n + 1):
            rng.shuffle(g[v])
        parts.append(str(n))
        parts.append(' '.join(str(rng.randint(0, maxw)) for _ in range(n)))
        for v in range(1, n + 1):
            parts.append(' '.join([str(len(g[v]))] + list(map(str, g[v]))))
        L = rng.randint(1, n); R = L if single else rng.randint(L, n)
        parts.append(f'{L} {R}')
    return '\n'.join(parts) + '\n'


def nauryz(rng, n=6, m=3, maxv=8, inc=False):
    if inc:
        a = sorted(rng.sample(range(1, 10 * n + 1), n))
    else:
        a = [rng.randint(1, maxv) for _ in range(n)]
    return f'{n} {m}\n{" ".join(map(str, a))}\n'


def quantum(rng, n=6, m=8, k=8, q=5, one_out=False, unique=False, r_is_k=False):
    edges = set()
    if one_out:
        for v in range(2, n + 1):
            edges.add((v, rng.randint(1, v - 1)))
    else:
        for v in range(2, n + 1):
            edges.add((v, rng.randint(1, v - 1)))
        tries = 0
        while len(edges) < m and tries < 1000:
            tries += 1
            u, v = rng.randint(2, n), rng.randint(1, n)
            if v < u:
                edges.add((u, v))
    edges = list(edges)
    rng.shuffle(edges)
    if unique:
        k = min(k, n - 1)
        a = rng.sample(range(2, n + 1), k)
    else:
        a = [rng.randint(2, n) for _ in range(k)]
    qs = []
    for _ in range(q):
        l = rng.randint(1, k); r = k if r_is_k else rng.randint(l, k)
        qs.append(f'{l} {r}')
    lines = [f'{n} {len(edges)}'] + [f'{u} {v}' for u, v in edges] + [f'{k} {q}', ' '.join(map(str, a))] + qs
    return '\n'.join(lines) + '\n'


def tree_merge(rng, n=8, q=8, star=False, no_ops=False, same=False, path=False):
    if star:
        edges = [(1, v) for v in range(2, n + 1)]
    elif path:
        edges = [(v - 1, v) for v in range(2, n + 1)]
    else:
        edges = [(v, rng.randint(1, v - 1)) for v in range(2, n + 1)]
    alive = set(range(1, n + 1))
    adj = {v: set() for v in alive}
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)
    vals = [rng.randint(-9, 9) for _ in range(n)]
    qs = []
    for _ in range(q):
        if not no_ops and rng.random() < 0.35:
            v = rng.choice(sorted(alive))
            qs.append(f'1 {v}')
            nb = sorted(adj[v])
            if len(nb) > 1:
                keep = nb[0]
                for u in nb[1:]:
                    for w in adj[u]:
                        if w != v:
                            adj[w].discard(u); adj[w].add(keep); adj[keep].add(w)
                    adj[v].discard(u); alive.discard(u); del adj[u]
        else:
            v = rng.choice(sorted(alive))
            u = v if same else rng.choice(sorted(alive))
            qs.append(f'2 {v} {u}')
    lines = [f'{n} {q}', ' '.join(map(str, vals))] + [f'{u} {v}' for u, v in edges] + qs
    return '\n'.join(lines) + '\n'


def all_in_one(rng, n=6, m=7, q=5, single=False):
    edges = set()
    for v in range(2, n + 1):
        edges.add((rng.randint(1, v - 1), v))
    tries = 0
    while len(edges) < m and tries < 500:
        tries += 1
        u, v = sorted(rng.sample(range(1, n + 1), 2))
        edges.add((u, v))
    ws = rng.sample(range(1, 10 * len(edges) + 1), len(edges))
    lines = [f'{n} {len(edges)}'] + [f'{u} {v} {w}' for (u, v), w in zip(edges, ws)] + [str(q)]
    for _ in range(q):
        k = 1 if single else rng.randint(1, min(3, n))
        lines.append(' '.join(map(str, [k] + rng.sample(range(1, n + 1), k))))
    return '\n'.join(lines) + '\n'


GENS = {
    'animals': animals, 'table-area': table_area, 'groups': groups, 'hanabi': hanabi,
    'brackets': brackets, 'hurdles': hurdles, 'target-mst': target_mst, 'contact': contact,
    'akserek': akserek, 'bitcount': bitcount, 'perm-sort': perm_sort,
    'alchemy': alchemy, 'tree-shifts': tree_shifts, 'nauryz': nauryz, 'quantum': quantum,
    'tree-merge': tree_merge, 'all-in-one': all_in_one,
}
