import sys

MOD = 10**9 + 7


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    s = data[1]
    N = n + 5
    fact = [1] * N
    for i in range(1, N):
        fact[i] = fact[i - 1] * i % MOD
    inv = [pow(f, MOD - 2, MOD) for f in fact]

    canon = {}   # отсортированный кортеж классов детей -> номер класса
    ways = []    # ways[класс] = сколько различных строк даёт поддерево

    def finish(children):
        children.sort()
        key = tuple(children)
        cid = canon.get(key)
        if cid is None:
            cid = len(ways)
            canon[key] = cid
            # k! / (m1! m2! ...) * произведение ways[дети]
            w = fact[len(children)]
            i = 0
            while i < len(children):
                j = i
                while j < len(children) and children[j] == children[i]:
                    j += 1
                w = w * inv[j - i] % MOD
                i = j
            for c in children:
                w = w * ways[c] % MOD
            ways.append(w)
        return cid

    stack = [[]]
    for ch in s:
        if ch == '(':
            stack.append([])
        else:
            kids = stack.pop()
            stack[-1].append(finish(kids))
    root = stack[0]
    # корень — «виртуальный» узел: те же правила
    root.sort()
    res = fact[len(root)]
    i = 0
    while i < len(root):
        j = i
        while j < len(root) and root[j] == root[i]:
            j += 1
        res = res * inv[j - i] % MOD
        i = j
    for c in root:
        res = res * ways[c] % MOD
    print(res)


main()
