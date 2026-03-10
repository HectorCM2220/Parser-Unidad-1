import re
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Union

app = FastAPI()

class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor

    def __repr__(self):
        return f"Token({self.tipo}, {repr(self.valor)})"

class Nodo:
    def __init__(self, valor, hijos=None):
        self.valor = str(valor)
        self.hijos = hijos if hijos is not None else []

    def dict(self):
        return {
            "valor": self.valor,
            "hijos": [h.dict() for h in self.hijos]
        }

class AnalizadorLexico:
    def __init__(self, codigo):
        self.codigo = codigo
        self.tokens = []
        self.palabras_clave = {
            'public', 'private', 'class', 'static', 'void', 'int', 'float', 'double', 'String',
            'if', 'else', 'while', 'for', 'return', 'System.out.println', 'print'
        }
        self.especificacion_tokens = [
            ('NUMERO',    r'\d+(\.\d*)?'),
            ('CADENA',    r'"[^"]*"'),
            ('ASIGNAR',   r'='),
            ('PUNTOYCOMA',r';'),
            ('COMA',      r','),
            ('COMPARAR',  r'[<>!=]=|[<>]'),
            ('ID',        r'[a-zA-Z_\u00c0-\u017f][a-zA-Z0-9_\u00c0-\u017f.]*'),
            ('OP',        r'[+\-*/]'),
            ('PAR_IZQ',   r'\('),
            ('PAR_DER',   r'\)'),
            ('LLAVE_IZQ', r'\{'),
            ('LLAVE_DER', r'\}'),
            ('COR_IZQ',   r'\['),
            ('COR_DER',   r'\]'),
            ('SALTAR',    r'[ \t\n\r]+'),
            ('ERROR',     r'.'),
        ]

    def tokenizar(self):
        regex_tokens = '|'.join('(?P<%s>%s)' % par for par in self.especificacion_tokens)
        for coincidencia in re.finditer(regex_tokens, self.codigo):
            tipo = coincidencia.lastgroup
            valor = coincidencia.group()
            if tipo == 'NUMERO':
                valor = float(valor) if '.' in valor else int(valor)
            elif tipo == 'ID' and valor in self.palabras_clave:
                tipo = valor.replace('.', '_').upper()
            elif tipo == 'SALTAR':
                continue
            elif tipo == 'ERROR':
                raise RuntimeError(f'{valor!r} inesperado')
            self.tokens.append(Token(tipo, valor))
        return self.tokens

