import sys
from collections import deque


def main():
    data = sys.stdin.read().split()
    n, m = int(data[0]), int(data[1])
    a = tuple(map(int, data[2:2 + n]))
    b = frozenset(map(int, data[2 + n:2 + n + m]))
    # Полный перебор состояний (массив, оставшиеся числа из b). Для n, m <= 5.
    start = (a, b)
    dist = {start: 0}
    dq = deque([start])
    while dq:
        arr, rest = dq.popleft()
        if all(arr[i] < arr[i + 1] for i in range(len(arr) - 1)):
            print(dist[(arr, rest)])
            return
        mn, mx = min(arr), max(arr)
        for rem in {mn, mx}:
            base = tuple(x for x in arr if x != rem)
            for x in rest:
                nrest = rest - {x}
                for pos in range(len(base) + 1):
                    nxt = (base[:pos] + (x,) + base[pos:], nrest)
                    if nxt not in dist:
                        dist[nxt] = dist[(arr, rest)] + 1
                        dq.append(nxt)
    print(-1)


main()
