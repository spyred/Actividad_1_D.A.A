"""Proceso de medición aislado: una versión sobre una pareja de cadenas.

Cada medición se lanza en un proceso Python nuevo para que la memoria de
una ejecución no contamine la siguiente. Dos modos:

  tiempo  -> tiempo de CPU (time.process_time) de R repeticiones y el
             incremento de memoria residente máxima (ru_maxrss) del proceso.
  memoria -> pico de memoria reservada por el algoritmo (tracemalloc).
             Se mide aparte porque tracemalloc ralentiza la ejecución.

Imprime una línea JSON con el resultado.
"""

import argparse
import gc
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from lcs import VERSIONES


def maxrss_windows():
    # Windows no tiene el módulo resource: se usa GetProcessMemoryInfo de la API de Windows
    import ctypes
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    contadores = PROCESS_MEMORY_COUNTERS()
    contadores.cb = ctypes.sizeof(contadores)
    kernel32 = ctypes.windll.kernel32
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.K32GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
    kernel32.K32GetProcessMemoryInfo(kernel32.GetCurrentProcess(),
                                     ctypes.byref(contadores), contadores.cb)
    return contadores.PeakWorkingSetSize // 1024   # bytes -> KiB


def maxrss_kib():
    # Memoria residente máxima del proceso en KiB
    if sys.platform == "win32":
        return maxrss_windows()
    import resource
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # En Linux ru_maxrss viene en KiB; en macOS, en bytes
    if sys.platform == "darwin":
        return r // 1024
    return r


def tiempo_cpu(f, x, y, minimo=0.25):
    # En Windows el reloj de CPU avanza a saltos de unos 15,6 ms, así que un cálculo
    # rápido mediría 0. Se repite hasta acumular al menos `minimo` segundos de CPU
    # y se divide entre el número de repeticiones.
    veces = 0
    t0 = time.process_time()
    while True:
        r = f(x, y)
        veces += 1
        transcurrido = time.process_time() - t0
        if transcurrido >= minimo:
            return transcurrido / veces, r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, choices=VERSIONES)
    ap.add_argument("--datos", required=True)
    ap.add_argument("--indice", type=int, required=True)
    ap.add_argument("--modo", choices=["tiempo", "memoria"], default="tiempo")
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()

    par = json.loads(Path(a.datos).read_text())[a.indice]
    x, y = par["x"], par["y"]
    f = VERSIONES[a.version][1]
    gc.collect()

    if a.modo == "tiempo":
        rss0 = maxrss_kib()
        tiempos = []
        for _ in range(a.reps):
            t, r = tiempo_cpu(f, x, y)
            tiempos.append(t)
            longitud = len(r)
            del r
            gc.collect()
        out = {
            "cpu_mediana_s": statistics.median(tiempos),
            "cpu_min_s": min(tiempos),
            "rss_incremento_kib": maxrss_kib() - rss0,
            "len_lcs": longitud,
        }
    else:
        tracemalloc.start()
        r = f(x, y)
        _, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        out = {"pico_tracemalloc_bytes": pico, "len_lcs": len(r)}

    print(json.dumps(out))


if __name__ == "__main__":
    main()
