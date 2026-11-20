import sys


def main():
    data = sys.stdin.read().split()
    p = 0
    n, q = int(data[p]), int(data[p + 1]); p += 2
    # ---- Link-Cut дерево (узлы 1..n) ----
    L = [0] * (n + 1)
    R = [0] * (n + 1)
    P = [0] * (n + 1)
    rev = [False] * (n + 1)
    val = [0] + [int(x) for x in data[p:p + n]]; p += n
    sm = val[:]

    def is_root(x):
        f = P[x]
        return f == 0 or (L[f] != x and R[f] != x)

    def push(x):
        if rev[x]:
            l, r = L[x], R[x]
            L[x], R[x] = r, l
            if l:
                rev[l] = not rev[l]
            if r:
                rev[r] = not rev[r]
            rev[x] = False

    def pull(x):
        sm[x] = sm[L[x]] + sm[R[x]] + val[x]

    def rotate(x):
        f = P[x]
        g = P[f]
        if not is_root(f):
            if L[g] == f:
                L[g] = x
            else:
                R[g] = x
        P[x] = g
        if L[f] == x:
            L[f] = R[x]
            if R[x]:
                P[R[x]] = f
            R[x] = f
        else:
            R[f] = L[x]
            if L[x]:
                P[L[x]] = f
            L[x] = f
        P[f] = x
        pull(f)
        pull(x)

    def splay(x):
        stack = [x]
        y = x
        while not is_root(y):
            y = P[y]
            stack.append(y)
        for y in reversed(stack):
            push(y)
        while not is_root(x):
            f = P[x]
            if not is_root(f):
                g = P[f]
                if (L[g] == f) == (L[f] == x):
                    rotate(f)
                else:
                    rotate(x)
            rotate(x)

    def access(x):
        last = 0
        y = x
        while y:
            splay(y)
            R[y] = last
            pull(y)
            last = y
            y = P[y]
        splay(x)

    def make_root(x):
        access(x)
        rev[x] = not rev[x]
        push(x)

    def link(x, y):
        make_root(x)
        P[x] = y

    def cut(x, y):
        make_root(x)
        access(y)
        # теперь x — левый ребёнок y
        L[y] = 0
        P[x] = 0
        pull(y)

    def path_sum(x, y):
        make_root(x)
        access(y)
        return sm[y]

    def set_val(x, v):
        access(x)
        val[x] = v
        pull(x)

    sm[0] = 0
    adj = [set() for _ in range(n + 1)]
    for _ in range(n - 1):
        u, v = int(data[p]), int(data[p + 1]); p += 2
        adj[u].add(v)
        adj[v].add(u)
        link(u, v)
    node_of = list(range(n + 1))   # номер вершины -> узел дерева
    name_of = list(range(n + 1))   # узел -> текущий номер (минимальный среди слитых)

    out = []
    for _ in range(q):
        if data[p] == '1':
            V = node_of[int(data[p + 1])]; p += 2
            nb = list(adj[V])
            if len(nb) <= 1:
                continue
            S = max(nb, key=lambda x: len(adj[x]))   # оставляем узел с самым большим списком
            total = val[S]
            new_name = min(name_of[x] for x in nb)
            for X in nb:
                if X == S:
                    continue
                for Y in list(adj[X]):
                    if Y == V:
                        continue
                    cut(X, Y)
                    link(S, Y)
                    adj[Y].discard(X)
                    adj[Y].add(S)
                    adj[S].add(Y)
                cut(X, V)
                adj[V].discard(X)
                adj[X] = set()
                total += val[X]
            set_val(S, total)
            name_of[S] = new_name
            node_of[new_name] = S
        else:
            v, u = node_of[int(data[p + 1])], node_of[int(data[p + 2])]; p += 3
            out.append(val[v] if v == u else path_sum(v, u))
    print('\n'.join(map(str, out)))


main()
