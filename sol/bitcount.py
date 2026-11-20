import sys


def solve_k1(a):
    """k = 1: динамика по битам s от младшего к старшему.
    Элементы, у которых есть перенос в текущий разряд, образуют «хвост»
    списка, отсортированного по остатку a mod 2^j, поэтому состояние — это
    просто размер хвоста z."""
    n = len(a)
    order = list(range(n))
    dp = {0: 0}
    for j in range(22):
        bits = [(a[i] >> j) & 1 for i in order]
        pre = [0]
        for b in bits:
            pre.append(pre[-1] + b)
        ones_total = pre[n]
        nd = {}
        for z, cost in dp.items():
            tau = n - z
            ones_carry = ones_total - pre[tau]
            ones_free = pre[tau]
            # s_j = 0
            c0 = cost + (z - ones_carry) + ones_free
            z0 = ones_carry
            if nd.get(z0, 10**18) > c0:
                nd[z0] = c0
            # s_j = 1
            c1 = cost + ones_carry + (tau - ones_free)
            z1 = z + ones_free
            if nd.get(z1, 10**18) > c1:
                nd[z1] = c1
        dp = nd
        order = [i for i in order if not (a[i] >> j) & 1] + \
                [i for i in order if (a[i] >> j) & 1]
    return min(cost + z for z, cost in dp.items())


def solve_brute(a, k):
    """Любое k, но только для небольших a_i: перебираем s < 2^(бит+1)."""
    cnt = {}
    for v in a:
        cnt[v] = cnt.get(v, 0) + 1
    bits = max(a).bit_length()
    best = None
    for s in range(1 << (bits + 1)):
        total = 0
        for v, c in cnt.items():
            total += c * bin(v + s).count('1') ** k
        if best is None or total < best:
            best = total
    return best


def main():
    data = sys.stdin.read().split()
    n, k = int(data[0]), int(data[1])
    a = list(map(int, data[2:2 + n]))
    if k == 1:
        print(solve_k1(a))
    else:
        print(solve_brute(a, k))  # подзадачи 1-2: a_i < 2^10


main()
