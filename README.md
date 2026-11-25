# LCS: recursiva directa, Hirschberg y programación dinámica

Actividad 1 de **Diseño Avanzado de Algoritmos** (Temas 1, 2 y 3). Implementación y comparación
experimental de tres algoritmos para la subsecuencia común más larga (LCS) de dos cadenas.

| Versión | Fichero | Técnica | Tiempo | Memoria |
|---|---|---|---|---|
| A | `lcs/recursiva.py`  | Recursión directa, sin memorizar | Θ(min(m,n)) mejor caso, Θ(C(m+n,n)) peor caso | Θ(m+n) (pila) |
| B | `lcs/hirschberg.py` | Divide y conquista (Hirschberg)   | Θ(m·n) | Θ(m+n) |
| C | `lcs/dinamica.py`   | PD tabular + reconstrucción       | Θ(m·n) | Θ(m·n) |

Todo el proyecto usa la biblioteca estándar de Python (≥ 3.9). Para generar las gráficas se
requiere `matplotlib` (`pip install -r requirements.txt`).

## Ejecución

```bash
python ejecutar.py          # ejecuta pruebas, experimentos y genera tablas y gráficas
python ejecutar.py --demo   # demostración rápida con el ejemplo del Tema 3
python -m unittest discover -s tests -v   # sólo pruebas unitarias
```

## Estructura del proyecto

```
lcs/            implementación de las versiones A, B y C
tests/          pruebas unitarias (unittest)
bench/
  experimentos.py  genera los datos de prueba y lanza las mediciones
  medir.py         ejecuta una medición aislada en un proceso nuevo
  graficas.py      procesa los CSV y genera tablas y gráficas
datos/          parejas de cadenas generadas (semilla 2026)
resultados/     CSV de mediciones, tablas y figuras PNG
memoria/        memoria en LaTeX y PDF
```

## Publicar el repositorio en GitHub

```bash
git init
git add .
git commit -m "Actvidad 1 LCS: versiones A, B y C"
git branch -M main
git remote add origin https://github.com/spyred/Actividad_1_D.A.A.git
git push -u origin main
```

