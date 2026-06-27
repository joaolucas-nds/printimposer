#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrintImposer v1.0
Ferramenta de Imposição de Páginas para Impressão em Massa

Selecione imagens, configure o layout e gere PDFs/PNGs prontos para impressão.
"""

import os
import sys
import math
import json
import threading
import io
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    USE_CTK = True
except ImportError:
    USE_CTK = False

from PIL import Image, ImageDraw, ImageOps, ImageTk, ImageFont

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

VERSION  = "1.0.0"
APP_NAME = "PrintImposer"
MM_TO_INCH = 1.0 / 25.4
SUPPORTED_EXT = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp'}
THUMB_W, THUMB_H = 56, 56
PREVIEW_MAX = (460, 580)

PAPER_SIZES: Dict[str, Optional[Tuple[float, float]]] = {
    "A3":      (297.0, 420.0),
    "A4":      (210.0, 297.0),
    "A5":      (148.0, 210.0),
    "A6":      (105.0, 148.0),
    "Letter":  (215.9, 279.4),
    "Legal":   (215.9, 355.6),
    "Tabloid": (279.4, 431.8),
    "Custom":  None,
}

NUP_LAYOUTS: Dict[str, Tuple[int, int]] = {
    "1-up  (1×1)":  (1, 1),
    "2-up  (2×1)":  (2, 1),
    "2-up  (1×2)":  (1, 2),
    "4-up  (2×2)":  (2, 2),
    "6-up  (3×2)":  (3, 2),
    "6-up  (2×3)":  (2, 3),
    "8-up  (4×2)":  (4, 2),
    "8-up  (2×4)":  (2, 4),
    "9-up  (3×3)":  (3, 3),
    "12-up (4×3)":  (4, 3),
    "16-up (4×4)":  (4, 4),
}

LINE_STYLES  = ["Sólida", "Tracejada", "Pontilhada"]
FIT_LABELS   = ["Ajustar (fit)", "Preencher (fill)", "Esticar (stretch)"]
FIT_KEYS     = ["fit",           "fill",              "stretch"]
OUT_FORMATS  = ["PDF", "PNG", "JPEG", "TIFF"]


# ══════════════════════════════════════════════════════════════════════════════
# MODELO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

class ImageEntry:
    def __init__(self, path: str):
        self.path     = path
        self.filename = Path(path).name
        self.quantity = 1
        self.pil_thumb: Optional[Image.Image] = None
        self._load_thumb()

    def _load_thumb(self):
        try:
            img = Image.open(self.path).convert("RGBA")
            img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
            # Paste on white bg
            bg = Image.new("RGB", (THUMB_W, THUMB_H), (50, 50, 60))
            x = (THUMB_W - img.width)  // 2
            y = (THUMB_H - img.height) // 2
            bg.paste(img, (x, y), img.split()[3] if img.mode == "RGBA" else None)
            self.pil_thumb = bg
        except Exception:
            self.pil_thumb = None


class LayoutConfig:
    def __init__(self):
        self.nup_key:           str   = "4-up  (2×2)"
        self.paper_key:         str   = "A4"
        self.paper_w_mm:        float = 210.0
        self.paper_h_mm:        float = 297.0
        self.dpi:               int   = 300
        self.margin_outer_mm:   float = 0.0
        self.margin_between_mm: float = 0.0
        self.bg_color:          str   = "#FFFFFF"
        self.fit_mode:          str   = "fit"
        self.auto_rotate:       bool  = True
        self.cut_lines:         bool  = False
        self.cut_color:         str   = "#999999"
        self.cut_width_px:      int   = 1
        self.cut_style:         str   = "Sólida"
        self.cut_dash:          int   = 10
        self.output_format:     str   = "PDF"
        self.output_prefix:     str   = "folha_"
        self.output_suffix:     str   = ""
        self.output_dir:        str   = str(Path.home() / "Desktop")

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def from_dict(self, d: dict):
        for k, v in d.items():
            if hasattr(self, k):
                setattr(self, k, v)


# ══════════════════════════════════════════════════════════════════════════════
# MOTOR DE IMPOSIÇÃO
# ══════════════════════════════════════════════════════════════════════════════

class ImpositionEngine:
    def __init__(self, entries: List[ImageEntry], cfg: LayoutConfig):
        self.entries = entries
        self.cfg     = cfg

    def _mm_px(self, mm: float) -> int:
        return max(0, int(round(mm * self.cfg.dpi * MM_TO_INCH)))

    def _page_px(self) -> Tuple[int, int]:
        return self._mm_px(self.cfg.paper_w_mm), self._mm_px(self.cfg.paper_h_mm)

    def _grid(self) -> Tuple[int, int]:
        return NUP_LAYOUTS[self.cfg.nup_key]

    def _expand(self) -> List[str]:
        out = []
        for e in self.entries:
            out.extend([e.path] * max(1, e.quantity))
        return out

    def total_pages(self) -> int:
        paths = self._expand()
        if not paths:
            return 0
        cols, rows = self._grid()
        return math.ceil(len(paths) / (cols * rows))

    def total_expanded(self) -> int:
        return len(self._expand())

    @staticmethod
    def _hex_rgb(h: str) -> Tuple[int, int, int]:
        h = h.lstrip('#')
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def _place_image(self, img: Image.Image, cw: int, ch: int,
                     bg: Tuple[int,int,int]) -> Image.Image:
        cfg = self.cfg
        iw, ih = img.size

        if cfg.auto_rotate and iw > 0 and ih > 0:
            if (cw >= ch) != (iw >= ih):
                img = img.rotate(90, expand=True)
                iw, ih = img.size

        cell = Image.new("RGB", (cw, ch), bg)

        if cfg.fit_mode == "stretch":
            resized = img.resize((cw, ch), Image.LANCZOS).convert("RGBA")
            cell.paste(resized, (0, 0), resized.split()[3])
            return cell

        s_fit  = min(cw / iw, ch / ih)
        s_fill = max(cw / iw, ch / ih)
        scale  = s_fill if cfg.fit_mode == "fill" else s_fit

        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        img = img.resize((nw, nh), Image.LANCZOS)

        mask = img.split()[3] if img.mode == "RGBA" else None

        if cfg.fit_mode == "fill":
            l = (nw - cw) // 2
            t = (nh - ch) // 2
            img = img.crop((l, t, l + cw, t + ch))
            mask = img.split()[3] if img.mode == "RGBA" else None
            cell.paste(img.convert("RGB"), (0, 0))
        else:
            x = (cw - nw) // 2
            y = (ch - nh) // 2
            cell.paste(img.convert("RGB"), (x, y), mask)

        return cell

    def _draw_cuts(self, page: Image.Image, cols: int, rows: int,
                   cw: int, ch: int, mo: int, mb: int):
        draw = ImageDraw.Draw(page)
        cfg  = self.cfg
        col  = cfg.cut_color
        lw   = max(1, cfg.cut_width_px)
        dash = max(2, cfg.cut_dash)
        pw, ph = page.size

        def solid(x1, y1, x2, y2):
            draw.line([(x1, y1), (x2, y2)], fill=col, width=lw)

        def dashed(x1, y1, x2, y2):
            if x1 == x2:
                y, on = y1, True
                while y <= y2:
                    if on: draw.line([(x1, y), (x2, min(y+dash, y2))], fill=col, width=lw)
                    y += dash; on = not on
            else:
                x, on = x1, True
                while x <= x2:
                    if on: draw.line([(x, y1), (min(x+dash, x2), y2)], fill=col, width=lw)
                    x += dash; on = not on

        def dotted(x1, y1, x2, y2):
            r = max(1, lw)
            gap = r * 4
            if x1 == x2:
                y = y1
                while y <= y2:
                    draw.ellipse([(x1-r, y-r), (x1+r, y+r)], fill=col)
                    y += gap
            else:
                x = x1
                while x <= x2:
                    draw.ellipse([(x-r, y1-r), (x+r, y1+r)], fill=col)
                    x += gap

        fn = {"Sólida": solid, "Tracejada": dashed, "Pontilhada": dotted}.get(
            cfg.cut_style, solid)

        for c in range(1, cols):
            x = mo + c * cw + (c-1) * mb + mb // 2 if mb > 0 else mo + c * cw
            fn(x, 0, x, ph)

        for r in range(1, rows):
            y = mo + r * ch + (r-1) * mb + mb // 2 if mb > 0 else mo + r * ch
            fn(0, y, pw, y)

    def compose_page(self, page_idx: int, image_paths: List[str],
                     override_dpi: Optional[int] = None) -> Image.Image:
        cfg  = self.cfg
        orig_dpi = cfg.dpi
        if override_dpi:
            cfg.dpi = override_dpi

        cols, rows = self._grid()
        nup        = cols * rows
        pw, ph     = self._page_px()
        mo         = self._mm_px(cfg.margin_outer_mm)
        mb         = self._mm_px(cfg.margin_between_mm)

        cw = max(1, (pw - 2*mo - (cols-1)*mb) // cols)
        ch = max(1, (ph - 2*mo - (rows-1)*mb) // rows)

        bg  = self._hex_rgb(cfg.bg_color)
        page = Image.new("RGB", (pw, ph), bg)

        start = page_idx * nup
        for slot in range(nup):
            idx = start + slot
            if idx >= len(image_paths): break

            col = slot % cols
            row = slot // cols
            x   = mo + col * (cw + mb)
            y   = mo + row * (ch + mb)

            try:
                img  = Image.open(image_paths[idx]).convert("RGBA")
                cell = self._place_image(img, cw, ch, bg)
            except Exception:
                cell = Image.new("RGB", (cw, ch), (200, 190, 190))
                d = ImageDraw.Draw(cell)
                d.text((4, ch//2 - 8), "⚠ Erro ao carregar", fill=(160, 30, 30))

            page.paste(cell, (x, y))

        if cfg.cut_lines:
            self._draw_cuts(page, cols, rows, cw, ch, mo, mb)

        if override_dpi:
            cfg.dpi = orig_dpi

        return page

    def generate_all(self, progress_cb=None) -> List[Image.Image]:
        paths = self._expand()
        cols, rows = self._grid()
        n_pages = max(1, math.ceil(len(paths) / (cols*rows)))
        pages   = []
        for i in range(n_pages):
            pages.append(self.compose_page(i, paths))
            if progress_cb:
                progress_cb(i+1, n_pages)
        return pages

    def preview_page(self, page_idx: int) -> Image.Image:
        paths   = self._expand()
        preview = self.compose_page(page_idx, paths, override_dpi=72)
        preview.thumbnail(PREVIEW_MAX, Image.LANCZOS)
        return preview

    def save(self, pages: List[Image.Image], progress_cb=None) -> List[str]:
        cfg = self.cfg
        out_dir = cfg.output_dir or str(Path.home() / "Desktop")
        os.makedirs(out_dir, exist_ok=True)

        fmt    = cfg.output_format
        ext    = {"PDF":"pdf","PNG":"png","JPEG":"jpg","TIFF":"tif"}[fmt]
        saved  = []

        def unique_path(template: str) -> str:
            p = os.path.join(out_dir, template)
            if not os.path.exists(p): return p
            base, ext_ = os.path.splitext(template)
            i = 2
            while True:
                candidate = os.path.join(out_dir, f"{base}_{i}{ext_}")
                if not os.path.exists(candidate): return candidate
                i += 1

        if fmt == "PDF":
            fname = f"{cfg.output_prefix}001{cfg.output_suffix}.pdf"
            fpath = unique_path(fname)
            if len(pages) == 1:
                pages[0].save(fpath, "PDF", resolution=cfg.dpi)
            else:
                pages[0].save(fpath, "PDF", resolution=cfg.dpi,
                              save_all=True, append_images=pages[1:])
            saved.append(fpath)
            if progress_cb:
                progress_cb(1, 1)
        else:
            for i, page in enumerate(pages):
                fname = f"{cfg.output_prefix}{i+1:03d}{cfg.output_suffix}.{ext}"
                fpath = unique_path(fname)
                if fmt == "JPEG":
                    page.convert("RGB").save(fpath, "JPEG", quality=95, dpi=(cfg.dpi, cfg.dpi))
                elif fmt == "TIFF":
                    page.save(fpath, "TIFF", dpi=(cfg.dpi, cfg.dpi), compression="lzw")
                else:
                    page.save(fpath, "PNG", dpi=(cfg.dpi, cfg.dpi))
                saved.append(fpath)
                if progress_cb:
                    progress_cb(i+1, len(pages))
        return saved


# ══════════════════════════════════════════════════════════════════════════════
# WIDGET: LINHA DE IMAGEM
# ══════════════════════════════════════════════════════════════════════════════

class ImageRow(ctk.CTkFrame):
    """Uma linha na lista de imagens com thumbnail, nome, quantidade e botões."""

    def __init__(self, master, entry: ImageEntry, idx: int,
                 on_remove, on_change, on_move_up, on_move_down, **kw):
        super().__init__(master, fg_color=("gray85","#2a2a3a"), corner_radius=6, **kw)
        self.entry       = entry
        self.idx         = idx
        self.on_remove   = on_remove
        self.on_change   = on_change
        self.on_move_up  = on_move_up
        self.on_move_down = on_move_down

        self._build()

    def _build(self):
        self.columnconfigure(2, weight=1)

        # Thumbnail
        self.tk_img = None
        if self.entry.pil_thumb:
            self.tk_img = ImageTk.PhotoImage(self.entry.pil_thumb)
            lbl_img = ctk.CTkLabel(self, image=self.tk_img, text="")
        else:
            lbl_img = ctk.CTkLabel(self, text="🖼", font=ctk.CTkFont(size=22))
        lbl_img.grid(row=0, column=0, rowspan=2, padx=(6, 4), pady=4)

        # Nome truncado
        name = self.entry.filename
        if len(name) > 28: name = name[:25] + "…"
        ctk.CTkLabel(self, text=name, anchor="w",
                     font=ctk.CTkFont(size=11)).grid(
            row=0, column=2, sticky="w", padx=2)

        # Quantidade
        qty_frame = ctk.CTkFrame(self, fg_color="transparent")
        qty_frame.grid(row=1, column=2, sticky="w", padx=2)

        ctk.CTkLabel(qty_frame, text="Qtd:", font=ctk.CTkFont(size=10)).pack(side="left")
        self.qty_var = tk.StringVar(value=str(self.entry.quantity))
        spin = ctk.CTkEntry(qty_frame, textvariable=self.qty_var, width=40,
                            font=ctk.CTkFont(size=11), justify="center")
        spin.pack(side="left", padx=2)
        spin.bind("<FocusOut>", self._qty_changed)
        spin.bind("<Return>",   self._qty_changed)

        ctk.CTkButton(qty_frame, text="+", width=22, height=22,
                      command=self._qty_up).pack(side="left")
        ctk.CTkButton(qty_frame, text="−", width=22, height=22,
                      command=self._qty_down).pack(side="left", padx=(1,0))

        # Botões direita
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=3, rowspan=2, padx=(4,4))

        ctk.CTkButton(btn_frame, text="↑", width=26, height=22,
                      command=lambda: self.on_move_up(self.idx)).pack(pady=(0,2))
        ctk.CTkButton(btn_frame, text="↓", width=26, height=22,
                      command=lambda: self.on_move_down(self.idx)).pack(pady=(0,2))
        ctk.CTkButton(btn_frame, text="✕", width=26, height=22,
                      fg_color="#993333", hover_color="#cc4444",
                      command=lambda: self.on_remove(self.idx)).pack()

    def _qty_changed(self, *_):
        try:
            v = max(1, int(self.qty_var.get()))
        except ValueError:
            v = 1
        self.qty_var.set(str(v))
        self.entry.quantity = v
        self.on_change()

    def _qty_up(self):
        self.entry.quantity += 1
        self.qty_var.set(str(self.entry.quantity))
        self.on_change()

    def _qty_down(self):
        self.entry.quantity = max(1, self.entry.quantity - 1)
        self.qty_var.set(str(self.entry.quantity))
        self.on_change()


# ══════════════════════════════════════════════════════════════════════════════
# PAINEL: LISTA DE IMAGENS
# ══════════════════════════════════════════════════════════════════════════════

class ImageListPanel(ctk.CTkFrame):
    def __init__(self, master, on_change, **kw):
        super().__init__(master, **kw)
        self.on_change = on_change
        self.entries: List[ImageEntry] = []
        self._rows: List[ImageRow] = []
        self._build()

    def _build(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Toolbar
        tb = ctk.CTkFrame(self, fg_color="transparent")
        tb.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,4))

        ctk.CTkLabel(tb, text="📁  Imagens",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(tb, text="+ Adicionar", width=90,
                      command=self._add_images).pack(side="right", padx=2)
        ctk.CTkButton(tb, text="Limpar", width=70, fg_color="#663333",
                      hover_color="#993333",
                      command=self._clear).pack(side="right", padx=2)

        # Info label
        self.info_var = tk.StringVar(value="Nenhuma imagem selecionada")
        ctk.CTkLabel(self, textvariable=self.info_var,
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50","gray60")).grid(
            row=2, column=0, sticky="w", padx=10, pady=(2,6))

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self, label_text="")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=0)
        self.scroll.columnconfigure(0, weight=1)

    def _add_images(self):
        files = filedialog.askopenfilenames(
            title="Selecionar Imagens",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp"),
                ("Todos",   "*.*"),
            ]
        )
        added = 0
        for f in files:
            if Path(f).suffix.lower() in SUPPORTED_EXT:
                self.entries.append(ImageEntry(f))
                added += 1
        if added:
            self._refresh_rows()
            self.on_change()

    def _clear(self):
        if self.entries and messagebox.askyesno("Limpar",
                "Remover todas as imagens da lista?"):
            self.entries.clear()
            self._refresh_rows()
            self.on_change()

    def _remove(self, idx: int):
        if 0 <= idx < len(self.entries):
            self.entries.pop(idx)
            self._refresh_rows()
            self.on_change()

    def _move_up(self, idx: int):
        if idx > 0:
            self.entries[idx-1], self.entries[idx] = \
                self.entries[idx], self.entries[idx-1]
            self._refresh_rows()
            self.on_change()

    def _move_down(self, idx: int):
        if idx < len(self.entries) - 1:
            self.entries[idx+1], self.entries[idx] = \
                self.entries[idx], self.entries[idx+1]
            self._refresh_rows()
            self.on_change()

    def _refresh_rows(self):
        for r in self._rows:
            r.destroy()
        self._rows.clear()

        for i, entry in enumerate(self.entries):
            row = ImageRow(
                self.scroll, entry, i,
                on_remove=self._remove,
                on_change=self.on_change,
                on_move_up=self._move_up,
                on_move_down=self._move_down,
            )
            row.grid(row=i, column=0, sticky="ew", padx=2, pady=2)
            self._rows.append(row)

        total_qty = sum(e.quantity for e in self.entries)
        if self.entries:
            self.info_var.set(
                f"{len(self.entries)} arquivo(s) · "
                f"{total_qty} cópias no total"
            )
        else:
            self.info_var.set("Nenhuma imagem selecionada")


# ══════════════════════════════════════════════════════════════════════════════
# PAINEL: CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════

class ConfigPanel(ctk.CTkFrame):
    """Painel direito com todas as opções de configuração."""

    def __init__(self, master, cfg: LayoutConfig, on_change, **kw):
        super().__init__(master, **kw)
        self.cfg       = cfg
        self.on_change = on_change
        self._build()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _section(self, text: str, row: int) -> ctk.CTkFrame:
        ctk.CTkLabel(self, text=text,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=row, column=0, columnspan=2,
                                      sticky="w", padx=10, pady=(10,2))
        sep = ctk.CTkFrame(self, height=1, fg_color=("gray70","gray35"))
        sep.grid(row=row+1, column=0, columnspan=2, sticky="ew", padx=10)
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=row+2, column=0, columnspan=2, sticky="ew", padx=10, pady=4)
        f.columnconfigure(1, weight=1)
        return f

    def _lbl(self, parent, text, row, col=0, **kw):
        ctk.CTkLabel(parent, text=text, anchor="w",
                     font=ctk.CTkFont(size=11), **kw).grid(
            row=row, column=col, sticky="w", padx=4, pady=2)

    def _entry_mm(self, parent, var, row, col=1) -> ctk.CTkEntry:
        e = ctk.CTkEntry(parent, textvariable=var, width=65,
                         font=ctk.CTkFont(size=11), justify="center")
        e.grid(row=row, column=col, sticky="w", padx=4, pady=2)
        return e

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        r = 0

        # ── LAYOUT ──
        f = self._section("📐  Layout de Impressão", r); r += 3
        f.columnconfigure(1, weight=1)

        self._lbl(f, "N-up:", 0)
        self._nup_var = tk.StringVar(value=self.cfg.nup_key)
        ctk.CTkOptionMenu(f, variable=self._nup_var,
                          values=list(NUP_LAYOUTS.keys()),
                          command=self._on_nup,
                          width=160).grid(row=0, column=1, sticky="w", padx=4)

        self._lbl(f, "Ajuste:", 1)
        self._fit_var = tk.StringVar(value=FIT_LABELS[FIT_KEYS.index(self.cfg.fit_mode)])
        ctk.CTkOptionMenu(f, variable=self._fit_var,
                          values=FIT_LABELS,
                          command=self._on_fit,
                          width=160).grid(row=1, column=1, sticky="w", padx=4)

        self._auto_var = tk.BooleanVar(value=self.cfg.auto_rotate)
        ctk.CTkCheckBox(f, text="Auto-Rotate (girar se necessário)",
                        variable=self._auto_var,
                        command=self._on_auto).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=4, pady=2)

        # ── PAPEL ──
        f2 = self._section("📄  Papel e Resolução", r); r += 3
        f2.columnconfigure(1, weight=1)

        self._lbl(f2, "Papel:", 0)
        self._paper_var = tk.StringVar(value=self.cfg.paper_key)
        ctk.CTkOptionMenu(f2, variable=self._paper_var,
                          values=list(PAPER_SIZES.keys()),
                          command=self._on_paper,
                          width=120).grid(row=0, column=1, sticky="w", padx=4)

        self._lbl(f2, "Largura (mm):", 1)
        self._pw_var = tk.StringVar(value=str(self.cfg.paper_w_mm))
        self._pw_entry = ctk.CTkEntry(f2, textvariable=self._pw_var, width=65,
                                      font=ctk.CTkFont(size=11), justify="center")
        self._pw_entry.grid(row=1, column=1, sticky="w", padx=4)
        self._pw_entry.bind("<FocusOut>", lambda e: self._on_paper_dim())

        self._lbl(f2, "Altura (mm):", 2)
        self._ph_var = tk.StringVar(value=str(self.cfg.paper_h_mm))
        self._ph_entry = ctk.CTkEntry(f2, textvariable=self._ph_var, width=65,
                                      font=ctk.CTkFont(size=11), justify="center")
        self._ph_entry.grid(row=2, column=1, sticky="w", padx=4)
        self._ph_entry.bind("<FocusOut>", lambda e: self._on_paper_dim())

        self._lbl(f2, "DPI:", 3)
        self._dpi_var = tk.StringVar(value=str(self.cfg.dpi))
        dpi_entry = ctk.CTkEntry(f2, textvariable=self._dpi_var, width=65,
                                  font=ctk.CTkFont(size=11), justify="center")
        dpi_entry.grid(row=3, column=1, sticky="w", padx=4)
        dpi_entry.bind("<FocusOut>", lambda e: self._on_dpi())

        # ── MARGENS ──
        f3 = self._section("📏  Margens e Espaçamento", r); r += 3
        f3.columnconfigure(1, weight=1)

        self._lbl(f3, "Margem ext. (mm):", 0)
        self._mo_var = tk.StringVar(value=str(self.cfg.margin_outer_mm))
        e1 = self._entry_mm(f3, self._mo_var, 0)
        e1.bind("<FocusOut>", lambda _: self._on_margins())
        e1.bind("<Return>",   lambda _: self._on_margins())

        self._lbl(f3, "Entre imagens (mm):", 1)
        self._mb_var = tk.StringVar(value=str(self.cfg.margin_between_mm))
        e2 = self._entry_mm(f3, self._mb_var, 1)
        e2.bind("<FocusOut>", lambda _: self._on_margins())
        e2.bind("<Return>",   lambda _: self._on_margins())

        self._lbl(f3, "Cor de fundo:", 2)
        self._bg_btn = ctk.CTkButton(f3, text="       ", width=65,
                                      fg_color=self.cfg.bg_color,
                                      command=self._pick_bg)
        self._bg_btn.grid(row=2, column=1, sticky="w", padx=4, pady=2)

        # ── LINHAS DE CORTE ──
        f4 = self._section("✂️   Linhas de Corte", r); r += 3
        f4.columnconfigure(1, weight=1)

        self._cuts_var = tk.BooleanVar(value=self.cfg.cut_lines)
        ctk.CTkCheckBox(f4, text="Habilitar linhas de corte",
                        variable=self._cuts_var,
                        command=self._on_cuts).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=4, pady=2)

        self._lbl(f4, "Estilo:", 1)
        self._cut_style_var = tk.StringVar(value=self.cfg.cut_style)
        ctk.CTkOptionMenu(f4, variable=self._cut_style_var,
                          values=LINE_STYLES,
                          command=lambda _: self._on_cut_opts(),
                          width=120).grid(row=1, column=1, sticky="w", padx=4)

        self._lbl(f4, "Espessura (px):", 2)
        self._cut_w_var = tk.StringVar(value=str(self.cfg.cut_width_px))
        ew = ctk.CTkEntry(f4, textvariable=self._cut_w_var, width=65,
                          font=ctk.CTkFont(size=11), justify="center")
        ew.grid(row=2, column=1, sticky="w", padx=4)
        ew.bind("<FocusOut>", lambda _: self._on_cut_opts())

        self._lbl(f4, "Comprimento traço:", 3)
        self._cut_dash_var = tk.StringVar(value=str(self.cfg.cut_dash))
        ed = ctk.CTkEntry(f4, textvariable=self._cut_dash_var, width=65,
                          font=ctk.CTkFont(size=11), justify="center")
        ed.grid(row=3, column=1, sticky="w", padx=4)
        ed.bind("<FocusOut>", lambda _: self._on_cut_opts())

        self._lbl(f4, "Cor da linha:", 4)
        self._cut_col_btn = ctk.CTkButton(f4, text="       ", width=65,
                                           fg_color=self.cfg.cut_color,
                                           command=self._pick_cut_color)
        self._cut_col_btn.grid(row=4, column=1, sticky="w", padx=4, pady=2)

        # ── SAÍDA ──
        f5 = self._section("💾  Saída", r); r += 3
        f5.columnconfigure(1, weight=1)

        self._lbl(f5, "Formato:", 0)
        self._fmt_var = tk.StringVar(value=self.cfg.output_format)
        ctk.CTkOptionMenu(f5, variable=self._fmt_var,
                          values=OUT_FORMATS,
                          command=lambda _: self._on_output(),
                          width=100).grid(row=0, column=1, sticky="w", padx=4)

        self._lbl(f5, "Prefixo:", 1)
        self._pfx_var = tk.StringVar(value=self.cfg.output_prefix)
        ep = ctk.CTkEntry(f5, textvariable=self._pfx_var, width=130,
                          font=ctk.CTkFont(size=11))
        ep.grid(row=1, column=1, sticky="w", padx=4)
        ep.bind("<FocusOut>", lambda _: self._on_output())

        self._lbl(f5, "Sufixo:", 2)
        self._sfx_var = tk.StringVar(value=self.cfg.output_suffix)
        es = ctk.CTkEntry(f5, textvariable=self._sfx_var, width=130,
                          font=ctk.CTkFont(size=11))
        es.grid(row=2, column=1, sticky="w", padx=4)
        es.bind("<FocusOut>", lambda _: self._on_output())

        self._lbl(f5, "Pasta:", 3)
        dir_row = ctk.CTkFrame(f5, fg_color="transparent")
        dir_row.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
        dir_row.columnconfigure(0, weight=1)

        self._dir_var = tk.StringVar(value=self.cfg.output_dir)
        ctk.CTkEntry(dir_row, textvariable=self._dir_var, width=180,
                     font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(dir_row, text="…", width=30,
                      command=self._pick_dir).grid(row=0, column=1, padx=(4,0))

        # Preview info
        self._sheet_info_var = tk.StringVar(value="")
        ctk.CTkLabel(self, textvariable=self._sheet_info_var,
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50","gray60")).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=12, pady=4)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_nup(self, v):
        self.cfg.nup_key = v
        self.on_change()

    def _on_fit(self, v):
        self.cfg.fit_mode = FIT_KEYS[FIT_LABELS.index(v)]
        self.on_change()

    def _on_auto(self):
        self.cfg.auto_rotate = self._auto_var.get()
        self.on_change()

    def _on_paper(self, v):
        self.cfg.paper_key = v
        if v != "Custom" and PAPER_SIZES[v]:
            w, h = PAPER_SIZES[v]
            self.cfg.paper_w_mm = w
            self.cfg.paper_h_mm = h
            self._pw_var.set(str(w))
            self._ph_var.set(str(h))
        self.on_change()

    def _on_paper_dim(self):
        try: self.cfg.paper_w_mm = max(1.0, float(self._pw_var.get()))
        except ValueError: pass
        try: self.cfg.paper_h_mm = max(1.0, float(self._ph_var.get()))
        except ValueError: pass
        self.cfg.paper_key = "Custom"
        self._paper_var.set("Custom")
        self.on_change()

    def _on_dpi(self):
        try: self.cfg.dpi = max(72, min(1200, int(self._dpi_var.get())))
        except ValueError: pass
        self._dpi_var.set(str(self.cfg.dpi))
        self.on_change()

    def _on_margins(self):
        try: self.cfg.margin_outer_mm   = max(0.0, float(self._mo_var.get()))
        except ValueError: pass
        try: self.cfg.margin_between_mm = max(0.0, float(self._mb_var.get()))
        except ValueError: pass
        self.on_change()

    def _pick_bg(self):
        c = colorchooser.askcolor(color=self.cfg.bg_color,
                                  title="Cor de fundo")[1]
        if c:
            self.cfg.bg_color = c
            self._bg_btn.configure(fg_color=c)
            self.on_change()

    def _on_cuts(self):
        self.cfg.cut_lines = self._cuts_var.get()
        self.on_change()

    def _on_cut_opts(self):
        self.cfg.cut_style = self._cut_style_var.get()
        try: self.cfg.cut_width_px = max(1, int(self._cut_w_var.get()))
        except ValueError: pass
        try: self.cfg.cut_dash = max(2, int(self._cut_dash_var.get()))
        except ValueError: pass
        self.on_change()

    def _pick_cut_color(self):
        c = colorchooser.askcolor(color=self.cfg.cut_color,
                                  title="Cor das linhas de corte")[1]
        if c:
            self.cfg.cut_color = c
            self._cut_col_btn.configure(fg_color=c)
            self.on_change()

    def _on_output(self):
        self.cfg.output_format = self._fmt_var.get()
        self.cfg.output_prefix = self._pfx_var.get()
        self.cfg.output_suffix = self._sfx_var.get()
        self.cfg.output_dir    = self._dir_var.get()

    def _pick_dir(self):
        d = filedialog.askdirectory(title="Pasta de saída",
                                    initialdir=self.cfg.output_dir)
        if d:
            self.cfg.output_dir = d
            self._dir_var.set(d)

    def update_sheet_info(self, n_images: int, n_pages: int):
        cols, rows = NUP_LAYOUTS[self.cfg.nup_key]
        nup = cols * rows
        self._sheet_info_var.set(
            f"{n_images} imagem(ns) · {nup} por folha · {n_pages} folha(s)"
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAINEL: PREVIEW
# ══════════════════════════════════════════════════════════════════════════════

class PreviewPanel(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._page_idx  = 0
        self._total     = 0
        self._tk_img    = None
        self._build()

    def _build(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Nav bar
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=0, column=0, sticky="ew", padx=8, pady=(6,2))

        ctk.CTkLabel(nav, text="👁  Preview",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self._nav_lbl = ctk.CTkLabel(nav, text="",
                                      font=ctk.CTkFont(size=11))
        self._nav_lbl.pack(side="left", padx=12)
        ctk.CTkButton(nav, text="▶", width=32, command=self._next).pack(side="right")
        ctk.CTkButton(nav, text="◀", width=32, command=self._prev).pack(side="right", padx=4)

        # Canvas
        self._canvas = tk.Canvas(self, bg="#1a1a2a", highlightthickness=0,
                                  width=PREVIEW_MAX[0], height=PREVIEW_MAX[1])
        self._canvas.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,6))

        self._canvas.create_text(PREVIEW_MAX[0]//2, PREVIEW_MAX[1]//2,
                                  text="Adicione imagens para ver o preview",
                                  fill="#555577", font=("Helvetica", 11),
                                  tags="placeholder")

    def update_preview(self, img: Optional[Image.Image], page_idx: int, total: int):
        self._page_idx = page_idx
        self._total    = total
        self._nav_lbl.configure(
            text=f"Folha {page_idx+1} / {total}" if total > 0 else "Sem folhas")

        self._canvas.delete("all")
        if img is None:
            self._canvas.create_text(PREVIEW_MAX[0]//2, PREVIEW_MAX[1]//2,
                                      text="Nenhuma imagem para exibir",
                                      fill="#555577", font=("Helvetica", 11))
            return

        # Center image on canvas
        cw = self._canvas.winfo_width()  or PREVIEW_MAX[0]
        ch = self._canvas.winfo_height() or PREVIEW_MAX[1]

        self._tk_img = ImageTk.PhotoImage(img)
        x = (cw - img.width)  // 2
        y = (ch - img.height) // 2

        # Shadow
        self._canvas.create_rectangle(x+4, y+4, x+img.width+4, y+img.height+4,
                                       fill="#000000", outline="")
        self._canvas.create_image(x, y, anchor="nw", image=self._tk_img)

    def _prev(self):
        self._canvas.event_generate("<<PreviewPrev>>")

    def _next(self):
        self._canvas.event_generate("<<PreviewNext>>")

    @property
    def canvas(self):
        return self._canvas


# ══════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class PrintImposerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1100x780")
        self.minsize(900, 650)

        self.cfg          = LayoutConfig()
        self._preview_idx = 0
        self._preview_job = None
        self._generating  = False

        self._build_ui()
        self._on_change()

    def _build_ui(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self, height=44, corner_radius=0,
                               fg_color=("gray80","#12121e"))
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(header,
                     text=f"🖨  {APP_NAME}  —  Imposição de Páginas para Impressão",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
            side="left", padx=14, pady=8)
        ctk.CTkLabel(header, text=f"v{VERSION}",
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50","gray50")).pack(side="right", padx=14)

        # ── Main PanedWindow ──
        pane = tk.PanedWindow(self, orient="horizontal", sashwidth=5,
                              bg="#2a2a3a", sashrelief="flat")
        pane.grid(row=1, column=0, sticky="nsew", pady=(0,0))

        # Scrollable list — use a plain tk.Frame wrapper for PanedWindow compat
        list_tk_outer = tk.Frame(pane, bg="#2a2a3a")
        list_tk_outer.rowconfigure(0, weight=1)
        list_tk_outer.columnconfigure(0, weight=1)

        self.img_panel = ImageListPanel(list_tk_outer, on_change=self._on_change)
        self.img_panel.grid(row=0, column=0, sticky="nsew")
        pane.add(list_tk_outer, minsize=280, width=320)

        # Center+Right: Config + Preview
        right_pane = tk.PanedWindow(pane, orient="horizontal", sashwidth=5,
                                     bg="#2a2a3a")
        pane.add(right_pane, minsize=580)

        # Config panel — wrap in a plain tk.Frame so PanedWindow accepts it
        cfg_tk_outer = tk.Frame(right_pane, bg="#2a2a3a")
        cfg_tk_outer.rowconfigure(0, weight=1)
        cfg_tk_outer.columnconfigure(0, weight=1)

        cfg_scroll = ctk.CTkScrollableFrame(cfg_tk_outer, width=320)
        cfg_scroll.grid(row=0, column=0, sticky="nsew")

        self.cfg_panel = ConfigPanel(cfg_scroll, self.cfg, on_change=self._on_change)
        self.cfg_panel.pack(fill="both", expand=True)
        right_pane.add(cfg_tk_outer, minsize=300, width=340)

        # Preview panel — wrap in plain tk.Frame
        preview_tk_outer = tk.Frame(right_pane, bg="#2a2a3a")
        preview_tk_outer.rowconfigure(0, weight=1)
        preview_tk_outer.columnconfigure(0, weight=1)

        self.preview_panel = PreviewPanel(preview_tk_outer)
        self.preview_panel.grid(row=0, column=0, sticky="nsew")
        right_pane.add(preview_tk_outer, minsize=280)

        # Bind preview nav
        self.preview_panel.canvas.bind("<<PreviewPrev>>",
                                        lambda _: self._nav_preview(-1))
        self.preview_panel.canvas.bind("<<PreviewNext>>",
                                        lambda _: self._nav_preview(+1))

        # ── Bottom Bar ──
        bottom = ctk.CTkFrame(self, height=54, corner_radius=0,
                               fg_color=("gray80","#12121e"))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(1, weight=1)

        self._gen_btn = ctk.CTkButton(
            bottom, text="⚡  Gerar Arquivos",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36, width=180,
            command=self._start_generate
        )
        self._gen_btn.grid(row=0, column=0, padx=12, pady=9)

        self._prog_var = tk.DoubleVar(value=0)
        self._prog_bar = ctk.CTkProgressBar(bottom, variable=self._prog_var,
                                             height=12)
        self._prog_bar.grid(row=0, column=1, sticky="ew", padx=8)

        self._status_var = tk.StringVar(value="Pronto")
        ctk.CTkLabel(bottom, textvariable=self._status_var,
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50","gray60")).grid(
            row=0, column=2, padx=12)

    # ── Change Handler ────────────────────────────────────────────────────────

    def _on_change(self):
        """Called whenever any setting or image list changes."""
        entries = self.img_panel.entries

        engine = ImpositionEngine(entries, self.cfg)
        n_exp  = engine.total_expanded()
        n_pgs  = engine.total_pages()

        self.cfg_panel.update_sheet_info(n_exp, n_pgs)

        # Clamp preview index
        if n_pgs > 0:
            self._preview_idx = max(0, min(self._preview_idx, n_pgs - 1))

        # Schedule preview refresh (debounce)
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(300, self._refresh_preview)

    def _refresh_preview(self):
        self._preview_job = None
        entries = self.img_panel.entries

        if not entries:
            self.preview_panel.update_preview(None, 0, 0)
            return

        engine  = ImpositionEngine(entries, self.cfg)
        n_pages = engine.total_pages()

        if n_pages == 0:
            self.preview_panel.update_preview(None, 0, 0)
            return

        def task():
            try:
                img = engine.preview_page(self._preview_idx)
                self.after(0, lambda: self.preview_panel.update_preview(
                    img, self._preview_idx, n_pages))
            except Exception as e:
                self.after(0, lambda: self._status_var.set(f"Preview error: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def _nav_preview(self, delta: int):
        entries = self.img_panel.entries
        if not entries: return
        engine  = ImpositionEngine(entries, self.cfg)
        n_pages = engine.total_pages()
        self._preview_idx = (self._preview_idx + delta) % max(1, n_pages)
        self._refresh_preview()

    # ── Generate ──────────────────────────────────────────────────────────────

    def _start_generate(self):
        if self._generating:
            return
        entries = self.img_panel.entries
        if not entries:
            messagebox.showwarning("Sem imagens",
                                   "Adicione pelo menos uma imagem antes de gerar.")
            return

        # Read latest output settings
        self.cfg_panel._on_output()

        if not self.cfg.output_dir:
            self.cfg.output_dir = str(Path.home() / "Desktop")

        self._generating = True
        self._gen_btn.configure(state="disabled", text="⏳ Gerando…")
        self._prog_var.set(0)
        self._status_var.set("Iniciando geração…")

        threading.Thread(target=self._generate_worker, daemon=True).start()

    def _generate_worker(self):
        try:
            entries = self.img_panel.entries
            engine  = ImpositionEngine(entries, self.cfg)
            n_pages = engine.total_pages()

            pages = []

            def prog_compose(done, total):
                pct = (done / total) * 0.7
                self.after(0, lambda: self._prog_var.set(pct))
                self.after(0, lambda: self._status_var.set(
                    f"Compondo folha {done}/{total}…"))

            pages = engine.generate_all(progress_cb=prog_compose)

            self.after(0, lambda: self._status_var.set("Salvando arquivos…"))

            def prog_save(done, total):
                pct = 0.7 + (done / total) * 0.3
                self.after(0, lambda: self._prog_var.set(pct))

            saved = engine.save(pages, progress_cb=prog_save)

            self.after(0, lambda: self._on_generate_done(saved))

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.after(0, lambda: self._on_generate_error(str(e), tb))

    def _on_generate_done(self, saved: List[str]):
        self._generating = False
        self._gen_btn.configure(state="normal", text="⚡  Gerar Arquivos")
        self._prog_var.set(1.0)

        n = len(saved)
        folder = str(Path(saved[0]).parent) if saved else ""
        self._status_var.set(f"✅ {n} arquivo(s) salvo(s) em {folder}")

        msg = f"{n} arquivo(s) gerado(s) com sucesso!\n\nPasta:\n{folder}"
        if messagebox.askyesno("Concluído!", msg + "\n\nAbrir a pasta?"):
            self._open_folder(folder)

    def _on_generate_error(self, err: str, tb: str):
        self._generating = False
        self._gen_btn.configure(state="normal", text="⚡  Gerar Arquivos")
        self._prog_var.set(0)
        self._status_var.set(f"❌ Erro: {err}")
        messagebox.showerror("Erro ao gerar",
                              f"Ocorreu um erro durante a geração:\n\n{err}\n\n{tb[:400]}")

    @staticmethod
    def _open_folder(path: str):
        import subprocess, platform
        s = platform.system()
        try:
            if s == "Windows":
                os.startfile(path)
            elif s == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    app = PrintImposerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
