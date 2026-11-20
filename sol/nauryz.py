import sys
from bisect import bisect_left


def main():
    data = sys.stdin.read().split()
    n, m = int(data[0]), int(data[1])
    a = list(map(int, data[2:2 + n]))
    # Классическая LIS (строго возрастающая) за O(log) на элемент
    # по всей последовательности из m копий. Подходит, пока n*m небольшое.
    total = n * m
    tails = []       # tails[k] — наименьший хвост возрастающей подпоследовательности длины k+1
    tails_pos = []   # позиция этого хвоста
    parent = [-1] * total
    for pos in range(total):
        v = a[pos % n]
        k = bisect_left(tails, v)
        if k == len(tails):
            tails.append(v)
            tails_pos.append(pos)
        else:
            tails[k] = v
            tails_pos[k] = pos
        parent[pos] = tails_pos[k - 1] if k > 0 else -1
    res = []
    cur = tails_pos[-1]
    while cur != -1:
        res.append(cur + 1)
        cur = parent[cur]
    res.reverse()
    print(len(res))
    print(*res)


main()
