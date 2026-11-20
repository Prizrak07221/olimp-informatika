n = int(input())
row = list(map(int, input().split()))
col = list(map(int, input().split()))
# A[i][j] = h_i * w_j, A[0][j] = h_0 * w_j, A[i][0] = h_i * w_0
# => A[i][j] = A[i][0] * A[0][j] / A[0][0]
for i in range(n):
    print(*[col[i] * row[j] // row[0] for j in range(n)])
