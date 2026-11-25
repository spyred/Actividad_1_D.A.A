"""Orquesta los experimentos y escribe los CSV en resultados/.

Experimento 1 (grande): parejas de ADN aleatorio de longitud creciente
  (100 ... 4000). Para cada versión y pareja se lanza bench/medir.py en un
  proceso nuevo, una vez en modo "tiempo" y otra en modo "memoria".
  La versión A se intenta con un límite de tiempo; si lo agota en una
  talla, no se prueba en tallas mayores (su coste es monótono en n).

Experimento 2 (pequeño): la versión A frente a B y C en cadenas cortas,
  en tres regímenes que fijan su mejor, típico y peor caso:
    iguales    x == y                  -> A hace min(m,n)+1 llamadas
    aleatorias ADN independiente       -> caso típico
    disjuntas  x en {A,C}, y en {G,T}  -> A hace 2*C(m+n,n)-1 llamadas
"""

import csv
import json
import random
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from lcs import VERSIONES, lcs_dinamica, lcs_hirschberg, lcs_recursiva

DATOS = RAIZ / "datos"
RES = RAIZ / "resultados"
TALLAS = [100, 250, 500, 1000, 2000, 4000]
SEMILLA = 2026
LIMITE_A_S = 30        # tiempo máximo que se deja correr a la versión A
REPS = 3               # repeticiones por medición de tiempo (se reporta la mediana)


def nombre_procesador():
    import platform
    try:
        if sys.platform == "win32":
            import winreg
            clave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(clave, "ProcessorNameString")[0].strip()
        if sys.platform.startswith("linux"):
            for linea in Path("/proc/cpuinfo").read_text().splitlines():
                if linea.startswith("model name"):
                    return linea.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def guardar_entorno():
    # Guarda Python, sistema operativo y procesador para citarlos en la memoria
    import platform
    if sys.platform == "win32":
        sistema = "Windows " + platform.release()
    else:
        sistema = platform.system() + " " + platform.release()
    entorno = {
        "python": platform.python_version(),
        "sistema": sistema,
        "procesador": " ".join(nombre_procesador().split()),
    }
    RES.mkdir(exist_ok=True)
    (RES / "entorno.json").write_text(json.dumps(entorno, indent=2, ensure_ascii=False))
    print("  Entorno:", entorno["python"], "·", entorno["sistema"], "·", entorno["procesador"])


def generar_parejas() -> Path:
    rnd = random.Random(SEMILLA)
    pares = []
    for n in TALLAS:
        x = "".join(rnd.choice("ACGT") for _ in range(n))
        y = "".join(rnd.choice("ACGT") for _ in range(n))
        pares.append({"n": n, "x": x, "y": y})
    DATOS.mkdir(exist_ok=True)
    ruta = DATOS / "parejas.json"
    ruta.write_text(json.dumps(pares, indent=1))
    return ruta


