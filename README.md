Parser

Miembros del equipo:
Alejandro Ceja Cervantes
Covarrubias Martinez Hector
Escobar Rubio Dominic

Este proyecto implementa un analizador léxico y sintáctico para Java, desarrollado en Python usando FastAPI.

El sistema recibe código fuente, lo tokeniza y luego construye un Árbol de Sintaxis Abstracta (AST) mediante análisis sintáctico.

El resultado se devuelve en formato JSON, lo que permite visualizar la estructura del programa.

-- Características --

Análisis léxico

Identificación de tokens

Reconocimiento de palabras clave

Manejo de números, cadenas, operadores y delimitadores

 -- Análisis sintáctico --

Construcción de AST (Abstract Syntax Tree)

Soporte para:

Clases

Métodos

Declaraciones de variables

Asignaciones

Expresiones aritméticas

Condicionales if / else

Ciclos while

return

print / System.out.println

API REST con FastAPI

Respuesta en JSON estructurado

Integración con frontend estático

-- Arquitectura del Proyecto --
project/
│
├── main.py
├── static/
│   └── index.html
│
└── README.md

---- Instalación ----
Clonar el repositorio
git clone https://github.com/tuusuario/analizador-lexico-sintactico.git
cd analizador-lexico-sintactico

Crear entorno virtual (opcional pero recomendado)
python -m venv venv

-- Activar entorno --

Windows
venv\Scripts\activate

Linux / Mac
source venv/bin/activate

-- Instalar dependencias --
pip install fastapi uvicorn pydantic
-- Ejecutar el servidor --
python main.py

o

uvicorn main:app --reload
