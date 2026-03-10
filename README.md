Parser

Miembros del equipo:
Alejandro Ceja Cervantes.
Covarrubias Martinez Hector.
Escobar Rubio Dominic.

Este proyecto implementa un analizador léxico y sintáctico para Java, desarrollado en Python usando FastAPI.

El sistema recibe código fuente, lo tokeniza y luego construye un Árbol de Sintaxis Abstracta (AST) mediante análisis sintáctico.

El resultado se devuelve en formato JSON, lo que permite visualizar la estructura del programa.

-- Características --

Análisis léxico.

Identificación de tokens.

Reconocimiento de palabras clave.

Manejo de números, cadenas, operadores y delimitadores.

 -- Análisis sintáctico --

Construcción de AST (Abstract Syntax Tree)

Soporte para:

Clases.

Métodos.

Declaraciones de variables.

Asignaciones.

Expresiones aritméticas.

Condicionales if / else

Ciclos while

return

print / System.out.println

API REST con FastAPI

Respuesta en JSON estructurado

Integración con frontend estático

uvicorn main:app --reload
