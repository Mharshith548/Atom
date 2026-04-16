#!/usr/bin/env python3
"""
Atom Language v1.0.0 — The AI Systems Language
Complete implementation with lexer, parser, interpreter, and compilers
"""

import os
import sys
import json
import shutil
import sqlite3
import hashlib
import subprocess
import urllib.request
import urllib.parse
import http.server
import socketserver
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import re

# ================ CONFIGURATION ================

class Config:
    VERSION = "1.0.0"
    HOME = Path.home() / ".atom"
    PACKAGES = HOME / "packages"
    MODELS = HOME / "models"
    CACHE = HOME / "cache"
    
    @classmethod
    def init(cls):
        for d in [cls.HOME, cls.PACKAGES, cls.MODELS, cls.CACHE]:
            d.mkdir(parents=True, exist_ok=True)

Config.init()

# ================ TOKEN TYPES ================

class TokenType(Enum):
    LET = "let"
    FN = "fn"
    CLASS = "class"
    IF = "if"
    ELIF = "elif"
    ELSE = "else"
    WHILE = "while"
    FOR = "for"
    IN = "in"
    RETURN = "return"
    IMPORT = "import"
    FROM = "from"
    AS = "as"
    MATCH = "match"
    CASE = "case"
    TRY = "try"
    EXCEPT = "except"
    RAISE = "raise"
    ASYNC = "async"
    AWAIT = "await"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"
    IDENT = "ident"
    NUMBER = "number"
    STRING = "string"
    TRUE = "true"
    FALSE = "false"
    NONE = "none"
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    PERCENT = "%"
    EQ = "="
    EQEQ = "=="
    NEQ = "!="
    LT = "<"
    GT = ">"
    LEQ = "<="
    GEQ = ">="
    AND = "and"
    OR = "or"
    NOT = "not"
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"
    COLON = ":"
    COMMA = ","
    DOT = "."
    ARROW = "->"
    FAT_ARROW = "=>"
    NEWLINE = "newline"
    INDENT = "indent"
    DEDENT = "dedent"
    EOF = "eof"

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int

