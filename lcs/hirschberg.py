"""Versión B: LCS mediante divide y conquista (algoritmo de Hirschberg).

Divide la cadena x por la mitad y busca el índice k de y por donde pasa
una LCS óptima usando únicamente dos filas de la tabla de programación dinámica.
"""


def ultima_fila(x, y):
    """Calcula la última fila de la tabla LCS de x frente a y usando O(len(y)) memoria."""
    n = len(y)
    prev = [0] * (n + 1)
    for xi in x:
        cur = [0] * (n + 1)
        for j in range(1, n + 1):
            if xi == y[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                if prev[j] >= cur[j - 1]:
                    cur[j] = prev[j]
                else:
                    cur[j] = cur[j - 1]
        prev = cur
    return prev


def hirschberg_rec(x, y, partes):
    m = len(x)
    n = len(y)
    if m == 0 or n == 0:
        return
    if m == 1:
        if x in y:
            partes.append(x)
        return

    mid = m // 2
    l1 = ultima_fila(x[:mid], y)
    l2 = ultima_fila(x[mid:][::-1], y[::-1])

    mejor = -1
    k = 0
    for j in range(n + 1):
        suma = l1[j] + l2[n - j]
        if suma > mejor:
            mejor = suma
            k = j

    hirschberg_rec(x[:mid], y[:k], partes)
    hirschberg_rec(x[mid:], y[k:], partes)


def lcs_hirschberg(x, y):
    """Devuelve una LCS de x e y en espacio lineal O(m + n)."""
    partes = []
    hirschberg_rec(x, y, partes)
    return "".join(partes)
