"""Punto de entrada único: tests + experimentos + gráficas.

    python ejecutar.py             # todo (≈ 3 min)
    python ejecutar.py --demo      # sólo una demostración rápida de las tres versiones

Equivale a `make`. Útil en Windows, donde `make` no suele estar instalado.
"""

import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


def paso(titulo, args):
    print(f"\n=== {titulo} ===", flush=True)
    t0 = time.time()
    subprocess.run([sys.executable, *args], cwd=RAIZ, check=True)
    print(f"({time.time() - t0:.1f} s)")


def demo():
    sys.path.insert(0, str(RAIZ))
    from lcs import VERSIONES

    x, y = "ACCGGTCGAGTGCGCGGAAGCCGGCCGAA", "GTCGTTCGGAATGCCGTTGCTCTGTAAA"
    print(f"x = {x}\ny = {y}  (Tema 3, Entrenamiento 3)\n")
    for clave, (nombre, f) in VERSIONES.items():
        if clave == "A":
            x2, y2 = x[:12], y[:12]
            r = f(x2, y2)
            print(f"{clave} {nombre:33s} (12 primeros símbolos) -> {r} (|LCS| = {len(r)})")
        else:
            r = f(x, y)
            print(f"{clave} {nombre:33s} -> {r} (|LCS| = {len(r)})")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
        sys.exit()
    paso("Tests de corrección", ["-m", "unittest", "discover", "-s", "tests", "-v"])
    paso("Experimentos", ["bench/experimentos.py"])
    paso("Gráficas y tablas", ["bench/graficas.py"])
    print("\nResultados en la carpeta resultados/")