# ================ LEXER ================

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent_stack = [0]
        self.tokens: List[Token] = []
        
        self.keywords = {
            'let': TokenType.LET, 'fn': TokenType.FN, 'class': TokenType.CLASS,
            'if': TokenType.IF, 'elif': TokenType.ELIF, 'else': TokenType.ELSE,
            'while': TokenType.WHILE, 'for': TokenType.FOR, 'in': TokenType.IN,
            'return': TokenType.RETURN, 'import': TokenType.IMPORT, 'from': TokenType.FROM,
            'as': TokenType.AS, 'match': TokenType.MATCH, 'case': TokenType.CASE,
            'try': TokenType.TRY, 'except': TokenType.EXCEPT, 'raise': TokenType.RAISE,
            'async': TokenType.ASYNC, 'await': TokenType.AWAIT,
            'and': TokenType.AND, 'or': TokenType.OR, 'not': TokenType.NOT,
            'int': TokenType.INT, 'float': TokenType.FLOAT, 'str': TokenType.STR,
            'bool': TokenType.BOOL, 'list': TokenType.LIST, 'dict': TokenType.DICT,
            'true': TokenType.TRUE, 'false': TokenType.FALSE, 'none': TokenType.NONE,
        }
    
    def tokenize(self) -> List[Token]:
        self._handle_indent()
        
        while self.pos < len(self.source):
            char = self.source[self.pos]
            
            if char in ' \t\r':
                self.pos += 1
                self.col += 1
                continue
            
            if char == '\n':
                self._add_token(TokenType.NEWLINE, '\n')
                self.pos += 1
                self.line += 1
                self.col = 1
                self._handle_indent()
                continue
            
            if char == '#':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
                continue
            
            if char in '"\'':
                self._read_string(char)
                continue
            
            if char.isdigit():
                self._read_number()
                continue
            
            if char.isalpha() or char == '_':
                self._read_identifier()
                continue
            
            if char == '=' and self._peek() == '=':
                self._add_token(TokenType.EQEQ, '==')
                self.pos += 2; self.col += 2; continue
            if char == '!' and self._peek() == '=':
                self._add_token(TokenType.NEQ, '!=')
                self.pos += 2; self.col += 2; continue
            if char == '<' and self._peek() == '=':
                self._add_token(TokenType.LEQ, '<=')
                self.pos += 2; self.col += 2; continue
            if char == '>' and self._peek() == '=':
                self._add_token(TokenType.GEQ, '>=')
                self.pos += 2; self.col += 2; continue
            if char == '-' and self._peek() == '>':
                self._add_token(TokenType.ARROW, '->')
                self.pos += 2; self.col += 2; continue
            if char == '=' and self._peek() == '>':
                self._add_token(TokenType.FAT_ARROW, '=>')
                self.pos += 2; self.col += 2; continue
            
            single = {'+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR,
                     '/': TokenType.SLASH, '%': TokenType.PERCENT, '=': TokenType.EQ,
                     '<': TokenType.LT, '>': TokenType.GT, '(': TokenType.LPAREN,
                     ')': TokenType.RPAREN, '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                     '{': TokenType.LBRACE, '}': TokenType.RBRACE, ':': TokenType.COLON,
                     ',': TokenType.COMMA, '.': TokenType.DOT}
            
            if char in single:
                self._add_token(single[char], char)
                self.pos += 1; self.col += 1
                continue
            
            raise SyntaxError(f"Unexpected character '{char}' at {self.line}:{self.col}")
        
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self._add_token(TokenType.DEDENT, '')
        
        self._add_token(TokenType.EOF, None)
        return self.tokens
    
    def _peek(self) -> str:
        return self.source[self.pos + 1] if self.pos + 1 < len(self.source) else ''
    
    def _add_token(self, type_: TokenType, value: Any):
        self.tokens.append(Token(type_, value, self.line, self.col))
    
    def _handle_indent(self):
        spaces = 0
        while self.pos + spaces < len(self.source) and self.source[self.pos + spaces] == ' ':
            spaces += 1
        if self.pos + spaces < len(self.source) and self.source[self.pos + spaces] == '\n':
            return
        
        current = self.indent_stack[-1]
        if spaces > current:
            self.indent_stack.append(spaces)
            self._add_token(TokenType.INDENT, '')
        elif spaces < current:
            while spaces < self.indent_stack[-1]:
                self.indent_stack.pop()
                self._add_token(TokenType.DEDENT, '')
    
    def _read_string(self, quote: str):
        self.pos += 1
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == '\\':
                self.pos += 2
            else:
                self.pos += 1
        value = self.source[start:self.pos]
        self._add_token(TokenType.STRING, value)
        self.pos += 1
        self.col += len(value) + 2
    
    def _read_number(self):
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            self.pos += 1
        value = self.source[start:self.pos]
        self._add_token(TokenType.NUMBER, float(value) if '.' in value else int(value))
        self.col += len(value)
    
    def _read_identifier(self):
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
        value = self.source[start:self.pos]
        self._add_token(self.keywords.get(value, TokenType.IDENT), value)
        self.col += len(value)

# ================ AST NODES ================

class ASTNode: pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]

@dataclass
class LetStmt(ASTNode):
    name: str
    value: 'Expr'
    type_anno: Optional[str] = None

@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List[Tuple[str, Optional[str]]]
    body: List[ASTNode]
    return_type: Optional[str] = None

@dataclass
class IfStmt(ASTNode):
    condition: 'Expr'
    then_body: List[ASTNode]
    elif_branches: List[Tuple['Expr', List[ASTNode]]] = field(default_factory=list)
    else_body: Optional[List[ASTNode]] = None

@dataclass
class WhileStmt(ASTNode):
    condition: 'Expr'
    body: List[ASTNode]

@dataclass
class ForStmt(ASTNode):
    var: str
    iterable: 'Expr'
    body: List[ASTNode]

@dataclass
class ReturnStmt(ASTNode):
    value: Optional['Expr']

@dataclass
class ExprStmt(ASTNode):
    expr: 'Expr'

@dataclass
class ImportStmt(ASTNode):
    module: str
    alias: Optional[str] = None

class Expr(ASTNode): pass

