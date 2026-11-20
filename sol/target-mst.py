import sys


def main():
    data = sys.stdin.read().split()
    n, m, W = int(data[0]), int(data[1]), int(data[2])
    U = [0] * m
    V = [0] * m
    L = [0] * m
    R = [0] * m
    for i in range(m):
        U[i] = int(data[3 + 4 * i]) - 1
        V[i] = int(data[4 + 4 * i]) - 1
        L[i] = int(data[5 + 4 * i])
        R[i] = int(data[6 + 4 * i])

    def mst(w):
        order = sorted(range(m), key=w.__getitem__)
        par = list(range(n))

        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a
        total = 0
        used = 0
        for i in order:
            a, b = find(U[i]), find(V[i])
            if a != b:
                par[a] = b
                total += w[i]
                used += 1
                if used == n - 1:
                    break
        return total

    wmin = mst(L)
    wmax = mst(R)
    if not (wmin <= W <= wmax):
        print('impossible')
        return

    # Вес MST как функция веса одного ребра растёт со скоростью 0 или 1,
    # поэтому принимает все целые значения между концами.
    def with_prefix(t):
        return [R[i] if i < t else L[i] for i in range(m)]

    lo, hi = 0, m  # наименьшее t, при котором MST >= W
    while lo < hi:
        mid = (lo + hi) // 2
        if mst(with_prefix(mid)) >= W:
            hi = mid
        else:
            lo = mid + 1
    t = lo
    c = with_prefix(t)
    if t > 0:
        e = t - 1
        c[e] = L[e]
        lo, hi = L[e], R[e]
        while lo < hi:
            mid = (lo + hi) // 2
            c[e] = mid
            if mst(c) >= W:
                hi = mid
            else:
                lo = mid + 1
        c[e] = lo
    print('possible')
    print('\n'.join(map(str, c)))


main()
