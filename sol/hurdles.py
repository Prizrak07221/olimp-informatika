import sys


def main():
    data = sys.stdin.read().split()
    n, h, x, y = int(data[0]), int(data[1]), int(data[2]), int(data[3])
    a = list(map(int, data[4:4 + n]))
    top = max(max(a), h)
    # Постоянные покупки выгодно делать в самом начале: выбираем итоговую H >= h,
    # платим (H-h)*x, а каждую преграду выше H перепрыгиваем временными усилениями.
    cnt = [0] * (top + 2)
    for v in a:
        cnt[v] += 1
    # over_cnt = сколько преград > H, over_sum = сумма их высот
    over_cnt = sum(1 for v in a if v > h)
    over_sum = sum(v for v in a if v > h)
    best = None
    for H in range(h, top + 1):
        if H > h:
            # преграды высоты H перестают быть «выше H»
            c = cnt[H]
            over_cnt -= c
            over_sum -= c * H
        cost = (H - h) * x + y * (over_sum - H * over_cnt)
        if best is None or cost < best:
            best = cost
    print(best)


main()