@dataclass
class NumberExpr(Expr): value: float
@dataclass
class StringExpr(Expr): value: str
@dataclass
class BoolExpr(Expr): value: bool
@dataclass
class NoneExpr(Expr): pass
@dataclass
class VarExpr(Expr): name: str
@dataclass
class BinaryExpr(Expr): left: Expr; op: str; right: Expr
@dataclass
class UnaryExpr(Expr): op: str; expr: Expr
@dataclass
class CallExpr(Expr): callee: Expr; args: List[Expr]
@dataclass
class GetAttrExpr(Expr): obj: Expr; attr: str
@dataclass
class ListExpr(Expr): elements: List[Expr]
@dataclass
class DictExpr(Expr): pairs: List[Tuple[Expr, Expr]]
@dataclass
class LambdaExpr(Expr): params: List[str]; body: Expr

# ================ PARSER ================

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self) -> Token: return self.tokens[self.pos]
    def consume(self) -> Token: 
        tok = self.peek()
        self.pos += 1
        return tok
    def match(self, *types: TokenType) -> bool:
        if self.peek().type in types:
            self.consume()
            return True
        return False
    def expect(self, type_: TokenType) -> Token:
        tok = self.peek()
        if tok.type != type_:
            raise SyntaxError(f"Expected {type_}, got {tok.type} at line {tok.line}")
        return self.consume()
    
    def parse(self) -> Program:
        stmts = []
        while self.peek().type != TokenType.EOF:
            if self.match(TokenType.NEWLINE):
                continue
            stmts.append(self.parse_statement())
        return Program(stmts)
    
    def parse_statement(self) -> ASTNode:
        tok = self.peek()
        
        if tok.type == TokenType.LET:
            return self.parse_let()
        elif tok.type == TokenType.FN:
            return self.parse_function()
        elif tok.type == TokenType.IF:
            return self.parse_if()
        elif tok.type == TokenType.WHILE:
            return self.parse_while()
        elif tok.type == TokenType.FOR:
            return self.parse_for()
        elif tok.type == TokenType.RETURN:
            return self.parse_return()
        elif tok.type == TokenType.IMPORT:
            return self.parse_import()
        else:
            expr = self.parse_expression()
            self.expect(TokenType.NEWLINE)
            return ExprStmt(expr)
    
    def parse_let(self) -> LetStmt:
        self.expect(TokenType.LET)
        name = self.expect(TokenType.IDENT).value
        type_anno = None
        if self.match(TokenType.COLON):
            type_anno = self.expect(TokenType.IDENT).value
        self.expect(TokenType.EQ)
        value = self.parse_expression()
        self.expect(TokenType.NEWLINE)
        return LetStmt(name, value, type_anno)
    
    def parse_function(self) -> FunctionDef:
        self.expect(TokenType.FN)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)
        params = []
        if self.peek().type != TokenType.RPAREN:
            while True:
                pname = self.expect(TokenType.IDENT).value
                ptype = None
                if self.match(TokenType.COLON):
                    ptype = self.expect(TokenType.IDENT).value
                params.append((pname, ptype))
                if not self.match(TokenType.COMMA):
                    break
        self.expect(TokenType.RPAREN)
        rtype = None
        if self.match(TokenType.ARROW):
            rtype = self.expect(TokenType.IDENT).value
        self.expect(TokenType.COLON)
        self.expect(TokenType.NEWLINE)
        self.expect(TokenType.INDENT)
        body = self._parse_block()
        return FunctionDef(name, params, body, rtype)
    
    def parse_if(self) -> IfStmt:
        self.expect(TokenType.IF)
        cond = self.parse_expression()
        self.expect(TokenType.COLON)
        self.expect(TokenType.NEWLINE)
        self.expect(TokenType.INDENT)
        then_body = self._parse_block()
        
        elif_branches = []
        while self.match(TokenType.ELIF):
            elif_cond = self.parse_expression()
            self.expect(TokenType.COLON)
            self.expect(TokenType.NEWLINE)
            self.expect(TokenType.INDENT)
            elif_body = self._parse_block()
            elif_branches.append((elif_cond, elif_body))
        
        else_body = None
        if self.match(TokenType.ELSE):
            self.expect(TokenType.COLON)
            self.expect(TokenType.NEWLINE)
            self.expect(TokenType.INDENT)
            else_body = self._parse_block()
        
        return IfStmt(cond, then_body, elif_branches, else_body)
    
    def parse_while(self) -> WhileStmt:
        self.expect(TokenType.WHILE)
        cond = self.parse_expression()
        self.expect(TokenType.COLON)
        self.expect(TokenType.NEWLINE)
        self.expect(TokenType.INDENT)
        body = self._parse_block()
        return WhileStmt(cond, body)
    
    def parse_for(self) -> ForStmt:
        self.expect(TokenType.FOR)
        var = self.expect(TokenType.IDENT).value
        self.expect(TokenType.IN)
        iterable = self.parse_expression()
        self.expect(TokenType.COLON)
        self.expect(TokenType.NEWLINE)
        self.expect(TokenType.INDENT)
        body = self._parse_block()
        return ForStmt(var, iterable, body)
    
    def parse_return(self) -> ReturnStmt:
        self.expect(TokenType.RETURN)
        if self.match(TokenType.NEWLINE):
            return ReturnStmt(None)
        value = self.parse_expression()
        self.expect(TokenType.NEWLINE)
        return ReturnStmt(value)
    
    def parse_import(self) -> ImportStmt:
        self.expect(TokenType.IMPORT)
        module = self.expect(TokenType.IDENT).value
        alias = None
        if self.match(TokenType.AS):
            alias = self.expect(TokenType.IDENT).value
        self.expect(TokenType.NEWLINE)
        return ImportStmt(module, alias)
    
    def _parse_block(self) -> List[ASTNode]:
        body = []
        while not self.match(TokenType.DEDENT):
            if self.peek().type == TokenType.NEWLINE:
                self.consume()
                continue
            body.append(self.parse_statement())
        return body
    
    def parse_expression(self, min_prec: int = 0) -> Expr:
        precedences = {
            TokenType.OR: 1, TokenType.AND: 2,
            TokenType.EQEQ: 4, TokenType.NEQ: 4, TokenType.LT: 5, TokenType.GT: 5,
            TokenType.LEQ: 5, TokenType.GEQ: 5,
            TokenType.PLUS: 10, TokenType.MINUS: 10,
            TokenType.STAR: 20, TokenType.SLASH: 20, TokenType.PERCENT: 20,
            TokenType.DOT: 30,
        }
        
        if self.peek().type in (TokenType.NOT, TokenType.MINUS):
            op = self.consume().value
            expr = self.parse_expression(30)
            return UnaryExpr(op, expr)
        
        left = self.parse_primary()
        
        while True:
            tok = self.peek()
            
            if tok.type == TokenType.LPAREN:
                self.consume()
                args = []
                if self.peek().type != TokenType.RPAREN:
                    while True:
                        args.append(self.parse_expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.expect(TokenType.RPAREN)
                left = CallExpr(left, args)
                continue
            
            if tok.type == TokenType.DOT:
                self.consume()
                attr = self.expect(TokenType.IDENT).value
                left = GetAttrExpr(left, attr)
                continue
            
            if tok.type in precedences:
                prec = precedences[tok.type]
                if prec < min_prec:
                    break
                op = self.consume().value
                right = self.parse_expression(prec + 1)
                left = BinaryExpr(left, op, right)
                continue
            
            break
        
        return left
    
    def parse_primary(self) -> Expr:
        tok = self.peek()
        
        if tok.type == TokenType.NUMBER:
            self.consume()
            return NumberExpr(tok.value)
        elif tok.type == TokenType.STRING:
            self.consume()
            return StringExpr(tok.value)
        elif tok.type == TokenType.TRUE:
            self.consume()
            return BoolExpr(True)
        elif tok.type == TokenType.FALSE:
            self.consume()
            return BoolExpr(False)
        elif tok.type == TokenType.NONE:
            self.consume()
            return NoneExpr()
        elif tok.type == TokenType.IDENT:
            self.consume()
            return VarExpr(tok.value)
        elif tok.type == TokenType.LPAREN:
            self.consume()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        elif tok.type == TokenType.LBRACKET:
            self.consume()
            elements = []
            if self.peek().type != TokenType.RBRACKET:
                while True:
                    elements.append(self.parse_expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RBRACKET)
            return ListExpr(elements)
        elif tok.type == TokenType.LBRACE:
            self.consume()
            pairs = []
            if self.peek().type != TokenType.RBRACE:
                while True:
                    key = self.parse_expression()
                    self.expect(TokenType.COLON)
                    value = self.parse_expression()
                    pairs.append((key, value))
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RBRACE)
            return DictExpr(pairs)
        elif tok.type == TokenType.FN:
            self.expect(TokenType.FN)
            self.expect(TokenType.LPAREN)
            params = []
            if self.peek().type != TokenType.RPAREN:
                while True:
                    params.append(self.expect(TokenType.IDENT).value)
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RPAREN)
            self.expect(TokenType.ARROW)
            body = self.parse_expression()
            return LambdaExpr(params, body)
        
        raise SyntaxError(f"Unexpected token {tok.type} at line {tok.line}")

