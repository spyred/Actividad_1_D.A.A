"""Genera tablas, cifras y (si matplotlib está instalado) figuras a partir de los CSV.

Sólo necesita la biblioteca estándar. Si matplotlib no está disponible, se
generan igualmente las tablas y las cifras, y se avisa de que faltan las figuras.

Salidas en resultados/:
  tabla_grande.tex   filas de la tabla del Experimento 1 (la incluye la memoria)
  cifras.tex         macros LaTeX con todas las cifras citadas en el texto
  resumen.json       ajustes y extrapolaciones
  fig_*.png          figuras (opcional)
"""

import csv
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "resultados"

# Colores fijos para cada versión.
COLOR = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
NOMBRE = {"A": "A · recursiva directa", "B": "B · Hirschberg", "C": "C · PD tabular"}
TINTA, TINTA2, REJILLA = "#0b0b0b", "#52514e", "#e4e3df"
ANCHO_IN = 6.2      # la memoria incluye las figuras a este ancho exacto (escala 1:1)
PT = 11             # tamaño mínimo de letra exigido por el enunciado


# ---------------------------------------------------------------- utilidades
def leer(ruta):
    with ruta.open() as fh:
        return list(csv.DictReader(fh))


def recta(xs, ys):
    """Ajuste por mínimos cuadrados y = a + b·x. Devuelve (a, b)."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my - b * mx, b


def pendiente_loglog(xs, ys):
    return recta([math.log(x) for x in xs], [math.log(y) for y in ys])[1]


def coma(v, dec=1):
    return f"{v:.{dec}f}".replace(".", "{,}")


def cientifica(v, dec=1):
    e = math.floor(math.log10(v))
    m = v / 10 ** e
    if round(m, dec) >= 10:
        m, e = m / 10, e + 1
    return f"{coma(m, dec)}\\cdot 10^{{{e}}}"


# ---------------------------------------------------------------- análisis
def analizar():
    grande = leer(RES / "experimento_grande.csv")
    peq = leer(RES / "experimento_pequeno.csv")
    ok = {v: [r for r in grande if r["version"] == v and r["estado"] == "ok"] for v in "ABC"}
    reg = {g: [r for r in peq if r["regimen"] == g] for g in ("iguales", "aleatorias", "disjuntas")}

    # Extrapolación de A: log(llamadas) = a + b·n en el régimen aleatorio (n >= 6)
    aj = [r for r in reg["aleatorias"] if int(r["n"]) >= 6]
    a, b = recta([int(r["n"]) for r in aj], [math.log(int(r["llamadas_A"])) for r in aj])
    medibles = [r for r in peq if float(r["cpu_A_s"]) > 0.05]
    s_llamada = sum(float(r["cpu_A_s"]) for r in medibles) / sum(int(r["llamadas_A"]) for r in medibles)

    def log10_seg_A(n):
        return (a + b * n) / math.log(10) + math.log10(s_llamada)

    return grande, peq, ok, reg, math.exp(b), s_llamada, log10_seg_A


def escribir_tablas_y_cifras(grande, peq, ok, reg, base, s_llamada, log10_seg_A):
    porn = {}
    for r in grande:
        porn.setdefault(int(r["n"]), {})[r["version"]] = r
    lineas = []
    for n in sorted(porn):
        bb, cc = porn[n]["B"], porn[n]["C"]
        tb, tc = float(bb["cpu_mediana_s"]), float(cc["cpu_mediana_s"])
        lineas.append(
            f"{n} & {cc['len_lcs']} & $10^{{{log10_seg_A(n):.0f}}}$ & {coma(tb, 3)} & {coma(tc, 3)} & "
            f"{coma(tb / tc, 2) if tc > 0 else '--'} & {coma(int(bb['pico_tracemalloc_bytes']) / 2**20, 2)} & "
            f"{coma(int(cc['pico_tracemalloc_bytes']) / 2**20, 2)} & "
            f"{coma(int(cc['rss_incremento_kib']) / 1024, 1)} \\\\")
    (RES / "tabla_grande.tex").write_text("\n".join(lineas) + "\n")

    # Tabla del Experimento 2: la última talla medida de cada régimen
    lin2 = []
    for g, r in ((g, max(reg[g], key=lambda r: int(r["n"]))) for g in reg):
        lin2.append(f"{g} & {r['n']} & {int(r['llamadas_A']):,}".replace(",", ".") +
                    f" & {coma(float(r['cpu_A_s']) * 1e3, 3)} & {coma(float(r['cpu_B_s']) * 1e3, 3)}"
                    f" & {coma(float(r['cpu_C_s']) * 1e3, 3)} \\\\")
    (RES / "tabla_pequeno.tex").write_text("\n".join(lin2) + "\n")

    # Cifras citadas en el texto (para que el texto nunca contradiga a las tablas)
    B, C = ok["B"], ok["C"]
    nB = [int(r["n"]) for r in B]
    tB = [float(r["cpu_mediana_s"]) for r in B]
    tC = [float(r["cpu_mediana_s"]) for r in C]
    mB = [int(r["pico_tracemalloc_bytes"]) for r in B]
    mC = [int(r["pico_tracemalloc_bytes"]) for r in C]
    desde = [i for i, n in enumerate(nB) if n >= 250]
    ratios = [tB[i] / tC[i] for i in desde if tC[i] > 0]
    factores = [mC[i + 1] / mC[i] for i in range(len(mC) - 1) if nB[i] >= 500]
    celdas = [mC[i] / (nB[i] + 1) ** 2 for i in range(len(nB))]
    ale, dis, igu = (max(reg[g], key=lambda r: int(r["n"])) for g in ("aleatorias", "disjuntas", "iguales"))
    n_ale = int(ale["n"])
    pend = lambda xs, ys: pendiente_loglog(xs[2:], ys[2:])
    ab = [r for r in grande if r["version"] == "A" and r["estado"] != "ok" and r["estado"] != "no ejecutada"]
    m = {
        "Nmax": nB[-1],
        "Nabort": ab[0]["n"] if ab else "--",
        "Alimite": "30",
        "Abase": coma(base, 1),
        "Allamada": coma(s_llamada * 1e6, 2),
        "AestCien": f"{log10_seg_A(100):.0f}",
        "AestMil": f"{log10_seg_A(1000):.0f}",
        "AaleN": n_ale,
        "AaleLlamadas": cientifica(int(ale["llamadas_A"])),
        "AaleSeg": coma(float(ale["cpu_A_s"]), 1),
        "CaleMicro": coma(float(ale["cpu_C_s"]) * 1e6, 0),
        "Celdas": (n_ale + 1) ** 2,
        "Repeticiones": cientifica(int(ale["llamadas_A"]) / (n_ale + 1) ** 2),
        "AdisN": dis["n"],
        "AdisLlamadas": cientifica(int(dis["llamadas_A"])),
        "AdisSeg": coma(float(dis["cpu_A_s"]), 1),
        "AiguN": igu["n"],
        "AiguMicro": coma(float(igu["cpu_A_s"]) * 1e6, 0),
        "CiguMicro": coma(float(igu["cpu_C_s"]) * 1e6, 0),
        "PendTB": coma(pend(nB, tB), 2),
        "PendTC": coma(pend(nB, tC), 2),
        "PendMB": coma(pend(nB, mB), 1),
        "RatioMin": coma(min(ratios), 1),
        "RatioMax": coma(max(ratios), 1),
        "TBmax": coma(tB[-1], 1),
        "TCmax": coma(tC[-1], 1),
        "MemCmil": coma(mC[nB.index(1000)] / 2**20, 1),
        "MemCmax": coma(mC[-1] / 2**20, 1),
        "MemBmax": coma(mB[-1] / 2**20, 2),
        "RatioMem": f"{round(mC[-1] / mB[-1], -1):.0f}",
        "FactMin": coma(min(factores), 1),
        "FactMax": coma(max(factores), 1),
        "CeldaMin": coma(min(celdas), 1),
        "CeldaMax": coma(max(celdas), 0),
        "GiBVeinteMil": coma(max(celdas) * 20001 ** 2 / 2**30, 1),
        "RssCmax": coma(int(C[-1]["rss_incremento_kib"]) / 1024, 1),
    }
    ruta_entorno = RES / "entorno.json"
    if ruta_entorno.exists():
        e = json.loads(ruta_entorno.read_text())
        entorno = f"Python {e['python']} en {e['sistema']}, procesador {e['procesador']}"
        # Caracteres especiales de LaTeX
        for car in ("_", "&", "%", "#"):
            entorno = entorno.replace(car, "\\" + car)
        m["Entorno"] = entorno
    else:
        m["Entorno"] = "entorno no registrado"
    texto = "% Generado por bench/graficas.py a partir de los CSV. No editar a mano.\n"
    texto += "".join(f"\\newcommand{{\\cifra{k}}}{{{v}}}\n" for k, v in m.items())
    (RES / "cifras.tex").write_text(texto)

    resumen = {"base_crecimiento_A": base, "s_por_llamada_A": s_llamada,
               "A_estimado_log10_s": {n: log10_seg_A(n) for n in (30, 50, 100, 1000, 4000)},
               "pendiente_tiempo": {"B": pend(nB, tB), "C": pend(nB, tC)},
               "pendiente_memoria": {"B": pend(nB, mB), "C": pend(nB, mC)},
               "bytes_por_celda_C": dict(zip(nB, celdas)), "cifras": m}
    (RES / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False))
    return m


# ---------------------------------------------------------------- figuras
def figuras(peq, ok, reg, base, log10_seg_A):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (matplotlib no está instalado: se omiten las figuras; tablas y CSV sí se generan)")
        return False

    plt.rcParams.update({
        "font.size": PT, "axes.titlesize": PT, "axes.labelsize": PT, "xtick.labelsize": PT,
        "ytick.labelsize": PT, "legend.fontsize": PT, "axes.edgecolor": TINTA2,
        "axes.labelcolor": TINTA, "xtick.color": TINTA2, "ytick.color": TINTA2,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.color": REJILLA, "grid.linewidth": 0.6, "legend.frameon": False,
        "lines.linewidth": 1.8, "lines.markersize": 5, "savefig.dpi": 200,
    })
    ale = reg["aleatorias"]

    def guardar(fig, nombre):
        fig.savefig(RES / nombre)          # sin bbox="tight": tamaño exacto = ANCHO_IN
        plt.close(fig)

    # Figura 1: tiempo de CPU (log-log)
    fig, ax = plt.subplots(figsize=(ANCHO_IN, 3.1), layout="constrained")
    for v in "BC":
        xs = [int(r["n"]) for r in ale if float(r[f"cpu_{v}_s"]) > 0] + [int(r["n"]) for r in ok[v]]
        ys = [float(r[f"cpu_{v}_s"]) for r in ale if float(r[f"cpu_{v}_s"]) > 0] + \
             [float(r["cpu_mediana_s"]) for r in ok[v]]
        ax.plot(xs, ys, "o-", color=COLOR[v], label=NOMBRE[v])
    xa = [int(r["n"]) for r in ale if float(r["cpu_A_s"]) > 1e-5]
    ya = [float(r["cpu_A_s"]) for r in ale if float(r["cpu_A_s"]) > 1e-5]
    ax.plot(xa, ya, "o-", color=COLOR["A"], label=NOMBRE["A"] + " (medida)")
    xe = list(range(xa[-1], 61))
    ax.plot(xe, [10 ** log10_seg_A(n) for n in xe], "--", color=COLOR["A"], lw=1.4,
            label=f"A extrapolada (≈{base:.1f}$^n$)".replace(".", ","))
    ax.set(xscale="log", yscale="log", xlim=(1, 10000), ylim=(1e-7, 1e18),
           xlabel="longitud de cada cadena n (m = n)", ylabel="CPU (s)")
    ax.set_yticks([1e-6, 1e-3, 1, 1e3, 1e6, 1e9, 1e12, 1e15, 1e18])
    ax.legend(loc="upper right")
    guardar(fig, "fig_tiempo.png")

    # Figura 2: pico de memoria (log-log)
    fig, ax = plt.subplots(figsize=(ANCHO_IN, 2.7), layout="constrained")
    for v in "BC":
        ax.plot([int(r["n"]) for r in ok[v]], [int(r["pico_tracemalloc_bytes"]) / 2**20 for r in ok[v]],
                "o-", color=COLOR[v], label=NOMBRE[v])
    cp = [r for r in ale if r.get("pico_A_bytes")]
    ax.plot([int(r["n"]) for r in cp], [int(r["pico_A_bytes"]) / 2**20 for r in cp],
            "o-", color=COLOR["A"], label=NOMBRE["A"])
    ax.set(xscale="log", yscale="log", xlim=(1, 10000),
           xlabel="longitud de cada cadena n (m = n)", ylabel="pico de memoria (MiB)")
    ax.legend(loc="upper left")
    guardar(fig, "fig_memoria.png")

    # Figura 3: llamadas de A por régimen frente a la teoría
    fig, ax = plt.subplots(figsize=(ANCHO_IN, 2.9), layout="constrained")
    estilos = {"iguales": ("#008300", "s", "iguales"), "aleatorias": (COLOR["A"], "o", "aleatorias"),
               "disjuntas": ("#6250d6", "^", "disjuntas")}
    for g, (col, mk, nom) in estilos.items():
        ax.plot([int(r["n"]) for r in reg[g]], [int(r["llamadas_A"]) for r in reg[g]], mk,
                color=col, label=nom)
    n_dis = max(int(r["n"]) for r in reg["disjuntas"])
    ax.plot(range(1, 31), [k + 1 for k in range(1, 31)], "-", color=TINTA2, lw=1, label="n + 1")
    ax.plot(range(1, n_dis + 1), [2 * math.comb(2 * k, k) - 1 for k in range(1, n_dis + 1)], "--",
            color=TINTA2, lw=1, label="2·C(2n, n) − 1")
    ax.set(yscale="log", xlim=(0, 31), xlabel="n (m = n)", ylabel="llamadas de A")
    ax.legend(loc="center right", ncol=1)
    guardar(fig, "fig_llamadas_A.png")
    return True


def main():
    grande, peq, ok, reg, base, s_llamada, log10_seg_A = analizar()
    m = escribir_tablas_y_cifras(grande, peq, ok, reg, base, s_llamada, log10_seg_A)
    hay = figuras(peq, ok, reg, base, log10_seg_A)
    txt = (f"  A crece ≈ {m['Abase']}^n · B/C entre {m['RatioMin']} y {m['RatioMax']} · "
           f"memoria C/B ≈ {m['RatioMem']}x con n = {m['Nmax']}")
    print(txt.replace("{,}", ","))
    print("  -> resultados/tabla_grande.tex, tabla_pequeno.tex, cifras.tex, resumen.json"
          + (", fig_*.png" if hay else ""))


if __name__ == "__main__":
    main()
