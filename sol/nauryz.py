import sys


def main():
    data = sys.stdin.read().split()
    n, m = int(data[0]), int(data[1])
    a = list(map(int, data[2:2 + n]))
    order = sorted(range(n), key=lambda i: a[i])   # элементы по возрастанию сложности
    groups = []                                     # группы равных значений
    for i in order:
        if groups and a[groups[-1][0]] == a[i]:
            groups[-1].append(i)
        else:
            groups.append([i])
    NEG = (-10**18, 0, 0)

    def better(x, y):
        """Состояние (очки, мин. дней, макс. дней): больше очков, при равенстве — объединяем диапазон дней."""
        if x[0] != y[0]:
            return x if x[0] > y[0] else y
        return (x[0], min(x[1], y[1]), max(x[2], y[2]))

    def run(lam):
        """Очки цепочки = длина − lam·(число дней). Для каждого элемента — лучшее состояние,
        если цепочка на нём заканчивается."""
        tree = [NEG] * (n + 1)          # Фенвик по позициям: максимум на префиксе
        glob = NEG                       # максимум по всем меньшим значениям
        best = [None] * n
        for g in groups:
            res = []
            for i in g:
                # тот же день: предыдущий элемент стоит левее
                cur = NEG
                j = i
                while j > 0:
                    cur = better(cur, tree[j])
                    j -= j & -j
                st = (cur[0] + 1, cur[1], cur[2]) if cur is not NEG and cur[0] > NEG[0] else NEG
                # новый день: предыдущий элемент где угодно
                if glob[0] > NEG[0]:
                    st = better(st, (glob[0] + 1 - lam, glob[1] + 1, glob[2] + 1))
                # начало цепочки
                st = better(st, (1 - lam, 1, 1))
                res.append(st)
            for i, st in zip(g, res):
                best[i] = st
                j = i + 1
                while j <= n:
                    tree[j] = better(tree[j], st)
                    j += j & -j
                glob = better(glob, st)
        return best, glob

    # наименьший штраф lam, при котором оптимальной цепочке хватает m дней
    lo, hi = 0, n + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if run(mid)[1][1] <= m:
            hi = mid
        else:
            lo = mid + 1
    lam = lo
    best, glob = run(lam)
    need = min(m, glob[2])               # столько дней займёт ответ
    length = glob[0] + lam * need

    # восстановление: идём от конца по убыванию значений
    end = next(i for i in range(n) if best[i][0] == glob[0] and best[i][1] <= need <= best[i][2])
    chain = [(end, need)]
    x, c = end, need
    rev = order[::-1]
    k = 0
    while True:
        # можно ли начать цепочку прямо с x?
        if c == 1 and best[x][0] == 1 - lam:
            break
        found = False
        while k < n:
            y = rev[k]
            k += 1
            if a[y] >= a[x]:
                continue
            s, l1, h1 = best[y]
            if y < x and s + 1 == best[x][0] and l1 <= c <= h1:
                x = y
                found = True
                break
            if s + 1 - lam == best[x][0] and l1 <= c - 1 <= h1:
                x, c = y, c - 1
                found = True
                break
        if not found:
            raise RuntimeError('восстановление не удалось')
        chain.append((x, c))
    chain.reverse()
    assert len(chain) == length
    print(length)
    print(*[(day - 1) * n + i + 1 for i, day in chain])


main()