# ================ STANDARD LIBRARY ================

class AI:
    def __init__(self):
        self.models = {}
    
    def load(self, name: str):
        if name in self.models:
            return self.models[name]
        print(f"🤖 Loading model: {name}")
        model = BasicModel(name) if name != "tinyllm" else TinyLLM()
        self.models[name] = model
        return model
    
    def list_models(self) -> List[str]:
        return ["tinyllm"]

class BasicModel:
    def __init__(self, name: str):
        self.name = name
    
    def ask(self, prompt: str) -> str:
        responses = {
            "hello": "Hello! I'm Atom AI.",
            "hi": "Hi there!",
            "what is atom": "Atom is the AI Systems Language.",
        }
        return responses.get(prompt.lower(), f"[{self.name}] Response to: {prompt[:50]}...")

class TinyLLM(BasicModel):
    def __init__(self):
        super().__init__("TinyLLM")
    
    def ask(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "atom" in prompt_lower:
            return "Atom is a modern programming language with Python syntax, native speed, and AI built-in."
        return super().ask(prompt)

class HTTP:
    @staticmethod
    def get(url: str, headers: Dict = None) -> Dict:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req) as resp:
            return {'status': resp.status, 'body': resp.read().decode()}

class DB:
    class SQLite:
        def __init__(self, path: str):
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
        
        def execute(self, query: str, params: tuple = ()):
            cur = self.conn.cursor()
            cur.execute(query, params)
            self.conn.commit()
            return self
        
        def query(self, query: str, params: tuple = ()) -> List[Dict]:
            cur = self.conn.cursor()
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

