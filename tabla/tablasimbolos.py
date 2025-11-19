from dataclasses import dataclass
from typing import List, Optional, Any, Dict, Tuple
import subprocess
import shutil
import sys

class DotParser:
    
    def __init__(self, content: str):
        self.content = content
        self.pos = 0
        self.length = len(content)
        self.nodes = {}
        self.edges = []
    
    def parse(self):
        while self.pos < self.length:
            self.skip_whitespace()
            if self.pos >= self.length:
                break
            
            if self.peek() == 'n' and self.peek_ahead_is_digit():
                self.parse_node()
            else:
                self.advance()
        
        return self.nodes, self.edges
    
    def peek(self, offset=0):
        pos = self.pos + offset
        if pos < self.length:
            return self.content[pos]
        return None
    
    def peek_ahead_is_digit(self):
        c = self.peek(1)
        return c and c.isdigit()
    
    def advance(self):
        if self.pos < self.length:
            c = self.content[self.pos]
            self.pos += 1
            return c
        return None
    
    def skip_whitespace(self):
        while self.pos < self.length and self.content[self.pos] in ' \t\n\r':
            self.pos += 1
    
    def parse_node(self):
        node_id = []
        while self.pos < self.length and self.content[self.pos].isalnum():
            node_id.append(self.advance())
        node_id = ''.join(node_id)
        
        self.skip_whitespace()
        
        if self.peek() == '-' and self.peek(1) == '>':
            self.advance()
            self.advance()
            self.skip_whitespace()
            
            to_id = []
            while self.pos < self.length and self.content[self.pos].isalnum():
                to_id.append(self.advance())
            to_id = ''.join(to_id)
            
            if node_id and to_id:
                self.edges.append((node_id, to_id))
            return
        
        if self.peek() == '[':
            self.advance()
            self.skip_whitespace()
            
            if self.find_text('label'):
                self.skip_whitespace()
                if self.peek() == '=':
                    self.advance()
                    self.skip_whitespace()
                    
                    if self.peek() == '"':
                        self.advance()
                        label = self.read_label()
                        
                        if node_id:
                            self.nodes[node_id] = label
    
    def find_text(self, text: str):
        start = self.pos
        for char in text:
            if self.pos >= self.length or self.content[self.pos] != char:
                self.pos = start
                return False
            self.pos += 1
        return True
    
    def read_label(self):
        label = []
        while self.pos < self.length:
            c = self.peek()
            if c == '"':
                self.advance()
                break
            elif c == '\\' and self.peek(1) == 'n':
                self.advance()
                self.advance()
                label.append('\n')
            else:
                label.append(self.advance())
        return ''.join(label)


