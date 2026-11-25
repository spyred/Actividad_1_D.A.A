"""Juego de pruebas para comprobar las tres implementaciones de LCS.

Ejecución: python -m unittest discover -s tests -v
"""

import itertools
import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lcs import lcs_dinamica, lcs_hirschberg, lcs_recursiva
from lcs.dinamica import tabla_lcs

TODAS = {"A": lcs_recursiva, "B": lcs_hirschberg, "C": lcs_dinamica}
RAPIDAS = {"B": lcs_hirschberg, "C": lcs_dinamica}


def es_subsecuencia(s, t):
    """Comprueba si s es subsecuencia de t."""
    idx = 0
    for c in t:
        if idx < len(s) and c == s[idx]:
            idx += 1
    return idx == len(s)


def lcs_fuerza_bruta(x, y):
    """Calcula la longitud óptima probando todas las subsecuencias de x."""
    for r in range(len(x), -1, -1):
        for comb in itertools.combinations(range(len(x)), r):
            sub = "".join(x[k] for k in comb)
            if es_subsecuencia(sub, y):
                return r
    return 0


class CasosLimite(unittest.TestCase):
    CASOS = [
        ("", "", ""),
        ("", "ABC", ""),
        ("ABC", "", ""),
        ("A", "A", "A"),
        ("A", "B", ""),
        ("ABC", "ABC", "ABC"),
        ("ABC", "DEF", ""),
        ("AAAA", "AA", "AA"),
        ("ABCBDAB", "BDCABA", None),
    ]

    def test_casos(self):
        for nombre, f in TODAS.items():
            for x, y, esperado in self.CASOS:
                with self.subTest(version=nombre, x=x, y=y):
                    r = f(x, y)
                    self.assertTrue(es_subsecuencia(r, x) and es_subsecuencia(r, y))
                    if esperado is not None:
                        self.assertEqual(r, esperado)
                    else:
                        self.assertEqual(len(r), 4)


class EjemploTema3(unittest.TestCase):
    """Entrenamiento 3 del Tema 3: la LCS tiene longitud 20."""

    A = "ACCGGTCGAGTGCGCGGAAGCCGGCCGAA"
    B = "GTCGTTCGGAATGCCGTTGCTCTGTAAA"

    def test_longitud_20(self):
        for nombre, f in RAPIDAS.items():
            with self.subTest(version=nombre):
                r = f(self.A, self.B)
                self.assertEqual(len(r), 20)
                self.assertTrue(es_subsecuencia(r, self.A) and es_subsecuencia(r, self.B))

    def test_celda_final(self):
        self.assertEqual(tabla_lcs(self.A, self.B)[-1][-1], 20)


class ValidacionCruzada(unittest.TestCase):
    def test_contra_fuerza_bruta(self):
        rnd = random.Random(7)
        for _ in range(300):
            x = "".join(rnd.choice("ACGT") for _ in range(rnd.randint(0, 9)))
            y = "".join(rnd.choice("ACGT") for _ in range(rnd.randint(0, 9)))
            optimo = lcs_fuerza_bruta(x, y)
            for nombre, f in TODAS.items():
                with self.subTest(version=nombre, x=x, y=y):
                    r = f(x, y)
                    self.assertEqual(len(r), optimo)
                    self.assertTrue(es_subsecuencia(r, x) and es_subsecuencia(r, y))

    def test_b_igual_a_c_en_cadenas_largas(self):
        rnd = random.Random(11)
        for m, n in [(300, 300), (500, 137), (1, 400), (257, 2)]:
            x = "".join(rnd.choice("ACGT") for _ in range(m))
            y = "".join(rnd.choice("ACGT") for _ in range(n))
            rb = lcs_hirschberg(x, y)
            rc = lcs_dinamica(x, y)
            self.assertEqual(len(rb), len(rc))
            self.assertTrue(es_subsecuencia(rb, x) and es_subsecuencia(rb, y))


class LlamadasVersionA(unittest.TestCase):
    """Comprueba la fórmula 2*C(m+n, n) - 1 en el peor caso y n + 1 en el mejor."""

    def test_formula_peor_caso(self):
        for m in range(0, 8):
            for n in range(0, 8):
                c = [0]
                lcs_recursiva("A" * m, "B" * n, c)
                self.assertEqual(c[0], 2 * math.comb(m + n, n) - 1)

    def test_mejor_caso_lineal(self):
        c = [0]
        lcs_recursiva("ACGT" * 50, "ACGT" * 50, c)
        self.assertEqual(c[0], 201)


if __name__ == "__main__":
    unittest.main()
