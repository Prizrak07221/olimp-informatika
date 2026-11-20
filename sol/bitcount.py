import sys
import numpy as np


def popcounts(size):
    return np.array([bin(x).count('1') for x in range(size)], dtype=np.float64)


def solve_k1(a):
    """k = 1: динамика по битам s от младшего к старшему. Элементы с переносом в разряд j —
    «хвост» списка, отсортированного по a mod 2^j, поэтому состояние — размер хвоста z."""
    n = len(a)
    order = list(range(n))
    dp = {0: 0}
    for j in range(22):
        bits = [(a[i] >> j) & 1 for i in order]
        pre = [0]
        for b in bits:
            pre.append(pre[-1] + b)
        nd = {}
        for z, cost in dp.items():
            tau = n - z
            ones_carry = pre[n] - pre[tau]
            ones_free = pre[tau]
            for c, z2 in ((cost + (z - ones_carry) + ones_free, ones_carry),        # бит s = 0
                          (cost + ones_carry + (tau - ones_free), z + ones_free)):  # бит s = 1
                if nd.get(z2, 10**18) > c:
                    nd[z2] = c
        dp = nd
        order = [i for i in order if not (a[i] >> j) & 1] + [i for i in order if (a[i] >> j) & 1]
    return min(cost + z for z, cost in dp.items())


def main():
    data = sys.stdin.read().split()
    n, k = int(data[0]), int(data[1])
    if k == 1:
        print(solve_k1([int(x) for x in data[2:2 + n]]))
        return
    a = np.array(data[2:2 + n], dtype=np.int64)

    # Все a_i < 2^T, значит достаточно s < 2^(T+1): старшие биты s только добавляют единицы.
    T = max(1, int(a.max()).bit_length())
    LB = T // 2                      # младшая половина битов
    LO, HI = 1 << LB, 1 << (T - LB)  # размеры половин a
    SL, SH = 1 << LB, 1 << (T + 1 - LB)  # размеры половин s
    lo = a & (LO - 1)
    hi = a >> LB

    # F[hi][lo] — сколько чисел с такими половинами
    F = np.zeros((HI, LO), dtype=np.float64)
    np.add.at(F, (hi, lo), 1)

    # Младшая половина: lo + sl даёт L = popcount((lo+sl) mod LO) и перенос c.
    pcl = popcounts(2 * LO)
    s_ = np.arange(SL)
    l_ = np.arange(LO)
    tot = l_[:, None] + s_[None, :]          # LO x SL
    carry = tot >= LO
    Lval = pcl[tot % LO] if LO > 1 else np.zeros_like(tot, dtype=np.float64)

    # Старшая половина: H = popcount(hi + sh + c)
    pch = popcounts(HI + SH + 2)
    h_ = np.arange(HI)
    sh_ = np.arange(SH)
    base = h_[:, None] + sh_[None, :]        # HI x SH

    cost = np.zeros((SL, SH), dtype=np.float64)
    for c in (0, 1):
        mask = (carry == bool(c)).astype(np.float64)
        cnt = F @ mask                       # HI x SL: сколько чисел с этим hi и переносом c
        sL = F @ (mask * Lval)               # сумма L
        G1 = pch[base + c]                   # HI x SH: H
        sL2 = F @ (mask * Lval * Lval)       # сумма L^2
        G2 = G1 * G1
        # (L + H)^2 = L^2 + 2·L·H + H^2
        cost += sL2.sum(axis=0)[:, None] + 2 * (sL.T @ G1) + cnt.T @ G2
    print(int(round(cost.min())))


main()