class AnalizadorSintactico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def token_actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consumir(self, tipo_token):
        token = self.token_actual()
        if token and (token.tipo == tipo_token or (isinstance(tipo_token, list) and token.tipo in tipo_token)):
            self.pos += 1
            return token
        return None

    def analizar(self):
        hijos = []
        while self.token_actual():
            bloque = self.sentencia()
            if bloque:
                hijos.append(bloque)
            else:
                self.pos += 1
        
        if len(hijos) == 1:
            return hijos[0]
        return Nodo("Raíz", hijos)

    def sentencia(self):
        token = self.token_actual()
        if not token: return None
        
        if token.tipo in ('PUBLIC', 'PRIVATE', 'CLASS', 'STATIC', 'VOID', 'INT', 'STRING', 'DOUBLE', 'FLOAT', 'ID'):
            if token.tipo == 'CLASS':
                return self.clase()
            
            # Buscar si es un método (hay un '(' antes de ';' o '{')
            temp_pos = self.pos
            es_metodo = False
            while temp_pos < len(self.tokens):
                t = self.tokens[temp_pos]
                if t.tipo == 'PAR_IZQ':
                    es_metodo = True
                    break
                if t.tipo in ('PUNTOYCOMA', 'LLAVE_IZQ', 'LLAVE_DER'):
                    break
                temp_pos += 1
            
            if es_metodo:
                return self.metodo()
            return self.asignacion_o_decl()
        
        elif token.tipo == 'IF':
            return self.si_entonces()
        elif token.tipo == 'WHILE':
            return self.mientras()
        elif token.tipo == 'RETURN':
            self.consumir('RETURN')
            expr = self.expresion()
            if self.token_actual() and self.token_actual().tipo == 'PUNTOYCOMA':
                self.consumir('PUNTOYCOMA')
            return Nodo("return", [expr])
        elif token.tipo == 'PRINT' or token.tipo == 'SYSTEM_OUT_PRINTLN':
            func_token = self.consumir(token.tipo)
            func_name = func_token.valor if func_token else "print"
            self.consumir('PAR_IZQ')
            expr = self.expresion()
            self.consumir('PAR_DER')
            if self.token_actual() and self.token_actual().tipo == 'PUNTOYCOMA':
                self.consumir('PUNTOYCOMA')
            return Nodo(func_name, [expr])
        
        return None

    def clase(self):
        self.consumir('CLASS')
        nombre = self.consumir('ID')
        self.consumir('LLAVE_IZQ')
        cuerpo = self.bloque_llaves()
        self.consumir('LLAVE_DER')
        return Nodo('class', [Nodo(nombre.valor), cuerpo])

    def metodo(self):
        # Consumir modificadores (opcional)
        while self.token_actual() and self.token_actual().tipo in ('PUBLIC', 'PRIVATE', 'STATIC'):
             self.consumir(self.token_actual().tipo)
        
        # Consumir tipo de retorno
        tipo_retorno = self.consumir(['VOID', 'INT', 'STRING', 'DOUBLE', 'FLOAT', 'ID'])
        if not tipo_retorno: return None
        
        nombre = self.consumir('ID')
        if not nombre: return None
        
        self.consumir('PAR_IZQ')
        params = []
        while self.token_actual() and self.token_actual().tipo != 'PAR_DER':
             ptipo_token = self.consumir(['INT', 'STRING', 'DOUBLE', 'FLOAT', 'ID'])
             if not ptipo_token: break
             
             ptipo_str = str(ptipo_token.valor)
             if self.token_actual() and self.token_actual().tipo == 'COR_IZQ':
                 self.consumir('COR_IZQ')
                 self.consumir('COR_DER')
                 ptipo_str += "[]"
                 
             pnombre = self.consumir('ID')
             if pnombre: 
                 params.append(Nodo(f"{ptipo_str} {pnombre.valor}"))
             
             if self.token_actual() and self.token_actual().tipo == 'COMA':
                 self.consumir('COMA')
        
        self.consumir('PAR_DER')
        self.consumir('LLAVE_IZQ')
        cuerpo = self.bloque_llaves()
        self.consumir('LLAVE_DER')
        return Nodo('method', [Nodo(nombre.valor), Nodo('parámetros', params), cuerpo])

    def si_entonces(self):
        self.consumir('IF')
        self.consumir('PAR_IZQ')
        cond = self.expresion()
        self.consumir('PAR_DER')
        self.consumir('LLAVE_IZQ')
        bloque_si = self.bloque_llaves()
        self.consumir('LLAVE_DER')
        hijos = [Nodo("condición", [cond]), Nodo("bloque_if", [bloque_si])]
        
        if self.token_actual() and self.token_actual().tipo == 'ELSE':
            self.consumir('ELSE')
            self.consumir('LLAVE_IZQ')
            bloque_sino = self.bloque_llaves()
            self.consumir('LLAVE_DER')
            hijos.append(Nodo("bloque_else", [bloque_sino]))
        
        return Nodo("if", hijos)

    def mientras(self):
        self.consumir('WHILE')
        self.consumir('PAR_IZQ')
        cond = self.expresion()
        self.consumir('PAR_DER')
        self.consumir('LLAVE_IZQ')
        cuerpo = self.bloque_llaves()
        self.consumir('LLAVE_DER')
        return Nodo("while", [Nodo("condición", [cond]), Nodo("bloque", [cuerpo])])

    def bloque_llaves(self):
        decls = []
        while self.token_actual() and self.token_actual().tipo != 'LLAVE_DER':
            s = self.sentencia()
            if s: decls.append(s)
            else: self.pos += 1
        return Nodo("bloque", decls)

    def asignacion_o_decl(self):
        # Omitir modificadores para encontrar el tipo y nombre
        while self.token_actual() and self.token_actual().tipo in ('PUBLIC', 'PRIVATE', 'STATIC'):
             self.consumir(self.token_actual().tipo)
        
        tipo_token = self.consumir(['INT', 'STRING', 'DOUBLE', 'FLOAT', 'ID'])
        if not tipo_token: return None
        
        tipo_str = str(tipo_token.valor)
        if self.token_actual() and self.token_actual().tipo == 'COR_IZQ':
            self.consumir('COR_IZQ')
            self.consumir('COR_DER')
            tipo_str += "[]"
            
        # Podría ser solo un ID (como una variable en una expresión) o una declaración
        if self.token_actual() and self.token_actual().tipo == 'ID':
            nombre = self.consumir('ID')
            hijos = [Nodo(nombre.valor)]
            if self.token_actual() and self.token_actual().tipo == 'ASIGNAR':
                self.consumir('ASIGNAR')
                hijos.append(self.expresion())
            if self.token_actual() and self.token_actual().tipo == 'PUNTOYCOMA':
                self.consumir('PUNTOYCOMA')
            return Nodo(tipo_str, hijos)

        # Si es una asignación directa (x = 5)
        if self.token_actual() and self.token_actual().tipo == 'ASIGNAR':
            self.consumir('ASIGNAR')
            expr = self.expresion()
            if self.token_actual() and self.token_actual().tipo == 'PUNTOYCOMA':
                self.consumir('PUNTOYCOMA')
            return Nodo('=', [Nodo(tipo_str), expr])
            
        return Nodo(tipo_str)

    def expresion(self):
        return self.comparacion()

    def comparacion(self):
        nodo = self.aritmetica()
        if self.token_actual() and self.token_actual().tipo == 'COMPARAR':
            token = self.consumir('COMPARAR')
            nodo = Nodo(token.valor, [nodo, self.aritmetica()])
        return nodo

    def aritmetica(self):
        nodo = self.termino()
        while self.token_actual() and self.token_actual().tipo == 'OP' and self.token_actual().valor in ('+', '-'):
            token = self.consumir('OP')
            nodo = Nodo(token.valor, [nodo, self.termino()])
        return nodo

    def termino(self):
        nodo = self.factor()
        while self.token_actual() and self.token_actual().tipo == 'OP' and self.token_actual().valor in ('*', '/'):
            token = self.consumir('OP')
            nodo = Nodo(token.valor, [nodo, self.factor()])
        return nodo

    def factor(self):
        token = self.token_actual()
        if not token: return None
        if token.tipo == 'NUMERO':
            self.consumir('NUMERO')
            return Nodo(token.valor)
        elif token.tipo == 'CADENA':
            self.consumir('CADENA')
            return Nodo(token.valor)
        elif token.tipo == 'ID':
            self.consumir('ID')
            return Nodo(token.valor)
        elif token.tipo == 'PAR_IZQ':
            self.consumir('PAR_IZQ')
            nodo = self.expresion()
            self.consumir('PAR_DER')
            return nodo
        return None

class RequestCodigo(BaseModel):
    codigo: str

@app.post("/analizar")
async def analizar_codigo(req: RequestCodigo):
    try:
        lex = AnalizadorLexico(req.codigo)
        tokens = lex.tokenizar()
        sin = AnalizadorSintactico(tokens)
        ast = sin.analizar()
        return ast.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("static/index.html")

app.mount("/", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
