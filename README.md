COMPILADOR – Análisis Léxico, Sintáctico y TAC

Descripción
Este proyecto es un compilador para un lenguaje simple. Incluye:
- Análisis léxico (tokens)
- Análisis sintáctico (AST)
- Generación de código intermedio (TAC)
- Tabla de símbolos
- Visualización opcional del AST usando Tkinter

El código fuente del programa se toma desde un archivo llamado datos.txt ubicado en el mismo directorio.

Cómo ejecutar el programa

1. Requisitos
- Python 3.6 o superior
- Tkinter instalado (solo si deseas ver el AST)

2. Archivos necesarios
Debes tener en la misma carpeta:
- tablasimbolos.py 
- datos.txt

3. Ejecutar el compilador
En la terminal:
python3 tablasimbolos.py

El programa mostrará:
- Código fuente leído
- Tokens generados
- Resultado del análisis
- Código TAC
- Tabla de símbolos

Finalmente preguntará si deseas visualizar el AST gráficamente con Tkinter.
Pulsa s si deseas abrir el visualizador o n de lo contrario.
