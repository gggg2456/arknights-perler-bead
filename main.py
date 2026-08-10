import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
import sys
import subprocess

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

for p in ["opencv-python", "numpy", "pillow"]:
    try:
        __import__(p.replace("-", "_"))
    except ImportError:
        install(p)

BEAD_COLORS = [
    {"name":"白色","hex":"#FFFFFF","num":1,"sym":"W"},
    {"name":"黑色","hex":"#000000","num":2,"sym":"B"},
    {"name":"红色","hex":"#FF0000","num":3,"sym":"R"},
    {"name":"蓝色","hex":"#0066FF","num":4,"sym":"BL"},
    {"name":"黄色","hex":"#FFFF00","num":5,"sym":"Y"},
    {"name":"绿色","hex":"#00CC00","num":6,"sym":"G"},
    {"name":"橙色","hex":"#FF8800","num":7,"sym":"O"},
    {"name":"紫色","hex":"#8800CC","num":8,"sym":"P"},
    {"name":"粉色","hex":"#FF88CC","num":9,"sym":"PK"},
    {"name":"棕色","hex":"#884400","num":10,"sym":"BR"},
    {"name":"灰色","hex":"#888888","num":11,"sym":"GR"},
    {"name":"青色","hex":"#00CCCC","num":12,"sym":"C"},
    {"name":"浅绿","hex":"#88DD88","num":13,"sym":"LG"},
    {"name":"深红","hex":"#CC0000","num":14,"sym":"DR"},
    {"name":"金色","hex":"#FFCC00","num":15,"sym":"GD"},
    {"name":"银色","hex":"#CCCCCC","num":16,"sym":"SV"},
    {"name":"深蓝","hex":"#000088","num":17,"sym":"DB"},
    {"name":"浅粉","hex":"#FFCCDD","num":18,"sym":"LP"},
    {"name":"米色","hex":"#FFEECC","num":19,"sym":"BE"},
    {"name":"深绿","hex":"#006600","num":20,"sym":"DG"},
]

def hex2rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

def dist(a,b):
    return ((a[0]-b[0])**2+(a[1]-b[1])**2+(a[2]-b[2])**2)**0.5

def match(rgb):
    best, mn = BEAD_COLORS[0], float("inf")
    for c in BEAD_COLORS:
        d = dist(rgb, hex2rgb(c["hex"]))
        if d < mn:
            mn = d
            best = c
    return best