def lanzar(version, ruta, indice, modo, timeout=None):
    cmd = [sys.executable, str(RAIZ / "bench" / "medir.py"), "--version", version,
           "--datos", str(ruta), "--indice", str(indice), "--modo", modo,
           "--reps", str(REPS)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
    except subprocess.TimeoutExpired:
        return None
    return json.loads(p.stdout.strip().splitlines()[-1])


def experimento_grande():
    ruta = generar_parejas()
    filas = []
    a_abortada = False
    for idx, n in enumerate(TALLAS):
        for v in VERSIONES:
            fila = {"n": n, "version": v}
            if v == "A":
                if a_abortada:
                    fila["estado"] = "no ejecutada"
                    filas.append(fila)
                    print(f"  n={n:5d}  A  no se ejecuta (ya superó el límite en una talla menor)")
                    continue
                t = lanzar(v, ruta, idx, "tiempo", timeout=LIMITE_A_S)
                if t is None:
                    a_abortada = True
                    fila["estado"] = f"> {LIMITE_A_S} s (abortada)"
                    filas.append(fila)
                    print(f"  n={n:5d}  A  abortada tras {LIMITE_A_S} s")
                    continue
            else:
                t = lanzar(v, ruta, idx, "tiempo")
            mem = lanzar(v, ruta, idx, "memoria")
            fila.update(estado="ok", **t, pico_tracemalloc_bytes=mem["pico_tracemalloc_bytes"])
            filas.append(fila)
            print(f"  n={n:5d}  {v}  cpu={t['cpu_mediana_s']:.3f} s  "
                  f"pico={mem['pico_tracemalloc_bytes'] / 2**20:.2f} MiB  "
                  f"rss+={t['rss_incremento_kib'] / 1024:.1f} MiB  |LCS|={t['len_lcs']}")
    campos = ["n", "version", "estado", "cpu_mediana_s", "cpu_min_s",
              "pico_tracemalloc_bytes", "rss_incremento_kib", "len_lcs"]
    escribir_csv(RES / "experimento_grande.csv", filas, campos)


def regimen(nombre, n, rnd):
    if nombre == "iguales":
        x = "".join(rnd.choice("ACGT") for _ in range(n))
        return x, x
    if nombre == "aleatorias":
        return ("".join(rnd.choice("ACGT") for _ in range(n)),
                "".join(rnd.choice("ACGT") for _ in range(n)))
    return ("".join(rnd.choice("AC") for _ in range(n)),
            "".join(rnd.choice("GT") for _ in range(n)))


def cronometrar(f, x, y, minimo=0.2):
    # Repite el cálculo hasta acumular al menos `minimo` segundos de CPU, porque en
    # Windows el reloj de CPU avanza a saltos de unos 15,6 ms y un cálculo corto mediría 0
    veces = 0
    t0 = time.process_time()
    while True:
        f(x, y)
        veces += 1
        transcurrido = time.process_time() - t0
        if transcurrido >= minimo:
            return transcurrido / veces


def pico(f, x, y):
    tracemalloc.start()
    f(x, y)
    _, p = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return p


def experimento_pequeno(limite_por_talla=5.0):
    rnd = random.Random(SEMILLA + 1)
    filas = []
    for reg in ["iguales", "aleatorias", "disjuntas"]:
        for n in range(1, 31):
            x, y = regimen(reg, n, rnd)
            c = [0]
            t0 = time.process_time()
            lcs_recursiva(x, y, c)
            ta = time.process_time() - t0
            if ta < 0.2:
                # Ejecución corta: se mide sin el contador y repitiendo
                ta = cronometrar(lcs_recursiva, x, y)
            fila = {"regimen": reg, "n": n, "llamadas_A": c[0], "cpu_A_s": ta,
                    "cpu_B_s": cronometrar(lcs_hirschberg, x, y),
                    "cpu_C_s": cronometrar(lcs_dinamica, x, y)}
            if ta < 1.5:   # tracemalloc ralentiza unas 3x: sólo en tallas asumibles
                for v, f in (("A", lcs_recursiva), ("B", lcs_hirschberg), ("C", lcs_dinamica)):
                    fila[f"pico_{v}_bytes"] = pico(f, x, y)
            filas.append(fila)
            if ta > limite_por_talla:
                break
        print(f"  {reg:10s} hasta n={n}: {c[0]:,} llamadas, {ta:.2f} s")
    escribir_csv(RES / "experimento_pequeno.csv", filas,
                 ["regimen", "n", "llamadas_A", "cpu_A_s", "cpu_B_s", "cpu_C_s",
                  "pico_A_bytes", "pico_B_bytes", "pico_C_bytes"])


def escribir_csv(ruta, filas, campos):
    RES.mkdir(exist_ok=True)
    with ruta.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for f in filas:
            w.writerow({k: f.get(k, "") for k in campos})
    print(f"  -> {ruta.relative_to(RAIZ)}")


if __name__ == "__main__":
    solo = sys.argv[1] if len(sys.argv) > 1 else "todos"
    guardar_entorno()
    if solo in ("todos", "pequeno"):
        print("Experimento 2: versión A en cadenas cortas (mejor / típico / peor caso)")
        experimento_pequeno()
    if solo in ("todos", "grande"):
        print("Experimento 1: parejas de longitud creciente (cada medición en un proceso nuevo)")
        experimento_grande()
