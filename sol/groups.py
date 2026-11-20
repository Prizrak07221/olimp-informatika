import sys


def main():
    data = sys.stdin.read().split()
    n, A, B = int(data[0]), int(data[1]), int(data[2])
    r = sorted(map(int, data[3:3 + n]))

    def ok(D):
        # dp[i] — можно ли разбить первые i учеников; pref[i] = dp[0]+...+dp[i]
        dp = [False] * (n + 1)
        pref = [0] * (n + 2)  # pref[i+1] = sum dp[0..i]
        dp[0] = True
        pref[1] = 1
        lo = 0
        for i in range(1, n + 1):
            # последняя группа — это r[j..i-1], нужно r[i-1] - r[j] <= D
            while r[i - 1] - r[lo] > D:
                lo += 1
            left = max(lo, i - B)
            right = i - A
            if right >= left and pref[right + 1] - pref[left] > 0:
                dp[i] = True
            pref[i + 1] = pref[i] + (1 if dp[i] else 0)
        return dp[n]

    lo, hi = 0, r[-1] - r[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    print(lo)


main()
