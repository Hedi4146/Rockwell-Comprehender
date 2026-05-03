"""Tokenizer subpackage — parsing de código RLL/ST/FBD para uso de tracer.py.

Construido en v0.2 (DT-009: el código se construye cuando se necesita).
v0.1 no requería tokenización porque sus capas operan a nivel de string.

Estado actual:
- rll_tokenizer.py: implementado en Paso 1 de v0.2
- st_tokenizer.py: pendiente — los proyectos del parque tienen muy poco ST
  (1-2 routines en CINTA+AQL); se construye cuando aparezca caso real
- fbd_tokenizer.py: pendiente — sin uso productivo en parque actual
"""

from .rll_tokenizer import Instruction, Operand, Rung, tokenize_rll

__all__ = ["tokenize_rll", "Rung", "Instruction", "Operand"]
