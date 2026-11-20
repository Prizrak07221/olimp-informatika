import sys

MOD = 998244353


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    words = data[1:1 + n]
    # биномиальные коэффициенты C(c, x) для c, x <= n
    C = [[0] * (n + 2) for _ in range(n + 2)]
    for i in range(n + 2):
        C[i][0] = 1
        for j in range(1, i + 1):
            C[i][j] = (C[i - 1][j - 1] + C[i - 1][j]) % MOD

    def lcp(a, b):
        k = 0
        m = min(len(a), len(b))
        while k < m and a[k] == b[k]:
            k += 1
        return k

    for si, s in enumerate(words):
        L = len(s)
        # cnt[l] — сколько других слов имеют общий префикс длины ровно l со словом s
        cnt = [0] * (L + 1)
        for j, w in enumerate(words):
            if j != si:
                cnt[lcp(s, w)] += 1
        # Слова, которые называют до отгадывания, нужно расставить так,
        # чтобы j-е слово совпадало с s хотя бы в j первых буквах.
        # Это возможно, если отсортированные по lcp значения l_(j) >= j.
        # dp[j] — число способов выбрать j слов (по группам lcp по возрастанию).
        dp = [0] * (L + 1)
        dp[0] = 1
        total = 0
        for l in range(1, L + 1):
            c = cnt[l]
            if c == 0:
                continue
            nd = dp[:]
            for j in range(0, l):
                if dp[j] == 0:
                    continue
                for x in range(1, min(c, l - j) + 1):
                    nd[j + x] = (nd[j + x] + dp[j] * C[c][x]) % MOD
            dp = nd
        # без самого s: ровно L-1 неверных слов; с s: не больше L-2 неверных
        res = 0
        if L - 1 >= 0:
            res += dp[L - 1] if L - 1 <= L else 0
        for c in range(0, L - 1):
            res += dp[c]
        print(res % MOD)


main()
