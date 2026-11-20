import contextlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cache = {}


def run_sol(pid, inp):
    """Запускает sol/<pid>.py в этом же процессе: stdin -> stdout."""
    code = _cache.get(pid)
    if code is None:
        path = os.path.join(ROOT, 'sol', pid + '.py')
        with open(path, encoding='utf-8') as f:
            code = compile(f.read(), path, 'exec')
        _cache[pid] = code
    old_in = sys.stdin
    sys.stdin = io.StringIO(inp)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {'__name__': '__main__'})
    finally:
        sys.stdin = old_in
    return buf.getvalue()


def mst_weight(n, edges, w):
    order = sorted(range(len(edges)), key=lambda i: w[i])
    par = list(range(n + 1))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    total = 0
    for i in order:
        a, b = find(edges[i][0]), find(edges[i][1])
        if a != b:
            par[a] = b
            total += w[i]
    return total


# ---------- проверяющие программы (checker) ----------
# Такой же код (CHECKERS_PY) отправляется в браузер и выполняется в Pyodide.

CHECKERS_PY = r'''
def _mst(n, edges, w):
    order = sorted(range(len(edges)), key=lambda i: w[i])
    par = list(range(n + 1))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    total = 0
    for i in order:
        a, b = find(edges[i][0]), find(edges[i][1])
        if a != b:
            par[a] = b
            total += w[i]
    return total

def check_target_mst(inp, out, exp):
    d = inp.split()
    n, m, W = int(d[0]), int(d[1]), int(d[2])
    edges, L, R = [], [], []
    for i in range(m):
        u, v, l, r = map(int, d[3 + 4*i: 7 + 4*i])
        edges.append((u, v)); L.append(l); R.append(r)
    o = out.split()
    e = exp.split()
    if not o:
        return False, 'Пустой вывод'
    if e[0] == 'impossible':
        return (o == ['impossible'], 'Ожидалось impossible' if o != ['impossible'] else 'OK')
    if o[0] != 'possible':
        return False, 'Ответ существует, а выведено ' + o[0]
    if len(o) != m + 1:
        return False, f'Нужно {m} весов, выведено {len(o) - 1}'
    try:
        c = [int(x) for x in o[1:]]
    except ValueError:
        return False, 'Веса должны быть целыми числами'
    for i in range(m):
        if not (L[i] <= c[i] <= R[i]):
            return False, f'Вес ребра {i+1} = {c[i]} вне отрезка [{L[i]}, {R[i]}]'
    got = _mst(n, edges, c)
    if got != W:
        return False, f'Вес MST получился {got}, а нужно {W}'
    return True, 'OK'

def check_nauryz(inp, out, exp):
    d = inp.split()
    n, m = int(d[0]), int(d[1])
    a = [int(x) for x in d[2:2 + n]]
    o = out.split()
    k_exp = int(exp.split()[0])
    if not o:
        return False, 'Пустой вывод'
    try:
        k = int(o[0])
        p = [int(x) for x in o[1:]]
    except ValueError:
        return False, 'Ожидались целые числа'
    if k != k_exp:
        return False, f'Длина {k}, а оптимум {k_exp}'
    if len(p) != k:
        return False, f'Указано {len(p)} номеров вместо {k}'
    for i in range(k):
        if not (1 <= p[i] <= n * m):
            return False, f'Номер {p[i]} вне [1, n*m]'
        if i and p[i] <= p[i-1]:
            return False, 'Номера должны строго возрастать'
        if i and a[(p[i]-1) % n] <= a[(p[i-1]-1) % n]:
            return False, 'Сложности должны строго возрастать'
    return True, 'OK'
'''

_ns = {}
exec(CHECKERS_PY, _ns)
CHECKERS = {'target-mst': _ns['check_target_mst'], 'nauryz': _ns['check_nauryz']}


def tokens_equal(a, b):
    return a.split() == b.split()


def verdict(pid, inp, out, exp):
    if pid in CHECKERS:
        return CHECKERS[pid](inp, out, exp)[0]
    if pid == 'hanabi':
        return out.upper().split() == exp.upper().split()
    return tokens_equal(out, exp)