BG = "#1a1a2e"
PANEL = "#16213e"
CARD = "#0f3460"
RED = "#e94560"
CYAN = "#00b4d8"
TEXT = "#e0e0e0"
DIM = "#8899aa"
BORDER = "#2a3a5c"

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("罗德岛拼豆工坊")
        self.root.geometry("800x700")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.img = None
        self.grid = None
        self.counts = None

        self.cols = tk.StringVar(value="40")
        self.rows = tk.StringVar(value="40")
        self.style = tk.StringVar(value="solid")
        self.coords = tk.BooleanVar(value=True)
        self.scale = tk.DoubleVar(value=1.0)

        self.ui()
        self.root.mainloop()

    def ui(self):
        hdr = tk.Frame(self.root, bg=PANEL, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="罗德岛拼豆工坊", font=("Microsoft YaHei",18,"bold"),
                 bg=PANEL, fg=CYAN).pack(pady=5)
        tk.Label(hdr, text="上传图片 - 生成拼豆图纸 + 材料清单",
                 bg=PANEL, fg=DIM, font=("Microsoft YaHei",9)).pack()

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        left = tk.Frame(main, bg=BG)
        left.pack(side=tk.LEFT, fill="both", expand=True, padx=(0,5))

        right = tk.Frame(main, bg=BG, width=400)
        right.pack(side=tk.RIGHT, fill="both", expand=True, padx=(5,0))
        right.pack_propagate(False)

        c1 = tk.Frame(left, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        c1.pack(fill="x", pady=5)
        tk.Label(c1, text="选择图片", font=("Microsoft YaHei",11,"bold"),
                 bg=CARD, fg=CYAN).pack(pady=(10,5))
        self.lbl = tk.Label(c1, text="未选择", bg=CARD, fg=DIM)
        self.lbl.pack()
        tk.Button(c1, text="上传图片", bg=RED, fg="white",
                  font=("Microsoft YaHei",10,"bold"), relief="flat",
                  padx=20, pady=5, command=self.load).pack(pady=10)

        c2 = tk.Frame(left, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        c2.pack(fill="both", expand=True, pady=5)
        tk.Label(c2, text="原图预览", bg=CARD, fg=CYAN,
                 font=("Microsoft YaHei",10,"bold")).pack(pady=(10,5))
        self.ocv = tk.Canvas(c2, bg=BG, highlightthickness=0)
        self.ocv.pack(fill="both", expand=True, padx=10, pady=10)

        c3 = tk.Frame(right, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        c3.pack(fill="x", pady=5)
        tk.Label(c3, text="参数设置", font=("Microsoft YaHei",11,"bold"),
                 bg=CARD, fg=CYAN).pack(pady=(10,5))

        f1 = tk.Frame(c3, bg=CARD)
        f1.pack(pady=5)
        tk.Label(f1, text="宽:", bg=CARD, fg=TEXT).pack(side=tk.LEFT)
        tk.Entry(f1, textvariable=self.cols, width=6, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT).pack(side=tk.LEFT, padx=5)
        tk.Label(f1, text="高:", bg=CARD, fg=TEXT).pack(side=tk.LEFT)
        tk.Entry(f1, textvariable=self.rows, width=6, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT).pack(side=tk.LEFT, padx=5)

        f2 = tk.Frame(c3, bg=CARD)
        f2.pack(pady=5)
        tk.Label(f2, text="风格:", bg=CARD, fg=TEXT).pack(side=tk.LEFT)
        for t,v in [("纯色","solid"),("色号","number"),("符号","symbol")]:
            tk.Radiobutton(f2, text=t, variable=self.style, value=v,
                           bg=CARD, fg=TEXT, selectcolor=PANEL,
                           command=self.preview).pack(side=tk.LEFT, padx=3)

        f3 = tk.Frame(c3, bg=CARD)
        f3.pack(pady=5)
        tk.Checkbutton(f3, text="行号/列号", variable=self.coords,
                       bg=CARD, fg=TEXT, selectcolor=PANEL,
                       command=self.preview).pack()

        f4 = tk.Frame(c3, bg=CARD)
        f4.pack(pady=5)
        tk.Label(f4, text="缩放:", bg=CARD, fg=DIM).pack(side=tk.LEFT)
        tk.Scale(f4, from_=0.5, to=3, resolution=0.1, variable=self.scale,
                 orient=tk.HORIZONTAL, length=120, bg=CARD, fg=TEXT,
                 troughcolor=BG, command=lambda e:self.preview()).pack(side=tk.LEFT)
        self.slbl = tk.Label(f4, text="1.0x", bg=CARD, fg=CYAN)
        self.slbl.pack(side=tk.LEFT, padx=5)

        tk.Button(c3, text="生成图纸", bg=RED, fg="white",
                  font=("Microsoft YaHei",12,"bold"), relief="flat",
                  padx=30, pady=8, command=self.generate).pack(pady=15)

        c4 = tk.Frame(right, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        c4.pack(fill="both", expand=True, pady=5)
        tk.Label(c4, text="图纸预览", bg=CARD, fg=CYAN,
                 font=("Microsoft YaHei",10,"bold")).pack(pady=(10,5))
        self.pcv = tk.Canvas(c4, bg=BG, highlightthickness=0)
        self.pcv.pack(fill="both", expand=True, padx=10, pady=5)
        tk.Button(c4, text="保存图纸", bg=CYAN, fg="white",
                  font=("Microsoft YaHei",10), relief="flat",
                  command=self.save).pack(pady=5)

        c5 = tk.Frame(self.root, bg=CARD, highlightbackground=BORDER, highlightthickness=1, height=120)
        c5.pack(fill="x", padx=10, pady=(5,10))
        c5.pack_propagate(False)
        tk.Label(c5, text="材料清单", bg=CARD, fg=CYAN,
                 font=("Microsoft YaHei",10,"bold")).pack(pady=(5,2), anchor="w", padx=10)
        self.mtxt = tk.Text(c5, font=("Consolas",9), bg=BG, fg=TEXT,
                            relief="flat", height=4, wrap=tk.WORD)
        self.mtxt.pack(fill="both", expand=True, padx=10, pady=(0,5))
        tk.Button(c5, text="复制", bg=PANEL, fg=TEXT, relief="flat",
                  command=self.copymat).pack(pady=(0,5), padx=10, anchor="e")

        self.sts = tk.Label(self.root, text="就绪", bg=PANEL, fg=DIM,
                            font=("Microsoft YaHei",8), anchor="w")
        self.sts.pack(fill="x", side=tk.BOTTOM, padx=10, pady=(0,5))

    def load(self):
        p = filedialog.askopenfilename(filetypes=[("图片","*.png *.jpg *.jpeg *.bmp *.webp")])
        if not p:
            return
        img = cv2.imread(p)
        if img is None:
            messagebox.showerror("错误","无法读取")
            return
        self.img = img
        name = os.path.basename(p)
        h,w = img.shape[:2]
        self.lbl.config(text=f"{name}\n{w}x{h}", fg="#27ae60")
        self.sts.config(text=f"已加载: {name}")
        if w <= 100 and h <= 100:
            self.cols.set(str(w))
            self.rows.set(str(h))
        else:
            s = 100 / max(w,h)
            self.cols.set(str(max(5, int(w*s))))
            self.rows.set(str(max(5, int(h*s))))
        self.show_orig()

    def show_orig(self):
        if self.img is None:
            return
        rgb = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        s = min(250/pil.width, 200/pil.height, 1)
        if s < 1:
            pil = pil.resize((int(pil.width*s), int(pil.height*s)), Image.NEAREST)
        tmp = os.path.join(tempfile.gettempdir(), "orig.png")
        pil.save(tmp)
        self.opi = tk.PhotoImage(file=tmp)
        self.ocv.delete("all")
        self.ocv.create_image(150, 140, image=self.opi)

    def generate(self):
        if self.img is None:
            messagebox.showwarning("提示","请先上传图片")
            return
        try:
            c = int(self.cols.get())
            r = int(self.rows.get())
        except:
            messagebox.showerror("错误","无效行列数")
            return
        if c<5 or c>100 or r<5 or r>100:
            messagebox.showerror("错误","5-100")
            return
        self.sts.config(text="生成中...")
        self.root.update()
        resized = cv2.resize(self.img, (c,r), interpolation=cv2.INTER_NEAREST)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        grid = []
        cnt = {}
        for y in range(r):
            row = []
            for x in range(c):
                b = match(tuple(rgb[y,x]))
                row.append(b)
                cnt[b["name"]] = cnt.get(b["name"],0)+1
            grid.append(row)
        self.grid = grid
        self.counts = cnt
        self.preview()
        self.upmat()
        self.sts.config(text=f"完成: {c}x{r}, {len(cnt)}种颜色")

    def preview(self):
        if not self.grid:
            return
        r = len(self.grid)
        c = len(self.grid[0])
        s = self.scale.get()
        self.slbl.config(text=f"{s:.1f}x")
        cl = max(4, int(20*s))
        m = int(24*s) if self.coords.get() else 0
        st = self.style.get()
        sc = self.coords.get()

        w = c*cl+m
        h = r*cl+m
        img = Image.new("RGB", (w,h), BG)
        dr = ImageDraw.Draw(img)
        try:
            fnt = ImageFont.truetype("simhei.ttf", max(6,int(10*s)))
        except:
            fnt = ImageFont.load_default()

        if sc:
            for x in range(c):
                dr.text((m+x*cl+cl//2-4, 2), str(x+1), fill=TEXT, font=fnt)
            for y in range(r):
                dr.text((2, m+y*cl+cl//2-5), str(y+1), fill=TEXT, font=fnt)

        for y in range(r):
            for x in range(c):
                b = self.grid[y][x]
                px = m+x*cl
                py = m+y*cl
                dr.rectangle([px,py,px+cl-1,py+cl-1], fill=b["hex"],
                             outline="#444466" if cl>6 else None)
                if cl >= 10:
                    rgb = hex2rgb(b["hex"])
                    tc = "#000" if sum(rgb)>400 else "#fff"
                    if st == "number":
                        dr.text((px+cl//2-4, py+cl//2-5), str(b["num"]), fill=tc, font=fnt)
                    elif st == "symbol":
                        dr.text((px+cl//2-4, py+cl//2-5), b["sym"], fill=tc, font=fnt)

        tmp = os.path.join(tempfile.gettempdir(), "preview.png")
        img.save(tmp)
        self.ppi = tk.PhotoImage(file=tmp)
        self.pcv.delete("all")
        self.pcv.create_image(w//2+10, h//2+10, image=self.ppi)
        self.pcv.config(scrollregion=(0,0,w+20,h+20))

    def upmat(self):
        if not self.counts:
            return
        self.mtxt.delete("1.0", tk.END)
        total = sum(self.counts.values())
        lines = []
        for name, cnt in sorted(self.counts.items(), key=lambda x:x[1], reverse=True):
            b = next(x for x in BEAD_COLORS if x["name"]==name)
            pct = cnt/total*100
            bar = "|" * int(pct/2)
            lines.append(f"#{b['num']:2d} {name:4s} x{cnt:4d}  {bar} {pct:.1f}%")
        lines.append("-"*40)
        lines.append(f"总计: {total}颗 | {len(self.counts)}种颜色")
        self.mtxt.insert("1.0", "\n".join(lines))

    def save(self):
        if not self.grid:
            messagebox.showwarning("提示","请先生成图纸")
            return
        p = filedialog.asksaveasfilename(defaultextension=".png",
                                          filetypes=[("PNG","*.png")])
        if not p:
            return
        r = len(self.grid)
        c = len(self.grid[0])
        cl = 20
        m = 24 if self.coords.get() else 0
        st = self.style.get()
        sc = self.coords.get()
        w = c*cl+m
        h = r*cl+m
        img = Image.new("RGB", (w,h), "white")
        dr = ImageDraw.Draw(img)
        try:
            fnt = ImageFont.truetype("simhei.ttf", 10)
        except:
            fnt = ImageFont.load_default()
        if sc:
            for x in range(c):
                dr.text((m+x*cl+cl//2-4,3), str(x+1), fill="black", font=fnt)
            for y in range(r):
                dr.text((3,m+y*cl+cl//2-5), str(y+1), fill="black", font=fnt)
        for y in range(r):
            for x in range(c):
                b = self.grid[y][x]
                px = m+x*cl
                py = m+y*cl
                dr.rectangle([px,py,px+cl-1,py+cl-1], fill=b["hex"], outline="#ccc")
                if st == "number":
                    dr.text((px+cl//2-4,py+cl//2-5), str(b["num"]), fill="black", font=fnt)
                elif st == "symbol":
                    dr.text((px+cl//2-4,py+cl//2-5), b["sym"], fill="black", font=fnt)
        img.save(p)
        self.sts.config(text=f"已保存: {p}")

    def copymat(self):
        t = self.mtxt.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(t)
        self.sts.config(text="已复制")


if __name__ == "__main__":
    App()