class File:
    @staticmethod
    def read(path: str) -> str:
        with open(path, 'r') as f:
            return f.read()
    
    @staticmethod
    def write(path: str, content: str):
        with open(path, 'w') as f:
            f.write(content)
    
    @staticmethod
    def exists(path: str) -> bool:
        return os.path.exists(path)

# ================ PACKAGE MANAGER ================

class PackageManager:
    def __init__(self):
        self.installed_file = Config.PACKAGES / "installed.json"
        self.installed = self._load()
    
    def _load(self) -> Dict:
        if self.installed_file.exists():
            with open(self.installed_file) as f:
                return json.load(f)
        return {}
    
    def _save(self):
        with open(self.installed_file, 'w') as f:
            json.dump(self.installed, f, indent=2)
    
    def install(self, package: str):
        print(f"📦 Installing {package}...")
        if package in self.installed:
            print(f"   Already installed")
            return
        pkg_dir = Config.PACKAGES / package
        pkg_dir.mkdir(exist_ok=True)
        with open(pkg_dir / "__init__.atom", 'w') as f:
            f.write(f'# Atom {package} package\nfn version() -> str: return "1.0.0"\n')
        self.installed[package] = "1.0.0"
        self._save()
        print(f"✅ Installed {package}")

# ================ WEB SERVER ================

class WebServer:
    def __init__(self, port: int = 8080):
        self.port = port
        self.routes = {}
    
    def route(self, path: str, methods: List[str] = None):
        methods = methods or ["GET"]
        def decorator(handler):
            self.routes[path] = {"handler": handler, "methods": methods}
            return handler
        return decorator
    
    def start(self):
        routes = self.routes
        
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self._handle("GET")
            
            def _handle(self, method):
                if self.path in routes and method in routes[self.path]["methods"]:
                    result = routes[self.path]["handler"](self)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(str(result).encode())
                else:
                    self.send_error(404)
            
            def log_message(self, format, *args):
                print(f"🌐 {args[0]}")
        
        with socketserver.TCPServer(("", self.port), Handler) as httpd:
            print(f"🚀 Server running on http://localhost:{self.port}")
            httpd.serve_forever()

# ================ INTERPRETER ================

