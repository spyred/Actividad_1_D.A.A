"""Versión C: LCS por programación dinámica tabular (bottom-up).

Rellena la tabla L[0..m][0..n] por filas (Tema 3, Entrenamiento 3) y
reconstruye la subsecuencia recorriendo la matriz desde (m, n) hasta (0, 0).
"""


def tabla_lcs(x, y):
    m = len(x)
    n = len(y)
    L = [[0] * (n + 1)]
    for i in range(1, m + 1):
        xi = x[i - 1]
        prev = L[i - 1]
        cur = [0] * (n + 1)
        for j in range(1, n + 1):
            if xi == y[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                if prev[j] >= cur[j - 1]:
                    cur[j] = prev[j]
                else:
                    cur[j] = cur[j - 1]
        L.append(cur)
    return L


def reconstruir(L, x, y):
    i = len(x)
    j = len(y)
    sol = []
    while i > 0 and j > 0:
        if x[i - 1] == y[j - 1]:
            sol.append(x[i - 1])
            i -= 1
            j -= 1
        elif L[i - 1][j] >= L[i][j - 1]:
            i -= 1
        else:
            j -= 1
    sol.reverse()
    return "".join(sol)


def lcs_dinamica(x, y):
    """Devuelve una LCS de x e y construyendo la tabla completa O(m * n)."""
    L = tabla_lcs(x, y)
    return reconstruir(L, x, y)
