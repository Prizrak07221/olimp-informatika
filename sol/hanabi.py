import sys


def main():
    data = sys.stdin.read().split()
    q = int(data[0])
    p = 1
    # Подсказка прикрепляется к картам, лежавшим в руке в момент подсказки.
    # Карта, добавленная в момент t, «слышала» подсказку про v, если
    # последняя подсказка про v была позже t.
    last_val = [-1] * 6
    last_col = [-1] * 5
    cards = []  # (цвет, значение, время добавления)
    out = []
    for t in range(q):
        typ = data[p]
        if typ == '1':
            cv = data[p + 1]
            cards.append((ord(cv[0]) - 65, int(cv[1]), t))
            p += 2
        elif typ == '2':
            last_val[int(data[p + 1])] = t
            p += 2
        elif typ == '3':
            last_col[ord(data[p + 1]) - 65] = t
            p += 2
        else:
            k = int(data[p + 1])
            p += 2
            c, v, t0 = cards[len(cards) - k]
            heard_v = [last_val[x] > t0 for x in range(1, 6)]
            heard_c = [last_col[x] > t0 for x in range(5)]
            # значение известно, если про него говорили «да»,
            # либо про остальные 4 значения сказали «нет»
            v_known = heard_v[v - 1] or sum(heard_v) == 4
            c_known = heard_c[c] or sum(heard_c) == 4
            out.append('YES' if v_known and c_known else 'NO')
    print('\n'.join(out))


main()