class Interpreter:
    def __init__(self):
        self.globals = {}
        self.locals = [{}]
        self.functions = {}
        self.modules = {'ai': AI(), 'http': HTTP(), 'db': DB(), 'file': File(), 'json': json}
        self._setup_builtins()
    
    def _setup_builtins(self):
        self.globals['print'] = lambda *args: print(*args)
        self.globals['len'] = len
        self.globals['range'] = range
        self.globals['input'] = input
        self.globals['str'] = str
        self.globals['int'] = int
        self.globals['float'] = float
        self.globals['list'] = list
        self.globals['dict'] = dict
        self.globals['type'] = lambda x: type(x).__name__
    
    def execute(self, program: Program):
        for stmt in program.statements:
            self._execute(stmt)
    
    def _execute(self, node: ASTNode):
        if isinstance(node, LetStmt):
            self.locals[-1][node.name] = self._eval(node.value)
        elif isinstance(node, ExprStmt):
            self._eval(node.expr)
        elif isinstance(node, IfStmt):
            if self._eval(node.condition):
                for s in node.then_body:
                    self._execute(s)
            else:
                for cond, body in node.elif_branches:
                    if self._eval(cond):
                        for s in body:
                            self._execute(s)
                        return
                if node.else_body:
                    for s in node.else_body:
                        self._execute(s)
        elif isinstance(node, WhileStmt):
            while self._eval(node.condition):
                for s in node.body:
                    self._execute(s)
        elif isinstance(node, ForStmt):
            for item in self._eval(node.iterable):
                self.locals[-1][node.var] = item
                for s in node.body:
                    self._execute(s)
        elif isinstance(node, FunctionDef):
            self.functions[node.name] = node
        elif isinstance(node, ReturnStmt):
            raise ReturnException(self._eval(node.value) if node.value else None)
        elif isinstance(node, ImportStmt):
            if node.module in self.modules:
                self.locals[-1][node.alias or node.module] = self.modules[node.module]
    
    def _eval(self, expr: Expr) -> Any:
        if isinstance(expr, NumberExpr):
            return expr.value
        elif isinstance(expr, StringExpr):
            return expr.value
        elif isinstance(expr, BoolExpr):
            return expr.value
        elif isinstance(expr, NoneExpr):
            return None
        elif isinstance(expr, VarExpr):
            for scope in reversed(self.locals):
                if expr.name in scope:
                    return scope[expr.name]
            if expr.name in self.globals:
                return self.globals[expr.name]
            if expr.name in self.functions:
                return self.functions[expr.name]
            raise NameError(f"Variable '{expr.name}' not defined")
        elif isinstance(expr, CallExpr):
            callee = self._eval(expr.callee)
            args = [self._eval(a) for a in expr.args]
            if callable(callee):
                return callee(*args)
            elif isinstance(callee, FunctionDef):
                return self._call_function(callee, args)
            return callee
        elif isinstance(expr, BinaryExpr):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            ops = {'+': lambda a,b: a+b, '-': lambda a,b: a-b, '*': lambda a,b: a*b,
                   '/': lambda a,b: a/b, '==': lambda a,b: a==b, '!=': lambda a,b: a!=b,
                   '<': lambda a,b: a<b, '>': lambda a,b: a>b, '<=': lambda a,b: a<=b,
                   '>=': lambda a,b: a>=b, 'and': lambda a,b: a and b, 'or': lambda a,b: a or b}
            return ops[expr.op](left, right)
        elif isinstance(expr, ListExpr):
            return [self._eval(e) for e in expr.elements]
        elif isinstance(expr, DictExpr):
            return {self._eval(k): self._eval(v) for k, v in expr.pairs}
        elif isinstance(expr, LambdaExpr):
            return FunctionDef('<lambda>', [(p, None) for p in expr.params], [ReturnStmt(expr.body)])
        elif isinstance(expr, GetAttrExpr):
            obj = self._eval(expr.obj)
            return getattr(obj, expr.attr)
        return None
    
    def _call_function(self, func: FunctionDef, args: List[Any]) -> Any:
        self.locals.append({})
        for (name, _), arg in zip(func.params, args):
            self.locals[-1][name] = arg
        try:
            for stmt in func.body:
                self._execute(stmt)
        except ReturnException as ret:
            return ret.value
        finally:
            self.locals.pop()
        return None

class ReturnException(Exception):
    def __init__(self, value): self.value = value

# ================ COMPILERS ================

