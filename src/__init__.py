"""
Módulo raíz del código fuente de Crypto Portfolio Tracker v3.

Este paquete sigue un layout tipo `src/` para:
- Evitar importar código por accidente desde el árbol de trabajo.
- Hacer más explícito el código que realmente forma parte del paquete.
- Facilitar empaquetado, tests y despliegue.

Los subpaquetes principales son:
- src.database  -> Modelos y gestión de base de datos
- src.api       -> Conectores a exchanges, blockchain y DeFi
- src.utils     -> Utilidades comunes (config, logging, validación)
- src.services  -> Lógica de negocio (portfolio, reportes, impuestos)
"""

__all__ = [
    "database",
    "api",
    "utils",
    "services",
]
