import sys
from bisect import bisect_right, insort


def best_grip(c):
    """Лучшая возможная минимальная сила хвата при расстановке цепи.
    c — отсортированный список. Оптимальна «змейка»:
    самый слабый, самый сильный, второй слабый, второй сильный, ..."""
    lo, hi = 0, len(c) - 1
    prev = None
    res = None
    take_low = True
    while lo <= hi:
        if take_low:
            cur = c[lo]
            lo += 1
        else:
            cur = c[hi]
            hi -= 1
        take_low = not take_low
        if prev is not None:
            s = prev + cur
            if res is None or s < res:
                res = s
        prev = cur
    return res


def main():
    data = sys.stdin.read().split()
    n, m = int(data[0]), int(data[1])
    defenders = sorted(map(int, data[2:2 + n]))
    attackers = sorted(map(int, data[2 + n:2 + n + m]))
    caught = 0
    while attackers:
        f = best_grip(defenders)
        i = bisect_right(attackers, f) - 1  # самый сильный из тех, кого можно поймать
        if i < 0:
            break
        x = attackers.pop(i)
        insort(defenders, x)
        caught += 1
    print(caught)


main()