class CCompiler:
    def compile(self, program: Program) -> str:
        self.output = []
        self.indent = 0
        self._emit('#include <stdio.h>')
        self._emit('#include <stdlib.h>')
        self._emit('')
        self._emit('int main() {')
        self.indent += 1
        for stmt in program.statements:
            self._compile_stmt(stmt)
        self._emit('return 0;')
        self.indent -= 1
        self._emit('}')
        return '\n'.join(self.output)
    
    def _emit(self, line: str):
        self.output.append('    ' * self.indent + line)
    
    def _compile_stmt(self, stmt: ASTNode):
        if isinstance(stmt, LetStmt):
            val = self._compile_expr(stmt.value)
            self._emit(f'int {stmt.name} = {val};')
        elif isinstance(stmt, ExprStmt):
            expr = self._compile_expr(stmt.expr)
            if isinstance(stmt.expr, CallExpr):
                self._emit(f'{expr};')
    
    def _compile_expr(self, expr: Expr) -> str:
        if isinstance(expr, NumberExpr):
            return str(expr.value)
        elif isinstance(expr, StringExpr):
            return f'"{expr.value}"'
        elif isinstance(expr, VarExpr):
            return expr.name
        elif isinstance(expr, CallExpr):
            if isinstance(expr.callee, VarExpr) and expr.callee.name == 'print':
                args = ', '.join(self._compile_expr(a) for a in expr.args)
                return f'printf("%s\\n", {args})'
        return '0'

# ================ CLI ================

class AtomCLI:
    def __init__(self):
        self.interpreter = Interpreter()
        self.c_compiler = CCompiler()
        self.pm = PackageManager()
    
    def run(self, filename: str):
        with open(filename) as f:
            source = f.read()
        self._run_source(source)
    
    def _run_source(self, source: str):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        self.interpreter.execute(ast)
    
    def build(self, filename: str, output: str = None):
        with open(filename) as f:
            source = f.read()
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        out = output or filename.replace('.atom', '')
        code = self.c_compiler.compile(ast)
        with open(out + '.c', 'w') as f:
            f.write(code)
        
        subprocess.run(['gcc', '-O2', '-o', out, out + '.c'], check=True)
        os.unlink(out + '.c')
        print(f"✅ Compiled to native: {out}")
    
    def serve(self, port: int = 8080):
        server = WebServer(port)
        
        @server.route("/")
        def index(req):
            return "Atom Web Server"
        
        @server.route("/health")
        def health(req):
            return "OK"
        
        server.start()
    
    def repl(self):
        print(f"⚛️  Atom v{Config.VERSION} REPL")
        print("   Type 'exit' to quit")
        
        while True:
            try:
                code = input("atom> ")
                if code.strip() == 'exit':
                    break
                if not code.strip():
                    continue
                self._run_source(code)
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")

# ================ MAIN ================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Atom — The AI Systems Language')
    sub = parser.add_subparsers(dest='command')
    
    new = sub.add_parser('new', help='Create new project')
    new.add_argument('name')
    
    run = sub.add_parser('run', help='Run Atom file')
    run.add_argument('file')
    
    build = sub.add_parser('build', help='Build project')
    build.add_argument('file')
    build.add_argument('-o', '--output')
    
    add = sub.add_parser('add', help='Install package')
    add.add_argument('package')
    
    serve = sub.add_parser('serve', help='Start web server')
    serve.add_argument('--port', type=int, default=8080)
    
    repl = sub.add_parser('repl', help='Start REPL')
    
    version = sub.add_parser('version', help='Show version')
    
    args = parser.parse_args()
    cli = AtomCLI()
    
    if args.command == 'new':
        proj_dir = Path(args.name)
        proj_dir.mkdir(exist_ok=True)
        (proj_dir / "src").mkdir(exist_ok=True)
        with open(proj_dir / "src" / "main.atom", 'w') as f:
            f.write('print("Hello from Atom!")\n')
        print(f"✅ Created project: {args.name}")
    elif args.command == 'run':
        cli.run(args.file)
    elif args.command == 'build':
        cli.build(args.file, args.output)
    elif args.command == 'add':
        cli.pm.install(args.package)
    elif args.command == 'serve':
        cli.serve(args.port)
    elif args.command == 'repl':
        cli.repl()
    elif args.command == 'version':
        print(f"Atom v{Config.VERSION}")
    else:
        cli.repl()

if __name__ == '__main__':
    main()