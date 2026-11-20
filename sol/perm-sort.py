import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    p = [int(x) - 1 for x in data[1:1 + n]]
    q = int(data[1 + n])
    pos = 2 + n

    # c[i] — сколько элементов «перешагивает» границу i|i+1 вправо (стоят на позиции <= i, значение > i).
    # Сортировка возможна, если c[i] <= 1 везде и неподвижные точки ни во что не попадают:
    # max(c[i] + [p[i] == i]) <= 1. Тогда ответ = сумма c[i].
    size = 1
    while size < n:
        size *= 2
    mx = [0] * (2 * size)    # максимум в поддереве с учётом своих прибавок
    add = [0] * (2 * size)   # прибавка ко всему отрезку вершины

    def update(l, r, d, node=1, nl=0, nr=size - 1):
        if r < nl or nr < l:
            return
        if l <= nl and nr <= r:
            mx[node] += d
            add[node] += d
            return
        mid = (nl + nr) // 2
        update(l, r, d, 2 * node, nl, mid)
        update(l, r, d, 2 * node + 1, mid + 1, nr)
        mx[node] = max(mx[2 * node], mx[2 * node + 1]) + add[node]

    total = 0  # сумма c[i]

    def contrib(x, sign):
        nonlocal total
        v = p[x]
        if v > x:
            update(x, v - 1, sign)
            total += sign * (v - x)
        elif v == x:
            update(x, x, sign)

    for x in range(n):
        contrib(x, 1)
    # фиктивные листья за пределами n не должны мешать: они равны 0 <= 1

    def answer():
        return total if mx[1] <= 1 else -1

    out = [answer()]
    for _ in range(q):
        x, y = int(data[pos]) - 1, int(data[pos + 1]) - 1
        pos += 2
        contrib(x, -1)
        contrib(y, -1)
        p[x], p[y] = p[y], p[x]
        contrib(x, 1)
        contrib(y, 1)
        out.append(answer())
    print('\n'.join(map(str, out)))


main()
