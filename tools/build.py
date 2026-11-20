"""Собирает data/content.js и data/tests.js.
1) проверяет все вопросы «что выведет код»;
2) генерирует тесты для проверки в браузере (ответы — из sol/, которые сверены с перебором);
3) проверяет примеры из условий.
Запуск: python tools/build.py"""
import contextlib
import io
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT, run_sol, verdict, CHECKERS_PY  # noqa: E402
from samples import SAMPLES  # noqa: E402
import gens as G  # noqa: E402
from content_problems import CONTESTS, TOPICS, P  # noqa: E402
from content_quiz import Q  # noqa: E402
from content_theory import THEORY  # noqa: E402

TOPICS_ALL = dict(TOPICS)
TOPICS_ALL['complexity'] = 'Оценка сложности'


def _distinct_tree(rng, N):
    """ПСП из N пар, у каждой вершины размеры детей попарно различны."""
    if N == 0:
        return ''
    rest = N - 1
    parts, k = [], 1
    while rest > 0:
        if k <= rest:
            parts.append(k); rest -= k; k += 1
        else:
            parts[-1] += rest; rest = 0
    rng.shuffle(parts)
    return '(' + ''.join(_distinct_tree(rng, p) for p in parts) + ')'


def _binary_tree(rng, N):
    if N == 0:
        return ''
    rest = N - 1
    if rest == 0:
        return '()'
    if rng.random() < 0.3:
        return '(' + _binary_tree(rng, rest) + ')'
    a = rng.randint(1, rest)
    b = rest - a
    return '(' + _binary_tree(rng, a) + (_binary_tree(rng, b) if b else '') + ')'


def _brackets_from(s):
    return f'{len(s) // 2}\n{s}\n'


def _two_kinds(rng, pieces, twice=False):
    if twice:
        arr = ['()'] * pieces + ['(())', '(())']
    else:
        arr = [rng.choice(['()', '(())']) for _ in range(pieces)]
    rng.shuffle(arr)
    return _brackets_from(''.join(arr))


def _contact_a(rng, n):
    lens = rng.sample(range(1, 3 * n), n)
    return f'{n}\n' + '\n'.join('a' * L for L in lens) + '\n'


