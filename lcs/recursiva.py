"""Versión A: LCS recursiva directa (sin memorización).

Aplica directamente la recurrencia del Tema 3:
- LCS(i, j) = 0                              si i == 0 o j == 0
- LCS(i, j) = LCS(i-1, j-1) + 1              si x[i-1] == y[j-1]
- LCS(i, j) = max(LCS(i-1, j), LCS(i, j-1))  en otro caso
"""

import sys

# Ampliamos el límite de recursión para cadenas largas en el mejor caso
sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))


def lcs_recursiva(x, y, contador=None):
    """Devuelve una LCS de x e y. Si se pasa contador=[0], cuenta las llamadas."""

    def rec(i, j):
        if contador is not None:
            contador[0] += 1
        if i == 0 or j == 0:
            return ""
        if x[i - 1] == y[j - 1]:
            return rec(i - 1, j - 1) + x[i - 1]
        izq = rec(i - 1, j)
        der = rec(i, j - 1)
        if len(izq) >= len(der):
            return izq
        return der

    return rec(len(x), len(y))
