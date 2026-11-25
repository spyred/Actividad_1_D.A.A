"""Tres algoritmos para la subsecuencia común más larga (LCS)."""

from .recursiva import lcs_recursiva
from .hirschberg import lcs_hirschberg
from .dinamica import lcs_dinamica

VERSIONES = {
    "A": ("Recursiva directa", lcs_recursiva),
    "B": ("Hirschberg (divide y conquista)", lcs_hirschberg),
    "C": ("Programación dinámica tabular", lcs_dinamica),
}

__all__ = ["lcs_recursiva", "lcs_hirschberg", "lcs_dinamica", "VERSIONES"]