# (номер подзадачи, генератор, количество)
PLANS = {
    'animals': [(1, lambda r: G.animals(r), 8), (1, lambda r: '0\n0\n', 1), (1, lambda r: '1000\n500\n', 1)],
    'table-area': [(1, lambda r: G.table_area(r, 2, 30000), 3), (2, lambda r: G.table_area(r, r.randint(2, 6), 1000, True), 2),
                   (3, lambda r: G.table_area(r, r.randint(3, 20), 30000), 3), (3, lambda r: G.table_area(r, 200, 30000), 1),
                   (3, lambda r: G.table_area(r, 1, 30000), 1)],
    'groups': [(1, lambda r: G.groups(r, r.randint(4, 40), 100, True), 3), (2, lambda r: G.groups(r, r.randint(50, 1500), 10**9), 3),
               (3, lambda r: G.groups(r, 20000, 10**9), 2)],
    'hurdles': [(1, lambda r: G.hurdles(r, r.randint(1, 50), 1000, 500, 10**6, eq=True), 3),
                (2, lambda r: G.hurdles(r, r.randint(1, 50), 10**6, 10**6, 10**6, same=True), 3),
                (3, lambda r: G.hurdles(r, r.randint(100, 1000), 1000, 500, 1000), 3),
                (4, lambda r: G.hurdles(r, 50000, 10**6, 10**5, 10**6), 2)],
    'target-mst': [(1, lambda r: G.target_mst(r, 3, 3, 9, zero_l=True), 3), (2, lambda r: G.target_mst(r, r.randint(3, 30), 50, 100, fixed=True), 3),
                   (3, lambda r: G.target_mst(r, r.randint(3, 50), 0, 100, tree=True), 3),
                   (4, lambda r: G.target_mst(r, r.randint(3, 50), 80, 100, zero_l=True), 3),
                   (5, lambda r: G.target_mst(r, 200, 400, 10**6), 2), (6, lambda r: G.target_mst(r, 1500, 3000, 10**9), 2)],
    'bitcount': [(1, lambda r: G.bitcount(r, r.randint(1, 300), None, 10), 4), (2, lambda r: G.bitcount(r, 2000, 2, 10), 1),
                 (3, lambda r: G.bitcount(r, 3000, 1, 20), 3), (4, lambda r: G.bitcount(r, 20000, 1, 20), 1)],
    'hanabi': [(1, lambda r: G.hanabi(r, r.randint(5, 100), only14=True), 3), (2, lambda r: G.hanabi(r, r.randint(5, 100)), 4),
               (3, lambda r: G.hanabi(r, 5000, queries_last=True), 3), (4, lambda r: G.hanabi(r, 50000), 2)],
    'brackets': [(0, lambda r: G.brackets(r, r.randint(1, 3)), 3), (1, lambda r: _two_kinds(r, r.randint(0, 50), True), 2),
                 (2, lambda r: _two_kinds(r, r.randint(10, 600)), 2), (3, lambda r: G.brackets(r, r.randint(5, 10)), 3),
                 (4, lambda r: G.brackets(r, 3000, depth2=True), 2), (5, lambda r: _brackets_from(_distinct_tree(r, r.randint(50, 3000))), 2),
                 (6, lambda r: G.brackets(r, r.randint(500, 2000)), 2), (7, lambda r: _brackets_from(_binary_tree(r, 3000)), 2),
                 (8, lambda r: G.brackets(r, 20000), 2)],
    'all-in-one': [(0, lambda r: G.all_in_one(r, r.randint(2, 50), r.randint(1, 50), r.randint(1, 50)), 3),
                   (1, lambda r: G.all_in_one(r, 300, 450, 300), 2)],
    'alchemy': [(1, lambda r: G.alchemy(r, r.randint(1, 10), 1, 40), 6)],
    'perm-sort': [(1, lambda r: G.perm_sort(r, 3, 0), 3), (2, lambda r: G.perm_sort(r, r.randint(2, 9), r.randint(0, 10)), 4),
                  (3, lambda r: G.perm_sort(r, 1000, 400, identity=True), 2), (4, lambda r: G.perm_sort(r, 500, 500), 2),
                  (5, lambda r: G.perm_sort(r, 2000, 1000), 2)],
    'tree-shifts': [(1, lambda r: G.tree_shifts(r, 3, r.randint(1, 8), 20), 4)],
    'akserek': [(0, lambda r: G.akserek(r, r.randint(2, 10), 1, 30), 3), (1, lambda r: G.akserek(r, r.randint(2, 5), r.randint(1, 5), 20), 3),
                (2, lambda r: G.akserek(r, r.randint(2, 8), r.randint(1, 8), 30), 3), (3, lambda r: G.akserek(r, 5000, 1, 10**9), 2),
                (4, lambda r: G.akserek(r, 1000, 1000, 10**6), 2), (5, lambda r: G.akserek(r, 2000, 2000, 10**9), 2)],
    'nauryz': [(1, lambda r: G.nauryz(r, r.randint(1, 2000), 1, 10**9), 3), (2, lambda r: G.nauryz(r, 20000, 1, 10**9), 1),
               (4, lambda r: G.nauryz(r, r.randint(5, 100), r.randint(1, 100), 0, inc=True), 2),
               (5, lambda r: G.nauryz(r, r.randint(50, 200), r.randint(1, 50), 100), 3)],
    'quantum': [(1, lambda r: G.quantum(r, r.randint(2, 60), 100, r.randint(1, 60), 60), 3),
                (2, lambda r: G.quantum(r, 300, 600, 300, 300), 2)],
    'tree-merge': [(2, lambda r: G.tree_merge(r, r.randint(2, 300), 300, no_ops=True), 2), (3, lambda r: G.tree_merge(r, r.randint(2, 300), 300), 3),
                   (4, lambda r: G.tree_merge(r, r.randint(2, 300), 300, same=True), 2)],
    'contact': [(0, lambda r: G.contact(r, 2, 2, 'abc'), 3), (1, lambda r: G.contact(r, r.randint(1, 10), 5, 'ab'), 3),
                (2, lambda r: _contact_a(r, r.randint(1, 150)), 2), (3, lambda r: G.contact(r, r.randint(10, 100), 10, 'ab'), 3),
                (4, lambda r: G.contact(r, 300, 20, 'ab'), 2)],
}

