import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple, Optional

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
    
    def peek(self, offset=0) -> Optional[str]:
        pos = self.pos + offset
        if pos < self.length:
            return self.content[pos]
        return None
    
    def peek_ahead_is_digit(self) -> bool:
        c = self.peek(1)
        return c and c.isdigit()
    
    def advance(self) -> Optional[str]:
        if self.pos < self.length:
            c = self.content[self.pos]
            self.pos += 1
            return c
        return None
    
    def skip_whitespace(self):
        while self.pos < self.length and self.content[self.pos] in ' \t\n\r':
            self.pos += 1
    
    def read_until(self, chars: str) -> str:
        result = []
        while self.pos < self.length and self.content[self.pos] not in chars:
            result.append(self.content[self.pos])
            self.pos += 1
        return ''.join(result)
    
    def parse_node(self):
        node_id = []
        while self.pos < self.length and (self.content[self.pos].isalnum()):
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
    
    def find_text(self, text: str) -> bool:
        start = self.pos
        for char in text:
            if self.pos >= self.length or self.content[self.pos] != char:
                self.pos = start
                return False
            self.pos += 1
        return True
    
    def read_label(self) -> str:
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


class DotASTVisualizer:
    def __init__(self, root, dot_file="ast.dot"):
        self.root = root
        self.root.title("🌳 Visualizador de AST")
        self.root.geometry("1600x900")
        self.root.configure(bg="#2C3E50")
        
        self.nodes = {}
        self.edges = []
        self.node_positions = {}
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
            
            print(f"✓ Cargado: {len(self.nodes)} nodos, {len(self.edges)} aristas")
            return len(self.nodes) > 0
            
        except FileNotFoundError:
            print(f"✗ Archivo {filename} no encontrado")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
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
            text="🌳 ÁRBOL DE SINTAXIS ABSTRACTA (AST)",
            bg="#34495E",
            fg="white",
            font=("Arial", 16, "bold"),
            pady=12
        )
        title.pack(side=tk.LEFT, padx=20)
        
        stats = tk.Label(
            title_frame,
            text=f"📊 {len(self.nodes)} nodos | {len(self.edges)} conexiones",
            bg="#34495E",
            fg="#ECF0F1",
            font=("Arial", 10),
            pady=12
        )
        stats.pack(side=tk.RIGHT, padx=20)
        
        canvas_frame = tk.Frame(main_frame, bg="#2C3E50")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="white",
            highlightthickness=0,
            cursor="hand2"
        )
        
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.configure(
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )
        
        toolbar = tk.Frame(main_frame, bg="#34495E", height=40)
        toolbar.pack(fill=tk.X, side=tk.BOTTOM)
        
        instructions = tk.Label(
            toolbar,
            text="🖱️ Rueda del mouse: Zoom | Click medio + arrastrar: Mover | Hover: Ver info",
            bg="#34495E",
            fg="#ECF0F1",
            font=("Arial", 9),
            pady=8
        )
        instructions.pack(side=tk.LEFT, padx=20)
        
        reset_btn = tk.Button(
            toolbar,
            text="🔄 Resetear Vista",
            command=self.reset_view,
            bg="#3498DB",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        reset_btn.pack(side=tk.RIGHT, padx=20)
        
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<Button-4>", self.zoom)
        self.canvas.bind("<Button-5>", self.zoom)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)
        
        self.scale_factor = 1.0
    
    def get_node_color(self, label: str) -> str:
        label_lower = label.lower()
        
        colors = {
            'program': '#3498DB',
            'function': '#27AE60',
            'func': '#27AE60',
            'procedure': '#27AE60',
            'proc': '#27AE60',
            'const': '#9B59B6',
            'var': '#7F8C8D',
            'array': '#E67E22',
            'type': '#E67E22',
            'assign': '#16A085',
            'if': '#F39C12',
            'while': '#F39C12',
            'return': '#E74C3C',
            'binop': '#1ABC9C',
            'number': '#95A5A6',
            'call': '#2ECC71',
            'then': '#F39C12',
            'else': '#E67E22',
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
                    fill="#95A5A6",
                    width=2,
                    arrow=tk.LAST,
                    arrowshape=(10, 12, 5),
                    tags="edge"
                )
                
                self.draw_node(child_id, child_x, child_y, width // 2, level + 1)
        
        x1 = x - self.node_w // 2
        y1 = y - self.node_h // 2
        x2 = x + self.node_w // 2
        y2 = y + self.node_h // 2
        
        color = self.get_node_color(label)
        
        shadow_offset = 3
        self.canvas.create_rectangle(
            x1 + shadow_offset, y1 + shadow_offset,
            x2 + shadow_offset, y2 + shadow_offset,
            fill="#00000020",
            outline="",
            tags="shadow"
        )
        
        rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=color,
            outline="#2C3E50",
            width=2,
            tags=("node", node_id)
        )
        
        text = self.canvas.create_text(
            x, y,
            text=label,
            font=("Arial", 9, "bold"),
            fill="white",
            width=self.node_w - 10,
            tags=("text", node_id)
        )
        
        self.node_positions[node_id] = (x, y)
        
        self.canvas.tag_bind(rect, "<Enter>", 
            lambda e, nid=node_id, lbl=label: self.show_tooltip(e, nid, lbl))
        self.canvas.tag_bind(rect, "<Leave>", self.hide_tooltip)
        self.canvas.tag_bind(text, "<Enter>", 
            lambda e, nid=node_id, lbl=label: self.show_tooltip(e, nid, lbl))
        self.canvas.tag_bind(text, "<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event, node_id, label):
        info = f"🏷️ ID: {node_id}\n"
        info += f"📝 Label: {label}\n"
        
        children = self.children_map.get(node_id, [])
        if children:
            info += f"👶 Hijos: {len(children)}"
        
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
        
        frame = tk.Frame(self.tooltip, bg="#2C3E50", relief=tk.SOLID, borderwidth=2)
        frame.pack()
        
        label_widget = tk.Label(
            frame,
            text=info,
            bg="#2C3E50",
            fg="white",
            font=("Arial", 9),
            padx=12,
            pady=8,
            justify=tk.LEFT
        )
        label_widget.pack()
    
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


def visualize_ast_from_dot(dot_file="ast.dot"):
    root = tk.Tk()
    app = DotASTVisualizer(root, dot_file)
    root.mainloop()


if __name__ == "__main__":
    visualize_ast_from_dot("ast.dot")
