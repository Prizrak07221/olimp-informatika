"""Сверка решений с перебором на случайных маленьких тестах.
Запуск: python tools/stress.py [задача ...] [-n ЧИСЛО]"""
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import run_sol, verdict  # noqa: E402
from brute import BRUTE  # noqa: E402
import gens  # noqa: E402

SMALL = {
    'animals': lambda r: gens.animals(r),
    'table-area': lambda r: gens.table_area(r, n=r.randint(1, 4), maxv=12),
    'groups': lambda r: gens.groups(r, n=r.randint(2, 8), maxr=15),
    'hanabi': lambda r: gens.hanabi(r, q=r.randint(2, 25)),
    'brackets': lambda r: gens.brackets(r, n=r.randint(1, 7)),
    'hurdles': lambda r: gens.hurdles(r, n=r.randint(1, 6)),
    'target-mst': lambda r: gens.target_mst(r, n=r.randint(2, 4), m=r.randint(1, 5), maxw=3),
    'contact': lambda r: gens.contact(r, n=r.randint(1, 5), maxlen=4, alpha=r.choice(['ab', 'abc', 'a'])),
    'akserek': lambda r: gens.akserek(r, n=r.randint(2, 4), m=r.randint(1, 4), maxv=r.randint(3, 12)),
    'bitcount': lambda r: gens.bitcount(r, n=r.randint(1, 6), bits=r.randint(1, 6)),
    'perm-sort': lambda r: gens.perm_sort(r, n=r.randint(2, 6), q=r.randint(0, 3)),
    'nauryz': lambda r: gens.nauryz(r, n=r.randint(1, 9), m=r.randint(1, 10), maxv=r.randint(1, 12)),
    'tree-shifts': lambda r: gens.tree_shifts(r, T=1, n=r.randint(1, 8), maxw=r.choice([3, 50]), star=r.random() < 0.1),
    'alchemy': lambda r: gens.alchemy(r, n=r.randint(1, 5), m=r.randint(1, 5), maxv=r.choice([12, 30])),
}


def main():
    args = sys.argv[1:]
    iters = 300
    if '-n' in args:
        i = args.index('-n'); iters = int(args[i + 1]); args = args[:i] + args[i + 2:]
    pids = args or list(SMALL)
    rng = random.Random(12345)
    for pid in pids:
        if pid == 'contact' and 'contact' not in args:
            pass
        fails = 0
        for it in range(iters):
            inp = SMALL[pid](rng)
            if pid == 'contact' and len(inp.split()) > 7:
                continue
            exp = BRUTE[pid](inp)
            out = run_sol(pid, inp)
            if pid == 'target-mst':
                ok = verdict(pid, inp, out, exp)
            else:
                ok = verdict(pid, inp, out, exp)
            if not ok:
                fails += 1
                if fails <= 2:
                    print(f'--- {pid} FAIL\n{inp}got: {out.strip()}\nexp: {exp.strip()}')
        print(f'{pid:12s}: {iters} тестов, ошибок {fails}')


if __name__ == '__main__':
    main()