def gen_contact_sub0(rng):
    """Подзадача 1: n = 2, оба слова длины 2."""
    words = rng.sample([a + b for a in 'abc' for b in 'abc'], 2)
    return '2\n' + '\n'.join(words) + '\n'


PLANS['contact'][0] = (0, gen_contact_sub0, 3)


def check_quiz():
    bad = 0
    for i, q in enumerate(Q):
        if not q['run']:
            continue
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(q['code'], {})
        got = buf.getvalue().strip()
        want = q['o'][q['a']]
        if got != want:
            bad += 1
            print(f'ВОПРОС {i}: код печатает {got!r}, а верный вариант {want!r}')
        if q['o'].count(want) > 1 or got in [o for j, o in enumerate(q['o']) if j != q['a']]:
            bad += 1
            print(f'ВОПРОС {i}: вывод совпадает с неверным вариантом')
    print(f'Вопросов: {len(Q)}, с проверкой кода: {sum(q["run"] for q in Q)}, ошибок: {bad}')
    return bad


def build_tests():
    tests = {}
    rng = random.Random(2026)
    pmap = {p['id']: p for p in P}
    for pid, p in pmap.items():
        lst = []
        has_samples_sub = p['subtasks'] and p['subtasks'][0][1].startswith('Пример')
        for inp, exp in SAMPLES.get(pid, []):
            lst.append({'in': inp, 'out': exp, 'sub': 0 if has_samples_sub else -1, 'sample': True})
        if p['status'] == 'none':
            tests[pid] = lst
            continue
        for sub, gen, cnt in PLANS.get(pid, []):
            for _ in range(cnt):
                inp = gen(rng)
                out = run_sol(pid, inp)
                lst.append({'in': inp, 'out': out.strip(), 'sub': sub})
        # примеры: проверим, что наше решение их проходит
        for t in lst:
            if t.get('sample'):
                out = run_sol(pid, t['in'])
                if not verdict(pid, t['in'], out, t['out']):
                    raise SystemExit(f'{pid}: решение не прошло пример')
        tests[pid] = lst
        size = sum(len(t['in']) + len(t['out']) for t in lst)
        print(f'{pid:12s}: {len(lst):3d} тестов, {size / 1024:7.1f} КБ')
    return tests


def main():
    if check_quiz():
        raise SystemExit('Есть ошибки в вопросах')
    probs = []
    for p in P:
        p = dict(p)
        path = os.path.join(ROOT, 'sol', p['id'] + '.py')
        p['solution'] = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
        p['samples'] = [{'in': a, 'out': b} for a, b in SAMPLES.get(p['id'], [])]
        p['checker'] = {'target-mst': 'check_target_mst', 'nauryz': 'check_nauryz'}.get(p['id'])
        probs.append(p)
    tests = build_tests()
    for p in probs:
        lst = tests.get(p['id'], [])
        p['testCount'] = len(lst)
        p['testSubs'] = sorted({t['sub'] for t in lst if t['sub'] >= 0})
    content = {'contests': CONTESTS, 'topics': TOPICS_ALL, 'problems': probs, 'theory': THEORY, 'quiz': Q,
               'checkers': CHECKERS_PY}
    tdir = os.path.join(ROOT, 'data', 'tests')
    os.makedirs(tdir, exist_ok=True)
    with open(os.path.join(ROOT, 'data', 'content.js'), 'w', encoding='utf-8') as f:
        f.write('window.OLY = ' + json.dumps(content, ensure_ascii=False) + ';\n')
    for pid, lst in tests.items():
        with open(os.path.join(tdir, pid + '.json'), 'w', encoding='utf-8') as f:
            json.dump(lst, f, ensure_ascii=False, separators=(',', ':'))
    old = os.path.join(ROOT, 'data', 'tests.js')
    if os.path.exists(old):
        os.remove(old)
    print('Готово: data/content.js, data/tests/*.json')


if __name__ == '__main__':
    main()