def visualize_ast_from_dot(dot_file="ast.dot"):
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("tkinter no esta disponible en tu instalacion de Python")
        return False
    
    class DotASTVisualizer:
        def __init__(self, root, dot_file):
            self.root = root
            self.root.title("Visualizador de AST")
            self.root.geometry("1600x900")
            self.root.configure(bg="#2C3E50")
            
            self.nodes = {}
            self.edges = []
            self.children_map = {}
            self.root_node = None
            
            if not self.load_dot_file(dot_file):
                messagebox.showerror("Error", f"No se pudo cargar {dot_file}")
                root.destroy()
                return
            
            self.build_tree()
            self.create_ui()
            self.draw_tree()
        
        def load_dot_file(self, filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                parser = DotParser(content)
                self.nodes, self.edges = parser.parse()
                
                print(f"Cargado: {len(self.nodes)} nodos, {len(self.edges)} aristas")
                return len(self.nodes) > 0
            except FileNotFoundError:
                print(f"Archivo {filename} no encontrado")
                return False
            except Exception as e:
                print(f"Error: {e}")
                return False
        
        def build_tree(self):
            targets = {edge[1] for edge in self.edges}
            sources = {edge[0] for edge in self.edges}
            roots = sources - targets
            
            if roots:
                self.root_node = list(roots)[0]
            elif self.nodes:
                self.root_node = list(self.nodes.keys())[0]
            
            self.children_map = {}
            for parent, child in self.edges:
                if parent not in self.children_map:
                    self.children_map[parent] = []
                self.children_map[parent].append(child)
        
        def create_ui(self):
            main_frame = tk.Frame(self.root, bg="#2C3E50")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            title_frame = tk.Frame(main_frame, bg="#34495E")
            title_frame.pack(fill=tk.X)
            
            title = tk.Label(
                title_frame,
                text="ARBOL DE SINTAXIS ABSTRACTA (AST)",
                bg="#34495E", fg="white",
                font=("Arial", 16, "bold"), pady=12
            )
            title.pack(side=tk.LEFT, padx=20)
            
            stats = tk.Label(
                title_frame,
                text=f"{len(self.nodes)} nodos | {len(self.edges)} conexiones",
                bg="#34495E", fg="#ECF0F1",
                font=("Arial", 10), pady=12
            )
            stats.pack(side=tk.RIGHT, padx=20)
            
            canvas_frame = tk.Frame(main_frame, bg="#2C3E50")
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
            h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
            v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
            
            h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
            v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
            
            toolbar = tk.Frame(main_frame, bg="#34495E", height=40)
            toolbar.pack(fill=tk.X, side=tk.BOTTOM)
            
            instructions = tk.Label(
                toolbar,
                text="Rueda: Zoom | Click medio + arrastrar: Mover | Hover: Info",
                bg="#34495E", fg="#ECF0F1",
                font=("Arial", 9), pady=8
            )
            instructions.pack(side=tk.LEFT, padx=20)
            
            reset_btn = tk.Button(
                toolbar, text="Resetear",
                command=self.reset_view,
                bg="#3498DB", fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT, padx=15, pady=5
            )
            reset_btn.pack(side=tk.RIGHT, padx=20)
            
            self.canvas.bind("<MouseWheel>", self.zoom)
            self.canvas.bind("<Button-4>", self.zoom)
            self.canvas.bind("<Button-5>", self.zoom)
            self.canvas.bind("<ButtonPress-2>", self.start_pan)
            self.canvas.bind("<B2-Motion>", self.pan)
            
            self.scale_factor = 1.0
        
        def get_node_color(self, label):
            label_lower = label.lower()
            colors = {
                'program': '#3498DB', 'function': '#27AE60', 'func': '#27AE60',
                'procedure': '#27AE60', 'proc': '#27AE60', 'const': '#9B59B6',
                'var': '#7F8C8D', 'array': '#E67E22', 'type': '#E67E22',
                'assign': '#16A085', 'if': '#F39C12', 'while': '#F39C12',
                'return': '#E74C3C', 'binop': '#1ABC9C', 'number': '#95A5A6',
                'call': '#2ECC71', 'then': '#F39C12', 'else': '#E67E22',
            }
            
            for key, color in colors.items():
                if key in label_lower:
                    return color
            return '#BDC3C7'
        
        def calculate_tree_dimensions(self, node_id, level=0):
            if not hasattr(self, 'max_level'):
                self.max_level = 0
                self.level_widths = {}
            
            self.max_level = max(self.max_level, level)
            self.level_widths[level] = self.level_widths.get(level, 0) + 1
            
            children = self.children_map.get(node_id, [])
            for child in children:
                self.calculate_tree_dimensions(child, level + 1)
        
        def draw_tree(self):
            if not self.root_node:
                return
            
            self.node_w = 100
            self.node_h = 50
            self.level_h = 120
            self.h_spacing = 40
            
            self.calculate_tree_dimensions(self.root_node)
            max_width = max(self.level_widths.values())
            tree_width = max(1600, max_width * (self.node_w + self.h_spacing))
            
            self.draw_node(self.root_node, tree_width // 2, 60, tree_width // 2)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.xview_moveto(0.3)
        
        def draw_node(self, node_id, x, y, width, level=0):
            if node_id not in self.nodes:
                return
            
            label = self.nodes[node_id]
            children = self.children_map.get(node_id, [])
            
            if children:
                total_width = len(children) * (self.node_w + self.h_spacing)
                start_x = x - total_width // 2
                child_spacing = total_width / max(len(children), 1)
                
                for i, child_id in enumerate(children):
                    child_x = start_x + i * child_spacing + child_spacing // 2
                    child_y = y + self.level_h
                    
                    self.canvas.create_line(
                        x, y + self.node_h // 2,
                        child_x, child_y - self.node_h // 2,
                        fill="#95A5A6", width=2,
                        arrow=tk.LAST, arrowshape=(10, 12, 5),
                        tags="edge"
                    )
                    
                    self.draw_node(child_id, child_x, child_y, width // 2, level + 1)
            
            x1 = x - self.node_w // 2
            y1 = y - self.node_h // 2
            x2 = x + self.node_w // 2
            y2 = y + self.node_h // 2
            
            color = self.get_node_color(label)
            
            self.canvas.create_rectangle(
                x1 + 3, y1 + 3, x2 + 3, y2 + 3,
                fill="#D5D8DC", outline="", tags="shadow"
            )
            
            rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color, outline="#2C3E50", width=2,
                tags=("node", node_id)
            )
            
            text = self.canvas.create_text(
                x, y, text=label,
                font=("Arial", 9, "bold"),
                fill="white", width=self.node_w - 10,
                tags=("text", node_id)
            )
            
            self.canvas.tag_bind(rect, "<Enter>", 
                lambda e, nid=node_id, lbl=label: self.show_tooltip(e, nid, lbl))
            self.canvas.tag_bind(rect, "<Leave>", self.hide_tooltip)
            self.canvas.tag_bind(text, "<Enter>", 
                lambda e, nid=node_id, lbl=label: self.show_tooltip(e, nid, lbl))
            self.canvas.tag_bind(text, "<Leave>", self.hide_tooltip)
        
        def show_tooltip(self, event, node_id, label):
            info = f"ID: {node_id}\nLabel: {label}\n"
            children = self.children_map.get(node_id, [])
            if children:
                info += f"Hijos: {len(children)}"
            
            self.tooltip = tk.Toplevel(self.root)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
            
            frame = tk.Frame(self.tooltip, bg="#2C3E50", relief=tk.SOLID, borderwidth=2)
            frame.pack()
            
            tk.Label(
                frame, text=info,
                bg="#2C3E50", fg="white",
                font=("Arial", 9),
                padx=12, pady=8, justify=tk.LEFT
            ).pack()
        
        def hide_tooltip(self, event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        
        def zoom(self, event):
            if event.num == 4 or event.delta > 0:
                scale = 1.1
            else:
                scale = 0.9
            
            self.canvas.scale("all", event.x, event.y, scale, scale)
            self.scale_factor *= scale
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        def start_pan(self, event):
            self.canvas.scan_mark(event.x, event.y)
        
        def pan(self, event):
            self.canvas.scan_dragto(event.x, event.y, gain=1)
        
        def reset_view(self):
            self.canvas.delete("all")
            self.scale_factor = 1.0
            self.draw_tree()
    
    try:
        root = tk.Tk()
        app = DotASTVisualizer(root, dot_file)
        root.mainloop()
        return True
    except Exception as e:
        print(f"Error al visualizar: {e}")
        return False


@dataclass
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int
    def __repr__(self):
        return f"Token({self.tipo}, '{self.lexema}', {self.linea}, {self.columna})"

KEYWORDS = {
    "if":"IF","else":"ELSE","while":"WHILE","return":"RETURN",
    "function":"FUNCTION","procedure":"PROCEDURE","const":"CONST",
    "array":"ARRAY","type":"TYPE"
}

class ASTNode:
    _id_counter = 0
    def __init__(self):
        self.id = ASTNode._id_counter
        ASTNode._id_counter += 1
    def accept(self, visitor):
        return getattr(visitor, 'visit_' + self.__class__.__name__)(self)

class Program(ASTNode):
    def __init__(self, decls: List['Decl']):
        super().__init__()
        self.decls = decls

class Decl(ASTNode):
    pass

class Stmt(ASTNode):
    pass

class Expr(ASTNode):
    pass

class ConstDecl(Decl):
    def __init__(self, name: str, value: Expr):
        super().__init__()
        self.name = name
        self.value = value

class VarDecl(Decl):
    def __init__(self, name: str, typ: Optional[str]=None):
        super().__init__()
        self.name = name
        self.typ = typ

class ArrayDecl(Decl):
    def __init__(self, name: str, size: int):
        super().__init__()
        self.name = name
        self.size = size

class TypeDecl(Decl):
    def __init__(self, name: str, fields: List[Tuple[str, Optional[str]]]):
        super().__init__()
        self.name = name
        self.fields = fields

class FunctionDecl(Decl):
    def __init__(self, name: str, params: List[Tuple[str,str]], ret_type: Optional[str], body: List[Stmt]):
        super().__init__()
        self.name = name
        self.params = params
        self.ret_type = ret_type
        self.body = body

class ProcedureDecl(Decl):
    def __init__(self, name: str, params: List[Tuple[str,str]], body: List[Stmt]):
        super().__init__()
        self.name = name
        self.params = params
        self.body = body

class Assign(Stmt):
    def __init__(self, target: Expr, expr: Expr):
        super().__init__()
        self.target = target
        self.expr = expr

class If(Stmt):
    def __init__(self, cond: Expr, then_block: List[Stmt], else_block: Optional[List[Stmt]]):
        super().__init__()
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block

class While(Stmt):
    def __init__(self, cond: Expr, body: List[Stmt]):
        super().__init__()
        self.cond = cond
        self.body = body

class Return(Stmt):
    def __init__(self, expr: Optional[Expr]):
        super().__init__()
        self.expr = expr

class ExprStmt(Stmt):
    def __init__(self, expr: Expr):
        super().__init__()
        self.expr = expr

class BinaryOp(Expr):
    def __init__(self, left: Expr, op: str, right: Expr):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right

class Number(Expr):
    def __init__(self, value: float):
        super().__init__()
        self.value = value

class Var(Expr):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

class Call(Expr):
    def __init__(self, name: str, args: List[Expr]):
        super().__init__()
        self.name = name
        self.args = args

class ArrayAccess(Expr):
    def __init__(self, name: str, index: Expr):
        super().__init__()
        self.name = name
        self.index = index

class FieldAccess(Expr):
    def __init__(self, expr: Expr, field: str):
        super().__init__()
        self.expr = expr
        self.field = field

@dataclass
class SymbolEntry:
    name: str
    sym_type: str
    data_type: Optional[str] = None
    scope_level: int = 0
    address: Optional[int] = None
    size: Optional[int] = None
    params: Optional[List[str]] = None
    return_type: Optional[str] = None
    label: Optional[str] = None
    extra: Dict[str, Any] = None

class SymbolTable:
    def __init__(self):
        self.scopes: List[Dict[str, SymbolEntry]] = [{}]
        self.address_counter = 0

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def current_level(self)->int:
        return len(self.scopes)-1

    def add(self, entry: SymbolEntry):
        if entry.name in self.scopes[-1]:
            print(f"Warning: redeclaracion de '{entry.name}' en scope {self.current_level()}")
        if entry.sym_type in ('var','const','param','array') and entry.address is None:
            entry.address = self.address_counter
            entry.size = entry.size if entry.size is not None else 8
            self.address_counter += entry.size
        entry.scope_level = self.current_level()
        self.scopes[-1][entry.name] = entry

    def lookup(self, name: str)->Optional[SymbolEntry]:
        for s in reversed(self.scopes):
            if name in s:
                return s[name]
        return None

    def __repr__(self):
        lines = []
        lines.append("======= Tabla de simbolos =======")
        lines.append("Name | kind | type | addr | size | params | return | label")
        lines.append("-"*90)
        for i, scope in enumerate(self.scopes):
            for e in scope.values():
                lines.append(f"{e.name} | {e.sym_type} | {e.data_type} | {e.address} | {e.size} | {e.params} | {e.return_type} | {e.label}")
        lines.append("="*90)
        return "\n".join(lines)
    # PARTE 2: Lexer y Parser

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.len = len(text)
        self.line = 1
        self.col = 1

    def _peek(self)->Optional[str]:
        if self.pos < self.len:
            return self.text[self.pos]
        return None

    def _advance(self)->Optional[str]:
        c = self._peek()
        if c is None:
            return None
        self.pos += 1
        if c == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def tokenize(self)->List[Token]:
        tokens: List[Token] = []
        while True:
            c = self._peek()
            if c is None:
                break
            if c in (' ', '\t', '\r'):
                self._advance(); continue
            if c == '\n':
                self._advance(); continue
            start_line, start_col = self.line, self.col

            if c == '=':
                self._advance()
                if self._peek() == '=':
                    self._advance(); tokens.append(Token('OP','==',start_line,start_col)); continue
                else:
                    tokens.append(Token('ASSIGN','=',start_line,start_col)); continue
            if c == '!':
                self._advance()
                if self._peek() == '=':
                    self._advance(); tokens.append(Token('OP','!=',start_line,start_col)); continue
                raise Exception(f"Caracter inesperado '!' en linea {start_line} col {start_col}")
            if c == '<':
                self._advance()
                if self._peek() == '=':
                    self._advance(); tokens.append(Token('OP','<=',start_line,start_col)); continue
                tokens.append(Token('OP','<',start_line,start_col)); continue
            if c == '>':
                self._advance()
                if self._peek() == '=':
                    self._advance(); tokens.append(Token('OP','>=',start_line,start_col)); continue
                tokens.append(Token('OP','>',start_line,start_col)); continue

            if c.isdigit():
                num = ''
                while self._peek() is not None and self._peek().isdigit():
                    num += self._advance()
                if self._peek() == '.':
                    num += self._advance()
                    while self._peek() is not None and self._peek().isdigit():
                        num += self._advance()
                tokens.append(Token('NUMBER', num, start_line, start_col))
                continue

            if c.isalpha() or c == '_':
                s = ''
                while self._peek() is not None and (self._peek().isalnum() or self._peek()=='_'):
                    s += self._advance()
                if s in KEYWORDS:
                    tokens.append(Token(KEYWORDS[s], s, start_line, start_col))
                else:
                    tokens.append(Token('ID', s, start_line, start_col))
                continue

            mapping = {
                '+':'OP','-':'OP','*':'OP','/':'OP',
                '(':'LPAREN',')':'RPAREN',',':'COMMA',';':'SEMICOLON',
                '{':'LBRACE','}':'RBRACE','[':'LBRACK',']':'RBRACK',':':'COLON','.':'DOT'
            }
            if c in mapping:
                tok_type = mapping[c]
                tokens.append(Token(tok_type, self._advance(), start_line, start_col))
                continue

            bad = self._advance()
            raise Exception(f"Caracter inesperado '{bad}' en linea {start_line} columna {start_col}")

        tokens.append(Token('EOF','',self.line,self.col))
        return tokens


class ParserError(Exception): pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self)->Token:
        return self.tokens[self.pos]

    def eat(self, tipo: str)->Token:
        cur = self.current()
        if cur.tipo == tipo:
            self.pos += 1
            return cur
        raise ParserError(f"Esperaba {tipo} pero vino {cur.tipo} en linea {cur.linea} columna {cur.columna}")

    def parse(self)->Program:
        decls = []
        while self.current().tipo != 'EOF':
            decls.append(self.parse_decl_or_stmt())
        return Program(decls)

    def parse_decl_or_stmt(self):
        t = self.current()
        if t.tipo == 'CONST':
            return self.parse_const_decl()
        if t.tipo == 'FUNCTION':
            return self.parse_function_decl()
        if t.tipo == 'PROCEDURE':
            return self.parse_procedure_decl()
        if t.tipo == 'ARRAY':
            return self.parse_array_decl()
        if t.tipo == 'TYPE':
            return self.parse_type_decl()
        if t.tipo in ('IF','WHILE','RETURN','LBRACE'):
            return self.parse_statement()
        if t.tipo == 'ID':
            nxt = self.tokens[self.pos+1] if (self.pos+1) < len(self.tokens) else Token('EOF','',t.linea,t.columna)
            if nxt.tipo == 'LPAREN':
                return self.parse_statement()
            return self.parse_statement()
        raise ParserError(f"Declaracion/Stmt inesperado: {t}")

    def parse_const_decl(self):
        self.eat('CONST')
        name = self.eat('ID').lexema
        self.eat('ASSIGN')
        val = self.parse_expr()
        self.eat('SEMICOLON')
        return ConstDecl(name, val)

    def parse_array_decl(self):
        self.eat('ARRAY')
        name = self.eat('ID').lexema
        self.eat('LBRACK')
        size_tok = self.eat('NUMBER')
        self.eat('RBRACK')
        self.eat('SEMICOLON')
        return ArrayDecl(name, int(size_tok.lexema))

    def parse_type_decl(self):
        self.eat('TYPE')
        name = self.eat('ID').lexema
        self.eat('LBRACE')
        fields = []
        while self.current().tipo != 'RBRACE':
            f = self.eat('ID').lexema
            self.eat('SEMICOLON')
            fields.append((f, None))
        self.eat('RBRACE')
        return TypeDecl(name, fields)

    def parse_function_decl(self):
        self.eat('FUNCTION')
        name = self.eat('ID').lexema
        self.eat('LPAREN')
        params = []
        if self.current().tipo != 'RPAREN':
            pname = self.eat('ID').lexema
            params.append((pname, None))
            while self.current().tipo == 'COMMA':
                self.eat('COMMA')
                pname = self.eat('ID').lexema
                params.append((pname, None))
        self.eat('RPAREN')
        self.eat('LBRACE')
        stmts = []
        while self.current().tipo != 'RBRACE':
            stmts.append(self.parse_statement())
        self.eat('RBRACE')
        return FunctionDecl(name, params, None, stmts)

    def parse_procedure_decl(self):
        self.eat('PROCEDURE')
        name = self.eat('ID').lexema
        self.eat('LPAREN')
        params = []
        if self.current().tipo != 'RPAREN':
            pname = self.eat('ID').lexema
            params.append((pname, None))
            while self.current().tipo == 'COMMA':
                self.eat('COMMA')
                pname = self.eat('ID').lexema
                params.append((pname, None))
        self.eat('RPAREN')
        self.eat('LBRACE')
        stmts = []
        while self.current().tipo != 'RBRACE':
            stmts.append(self.parse_statement())
        self.eat('RBRACE')
        return ProcedureDecl(name, params, stmts)

    def parse_statement(self)->Stmt:
        t = self.current()
        if t.tipo == 'IF':
            return self.parse_if()
        if t.tipo == 'WHILE':
            return self.parse_while()
        if t.tipo == 'RETURN':
            self.eat('RETURN')
            if self.current().tipo != 'SEMICOLON':
                e = self.parse_expr()
            else:
                e = None
            self.eat('SEMICOLON')
            return Return(e)
        if t.tipo == 'LBRACE':
            self.eat('LBRACE')
            stmts = []
            while self.current().tipo != 'RBRACE':
                stmts.append(self.parse_statement())
            self.eat('RBRACE')
            node = ExprStmt(Number(0))
            node.block = stmts
            return node
        if t.tipo == 'ID':
            ident_tok = self.eat('ID')
            cur = self.current()
            if cur.tipo == 'ASSIGN':
                self.eat('ASSIGN')
                expr = self.parse_expr()
                self.eat('SEMICOLON')
                return Assign(Var(ident_tok.lexema), expr)
            elif cur.tipo == 'LBRACK':
                self.eat('LBRACK')
                idx = self.parse_expr()
                self.eat('RBRACK')
                self.eat('ASSIGN')
                expr = self.parse_expr()
                self.eat('SEMICOLON')
                return Assign(ArrayAccess(ident_tok.lexema, idx), expr)
            elif cur.tipo == 'DOT':
                self.eat('DOT')
                field = self.eat('ID').lexema
                self.eat('ASSIGN')
                expr = self.parse_expr()
                self.eat('SEMICOLON')
                return Assign(FieldAccess(Var(ident_tok.lexema), field), expr)
            elif cur.tipo == 'LPAREN':
                call = self.parse_call_with_name(ident_tok.lexema)
                self.eat('SEMICOLON')
                return ExprStmt(call)
            else:
                raise ParserError(f"Esperaba ASSIGN, LPAREN, LBRACK o DOT despues de ID en linea {cur.linea} col {cur.columna}")
        raise ParserError(f"Statement invalido en {t}")

    def parse_if(self)->If:
        self.eat('IF')
        self.eat('LPAREN')
        cond = self.parse_expr()
        self.eat('RPAREN')
        then_block = []
        if self.current().tipo == 'LBRACE':
            self.eat('LBRACE')
            while self.current().tipo != 'RBRACE':
                then_block.append(self.parse_statement())
            self.eat('RBRACE')
        else:
            then_block.append(self.parse_statement())
        else_block = None
        if self.current().tipo == 'ELSE':
            self.eat('ELSE')
            if self.current().tipo == 'LBRACE':
                self.eat('LBRACE')
                else_block = []
                while self.current().tipo != 'RBRACE':
                    else_block.append(self.parse_statement())
                self.eat('RBRACE')
            else:
                else_block = [self.parse_statement()]
        return If(cond, then_block, else_block)

    def parse_while(self)->While:
        self.eat('WHILE')
        self.eat('LPAREN')
        cond = self.parse_expr()
        self.eat('RPAREN')
        self.eat('LBRACE')
        body = []
        while self.current().tipo != 'RBRACE':
            body.append(self.parse_statement())
        self.eat('RBRACE')
        return While(cond, body)

    def parse_call_with_name(self, name: str)->Call:
        self.eat('LPAREN')
        args = []
        if self.current().tipo != 'RPAREN':
            args.append(self.parse_expr())
            while self.current().tipo == 'COMMA':
                self.eat('COMMA')
                args.append(self.parse_expr())
        self.eat('RPAREN')
        return Call(name, args)

    def parse_expr(self)->Expr:
        return self.parse_rel()

    def parse_rel(self)->Expr:
        node = self.parse_add()
        while self.current().tipo == 'OP' and self.current().lexema in ('==','!=','<','>','<=','>='):
            op = self.eat('OP').lexema
            right = self.parse_add()
            node = BinaryOp(node, op, right)
        return node

    def parse_add(self)->Expr:
        node = self.parse_mul()
        while self.current().tipo == 'OP' and self.current().lexema in ('+','-'):
            op = self.eat('OP').lexema
            right = self.parse_mul()
            node = BinaryOp(node, op, right)
        return node

    def parse_mul(self)->Expr:
        node = self.parse_unary()
        while self.current().tipo == 'OP' and self.current().lexema in ('*','/'):
            op = self.eat('OP').lexema
            right = self.parse_unary()
            node = BinaryOp(node, op, right)
        return node

    def parse_unary(self)->Expr:
        t = self.current()
        if t.tipo == 'OP' and t.lexema in ('+','-'):
            op = self.eat('OP').lexema
            right = self.parse_unary()
            return BinaryOp(Number(0), op, right)
        return self.parse_postfix()

    def parse_postfix(self)->Expr:
        t = self.current()
        if t.tipo == 'NUMBER':
            v = float(self.eat('NUMBER').lexema)
            return Number(v)
        if t.tipo == 'ID':
            name = self.eat('ID').lexema
            if self.current().tipo == 'LPAREN':
                return self.parse_call_with_name(name)
            if self.current().tipo == 'LBRACK':
                self.eat('LBRACK')
                idx = self.parse_expr()
                self.eat('RBRACK')
                return ArrayAccess(name, idx)
            if self.current().tipo == 'DOT':
                self.eat('DOT')
                fld = self.eat('ID').lexema
                return FieldAccess(Var(name), fld)
            return Var(name)
        if t.tipo == 'LPAREN':
            self.eat('LPAREN')
            e = self.parse_expr()
            self.eat('RPAREN')
            return e
        raise ParserError(f"Factor inesperado: {t}")
    # PARTE 3: Generador TAC y Visualizador AST

class TACGenerator:
    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.code: List[str] = []
        self.symtab = SymbolTable()

    def new_temp(self)->str:
        t = f"t{self.temp_count}"
        self.temp_count += 1
        entry = SymbolEntry(name=t, sym_type='temp', data_type=None, size=8)
        self.symtab.add(entry)
        return t

    def new_label(self)->str:
        l = f"L{self.label_count}"
        self.label_count += 1
        entry = SymbolEntry(name=l, sym_type='label', label=l)
        self.symtab.add(entry)
        return l

    def gen(self, line: str):
        self.code.append(line)

    def generate(self, node: Program)->List[str]:
        for d in node.decls:
            if isinstance(d, ConstDecl):
                ent = SymbolEntry(name=d.name, sym_type='const', data_type='float', size=8)
                self.symtab.add(ent)
            elif isinstance(d, ArrayDecl):
                ent = SymbolEntry(name=d.name, sym_type='array', data_type='float', size=8*d.size)
                self.symtab.add(ent)
            elif isinstance(d, TypeDecl):
                ent = SymbolEntry(name=d.name, sym_type='type', data_type=d.name, extra={'fields':d.fields})
                self.symtab.add(ent)
            elif isinstance(d, FunctionDecl):
                ent = SymbolEntry(name=d.name, sym_type='func', params=[p[0] for p in d.params], return_type=d.ret_type, label=f"func_{d.name}")
                self.symtab.add(ent)
            elif isinstance(d, ProcedureDecl):
                ent = SymbolEntry(name=d.name, sym_type='proc', params=[p[0] for p in d.params], label=f"proc_{d.name}")
                self.symtab.add(ent)
            elif isinstance(d, VarDecl):
                ent = SymbolEntry(name=d.name, sym_type='var', data_type=d.typ or 'float', size=8)
                self.symtab.add(ent)

        for d in node.decls:
            if isinstance(d, ConstDecl):
                t = self.visit_expr(d.value)
                self.gen(f"{d.name} = {t}")
            elif isinstance(d, ArrayDecl):
                pass
            elif isinstance(d, TypeDecl):
                pass
            elif isinstance(d, FunctionDecl):
                label = f"func_{d.name}"
                self.gen(f"label {label}")
                e = self.symtab.lookup(d.name)
                if e: e.label = label
                self.symtab.enter_scope()
                for pname, _ in d.params:
                    pentry = SymbolEntry(name=pname, sym_type='param', data_type=None, size=8)
                    self.symtab.add(pentry)
                for s in d.body:
                    self.visit_stmt(s)
                self.symtab.exit_scope()
            elif isinstance(d, ProcedureDecl):
                label = f"proc_{d.name}"
                self.gen(f"label {label}")
                e = self.symtab.lookup(d.name)
                if e: e.label = label
                self.symtab.enter_scope()
                for pname,_ in d.params:
                    pentry = SymbolEntry(name=pname, sym_type='param', data_type=None, size=8)
                    self.symtab.add(pentry)
                for s in d.body:
                    self.visit_stmt(s)
                self.symtab.exit_scope()
            else:
                if isinstance(d, Stmt):
                    self.visit_stmt(d)
        return self.code

    def visit_stmt(self, s: Stmt):
        if isinstance(s, Assign):
            rhs = self.visit_expr(s.expr)
            if isinstance(s.target, Var):
                name = s.target.name
                if not self.symtab.lookup(name):
                    self.symtab.add(SymbolEntry(name=name, sym_type='var', data_type='float', size=8))
                self.gen(f"{name} = {rhs}")
            elif isinstance(s.target, ArrayAccess):
                arr = s.target.name
                idx = self.visit_expr(s.target.index)
                if not self.symtab.lookup(arr):
                    self.symtab.add(SymbolEntry(name=arr, sym_type='array', data_type='float', size=None))
                self.gen(f"store {arr}, {idx}, {rhs}")
            elif isinstance(s.target, FieldAccess):
                base_temp = self.visit_expr(s.target.expr)
                field = s.target.field
                self.gen(f"field_store {base_temp}, {field}, {rhs}")
            else:
                raise Exception("Assign target no soportado")
        elif isinstance(s, ExprStmt):
            self.visit_expr(s.expr)
        elif isinstance(s, If):
            condt = self.visit_expr(s.cond)
            l_else = self.new_label()
            l_end = self.new_label()
            self.gen(f"if_false {condt} goto {l_else}")
            self.symtab.enter_scope()
            for st in s.then_block:
                self.visit_stmt(st)
            self.symtab.exit_scope()
            self.gen(f"goto {l_end}")
            self.gen(f"label {l_else}")
            if s.else_block:
                self.symtab.enter_scope()
                for st in s.else_block:
                    self.visit_stmt(st)
                self.symtab.exit_scope()
            self.gen(f"label {l_end}")
        elif isinstance(s, While):
            l_begin = self.new_label()
            l_end = self.new_label()
            self.gen(f"label {l_begin}")
            condt = self.visit_expr(s.cond)
            self.gen(f"if_false {condt} goto {l_end}")
            self.symtab.enter_scope()
            for st in s.body:
                self.visit_stmt(st)
            self.symtab.exit_scope()
            self.gen(f"goto {l_begin}")
            self.gen(f"label {l_end}")
        elif isinstance(s, Return):
            if s.expr:
                val = self.visit_expr(s.expr)
                self.gen(f"return {val}")
            else:
                self.gen("return")
        else:
            raise Exception("Stmt no soportado en visit_stmt")

    def visit_expr(self, e: Expr)->str:
        if isinstance(e, Number):
            t = self.new_temp()
            self.gen(f"{t} = {e.value}")
            return t
        if isinstance(e, Var):
            ent = self.symtab.lookup(e.name)
            if not ent:
                self.symtab.add(SymbolEntry(name=e.name, sym_type='var', data_type='float', size=8))
            return e.name
        if isinstance(e, Call):
            arg_temps = []
            for a in e.args:
                arg_temps.append(self.visit_expr(a))
            for at in arg_temps:
                self.gen(f"param {at}")
            t = self.new_temp()
            self.gen(f"{t} = call {e.name}, {len(arg_temps)}")
            if not self.symtab.lookup(e.name):
                self.symtab.add(SymbolEntry(name=e.name, sym_type='func', params=[None]*len(e.args), label=f"func_{e.name}"))
            return t
        if isinstance(e, ArrayAccess):
            idx = self.visit_expr(e.index)
            t = self.new_temp()
            self.gen(f"{t} = load {e.name}, {idx}")
            if not self.symtab.lookup(e.name):
                self.symtab.add(SymbolEntry(name=e.name, sym_type='array', data_type='float'))
            return t
        if isinstance(e, FieldAccess):
            base = self.visit_expr(e.expr)
            t = self.new_temp()
            self.gen(f"{t} = field_load {base}, {e.field}")
            return t
        if isinstance(e, BinaryOp):
            l = self.visit_expr(e.left)
            r = self.visit_expr(e.right)
            t = self.new_temp()
            self.gen(f"{t} = {l} {e.op} {r}")
            return t
        raise Exception("Expr no soportada en visit_expr")


class ASTVisualizer:
    def __init__(self):
        self.lines = ["digraph AST {", "node [shape=box];"]
    def render(self, node: ASTNode)->str:
        self._visit(node)
        self.lines.append("}")
        return "\n".join(self.lines)
    def _label(self,node,text):
        self.lines.append(f' n{node.id} [label="{text}"];')
    def _edge(self,a,b):
        self.lines.append(f' n{a.id} -> n{b.id};')
    def _visit(self,node):
        method = '_visit_' + node.__class__.__name__
        if hasattr(self, method):
            getattr(self, method)(node)
        else:
            self._label(node, node.__class__.__name__)

    def _visit_Program(self,node: Program):
        self._label(node,'Program')
        for d in node.decls:
            self._visit(d); self._edge(node,d)
    def _visit_ConstDecl(self,n):
        self._label(n,f"Const {n.name}")
        self._visit(n.value); self._edge(n,n.value)
    def _visit_ArrayDecl(self,n):
        self._label(n,f"Array {n.name}[{n.size}]")
    def _visit_TypeDecl(self,n):
        self._label(n,f"Type {n.name}")
        for f in n.fields:
            fn = ASTNode(); self._label(fn,f[0]); self._edge(n,fn)
    def _visit_FunctionDecl(self,n):
        self._label(n,f"Function {n.name}({','.join([p[0] for p in n.params])})")
        for s in n.body:
            self._visit(s); self._edge(n,s)
    def _visit_ProcedureDecl(self,n):
        self._label(n,f"Procedure {n.name}({','.join([p[0] for p in n.params])})")
        for s in n.body:
            self._visit(s); self._edge(n,s)
    def _visit_Assign(self,n):
        self._label(n,"Assign")
        self._visit(n.target); self._edge(n,n.target)
        self._visit(n.expr); self._edge(n,n.expr)
    def _visit_Var(self,n):
        self._label(n,f"Var\\n{n.name}")
    def _visit_Number(self,n):
        self._label(n,f"Number\\n{n.value}")
    def _visit_BinaryOp(self,n):
        self._label(n,f"BinOp\\n{n.op}")
        self._visit(n.left); self._edge(n,n.left)
        self._visit(n.right); self._edge(n,n.right)
    def _visit_Call(self,n):
        self._label(n,f"Call\\n{n.name}()")
        for a in n.args:
            self._visit(a); self._edge(n,a)
    def _visit_ArrayAccess(self,n):
        self._label(n,f"ArrayAccess\\n{n.name}")
        self._visit(n.index); self._edge(n,n.index)
    def _visit_FieldAccess(self,n):
        self._label(n,f"FieldAccess\\n{n.field}")
        self._visit(n.expr); self._edge(n,n.expr)
    def _visit_If(self,n):
        self._label(n,"If")
        self._visit(n.cond); self._edge(n,n.cond)
        then_node = ASTNode(); self._label(then_node,"Then"); self._edge(n,then_node)
        for s in n.then_block:
            self._visit(s); self._edge(then_node,s)
        if n.else_block:
            else_node = ASTNode(); self._label(else_node,"Else"); self._edge(n,else_node)
            for s in n.else_block:
                self._visit(s); self._edge(else_node,s)
    def _visit_While(self,n):
        self._label(n,"While"); self._visit(n.cond); self._edge(n,n.cond)
        body = ASTNode(); self._label(body,"Body"); self._edge(n,body)
        for s in n.body:
            self._visit(s); self._edge(body,s)
    def _visit_Return(self,n):
        self._label(n,"Return")
        if n.expr:
            self._visit(n.expr); self._edge(n,n.expr)
    def _visit_ExprStmt(self,n):
        self._label(n,"ExprStmt")
        self._visit(n.expr); self._edge(n,n.expr)


def try_make_png(dotfile="ast.dot", pngfile="ast.png"):
    if shutil.which("dot"):
        try:
            subprocess.run(["dot","-Tpng",dotfile,"-o",pngfile], check=True)
            print(f"AST PNG generado: {pngfile}")
        except Exception as e:
            print(f"Error creando PNG con dot: {e}")
    else:
        print("Graphviz 'dot' no encontrado en PATH (opcional)")


if __name__ == '__main__':
    try:
        with open("datos.txt","r",encoding="utf-8") as f:
            src = f.read()
    except FileNotFoundError:
        print("ERROR: Crea 'datos.txt' con el codigo fuente.")
        sys.exit(1)

    print("         COMPILADOR - Analisis Completo")
    
    print("\n--- CODIGO FUENTE ---")
    print(src)

    lexer = Lexer(src)
    tokens = lexer.tokenize()
    print(f"\n--- TOKENS ({len(tokens)} generados) ---")
    for t in tokens:
        print(t)

    parser = Parser(tokens)
    try:
        program = parser.parse()
        print("\nAnalisis sintactico completado")
    except ParserError as pe:
        print(f"\nError de parseo: {pe}")
        sys.exit(1)

    print("\n--- GENERANDO AST (archivo .dot) ---")
    vis = ASTVisualizer()
    dot = vis.render(program)
    with open("ast.dot","w",encoding="utf-8") as f:
        f.write(dot)
    print("Archivo ast.dot generado")
    
    try_make_png("ast.dot","ast.png")

    print("\n--- GENERANDO CODIGO INTERMEDIO (TAC) ---")
    tacgen = TACGenerator()
    code = tacgen.generate(program)
    for i, line in enumerate(code, 1):
        print(f"{i:3d}: {line}")

    print("\n--- TABLA DE SIMBOLOS ---")
    print(tacgen.symtab)

    print("Desea visualizar el AST graficamente con tkinter? (s/n): ", end="")
    try:
        respuesta = input().strip().lower()
    except:
        respuesta = 'n'
    
    if respuesta in ['s', 'si', 'y', 'yes', '']:
        print("\nAbriendo visualizador grafico...")
        visualize_ast_from_dot("ast.dot")
    else:
        print("\nCompilacion completada. Revisa ast.dot para el arbol.")