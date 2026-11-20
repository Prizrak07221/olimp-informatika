import sys
from bisect import bisect_left


def main():
    d = sys.stdin.read().split()
    n, m = int(d[0]), int(d[1])
    a = list(map(int, d[2:2 + n]))
    B = sorted(map(int, d[2 + n:2 + n + m]))
    A = sorted(a)
    pos = {v: i for i, v in enumerate(a)}
    INF = float('inf')

    def ops(l, r):
        """Оставляем исходные элементы с рангами l..r (r = l-1 — не оставляем ничего).
        Возвращает число операций или INF."""
        p, q = l - 1, n - r          # сколько удалить снизу и сверху
        t = p + q
        if t == 0:
            return 0
        low_top = A[l - 2] if p else -INF   # последний удаляемый снизу
        high_bot = A[r] if q else INF       # последний удаляемый сверху
        # «свободные» b ничему не мешают: они между удаляемыми снизу и сверху
        # (все числа различны, поэтому bisect_left даёт «строго меньше»)
        free = bisect_left(B, high_bot) - bisect_left(B, low_top)
        # «поздние» b загораживают ещё не удалённые элементы — их можно вставлять только в конце
        late_low = bisect_left(B, low_top)
        late_high = len(B) - bisect_left(B, high_bot)
        cap1 = min(late_low + min(late_high, 1), q + 1)  # сначала удаляем все нижние
        cap2 = min(late_high + min(late_low, 1), p + 1)  # сначала все верхние
        return t if free + max(cap1, cap2) >= t else INF

    best = INF
    for j in range(n + 1):           # ничего не оставляем: разрез между рангами j и j+1
        best = min(best, ops(j + 1, j))
    i = 0
    while i < n:                     # максимальные серии рангов, стоящие в a по возрастанию
        j = i
        while j + 1 < n and pos[A[j + 1]] > pos[A[j]]:
            j += 1
        best = min(best, ops(i + 1, j + 1))
        i = j + 1
    print(-1 if best == INF else best)


main()
