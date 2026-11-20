import sys


def answer(p):
    """Каждую операцию можно использовать один раз, поэтому перестановка
    распадается на циклы, каждый из которых занимает отрезок позиций
    [l..r] и «унимодален»: от l значения растут до r, затем убывают.
    Тогда нужно (r - l) операций на цикл, всего n - (число циклов)."""
    n = len(p)
    seen = [False] * n
    cycles = 0
    for i in range(n):
        if seen[i]:
            continue
        seq = []
        x = i
        while not seen[x]:
            seen[x] = True
            seq.append(x)
            x = p[x]
        mx = max(seq)
        if len(seq) != mx - i + 1:      # цикл должен занимать отрезок
            return -1
        t = 0
        while t + 1 < len(seq) and seq[t + 1] > seq[t]:
            t += 1                       # растём до максимума
        for u in range(t, len(seq) - 1):
            if seq[u + 1] > seq[u]:      # дальше только убывание
                return -1
        cycles += 1
    return n - cycles


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    p = [int(x) - 1 for x in data[1:1 + n]]
    q = int(data[1 + n])
    pos = 2 + n
    out = [answer(p)]
    for _ in range(q):
        x, y = int(data[pos]) - 1, int(data[pos + 1]) - 1
        pos += 2
        p[x], p[y] = p[y], p[x]
        out.append(answer(p))
    print('\n'.join(map(str, out)))  # O(n) на запрос — подзадачи с n, q <= 10^4


main()
