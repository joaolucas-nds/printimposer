#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrintImposer v1.9.1
Ferramenta de Imposição de Páginas para Impressão em Massa

Selecione imagens, configure o layout e gere PDFs/PNGs prontos para impressão.

Novidades da 1.1 (fase F2 do ROADMAP):
  - Grade livre colunas x linhas (DEC-009) — qualquer combinação sem editar código
  - Persistência de configuração e presets nomeados em ~/.printimposer/
  - Janela centralizada, com clamp ao monitor e DPI awareness no Windows
  - Pastas de entrada e saída independentes; até dois destinos simultâneos
  - Entrada SVG (dependência opcional, antecipada da F3)
  - Guarda de qualidade: avisa quando a imagem-fonte é menor que a célula
  - Gerador de .bat para abrir a GUI sem console

Novidades da 1.2 (fase F3 do ROADMAP, SPEC-F3-UI):
  - Menubar Arquivo / Opções / Ajuda; presets e atalho .bat saíram do painel
  - Painel de configuração em três zonas: grade fixa, accordion, resumo fixo
  - Seções abertas/fechadas lembradas entre sessões (`sections_open`)

Novidades da 1.3 (fase F4, etapa 1 — SPEC-F4-etapa1):
  - PDF sem perda por padrão: escritor próprio embute o fluxo do PNG (DEC-014)
  - Compressão escolhível: PDF sem perda/JPEG e qualidade JPEG de 50 a 100
  - Espaçamento independente entre colunas e entre linhas
  - Rodapé mostra o tamanho da folha em px e o tamanho bruto em MB
  - Entrada AVIF (nativa do Pillow) e HEIC/HEIF (com `pillow-heif`, opcional)

Novidades da 1.4 (fase F4, etapa 2 — SPEC-F4-etapa2):
  - Entrada PDF via `pypdfium2` (opcional): cada página vira um item da lista
  - A página é rasterizada no tamanho da célula, já na orientação final
    (sem ampliação depois do render); PDF ilegível é pulado com aviso

Novidades da 1.4.1 (robustez):
  - Erro ao abrir o app grava ~/.printimposer/last_error.log e mostra uma
    janela, mesmo com o atalho .bat (que não tem console)
  - Barra inferior avisa quando o segundo destino está ligado (âmbar se a
    pasta não existe ou é temporária)
  - A geração trabalha sobre cópias da configuração e da lista: mexer nelas
    durante uma geração longa não mistura folhas
  - Guia rápido sem amarrar a uma ferramenta de design

Novidades da 1.5.0:
  - Saída WebP (sem perda ou com perda) e AVIF, para compartilhar
  - A guarda de qualidade olha as imagens embutidas nas páginas de PDF
  - SVG rasterizado já na orientação final e respeitando o modo de ajuste
    (antes saía ampliado com Auto-Rotate e no modo Preencher)

Novidades da 1.6 (fase F4, etapa 4 — SPEC-F4-etapa4):
  - Marcas de canto na margem externa, uma por ponta de cada linha de corte
  - Sangria em mm, em dois modos: estender a borda (espelhar) ou a arte já
    traz a sangria; limitada ao espaço entre as células
  - Avisos (margem curta para as marcas, espaçamento menor que 2× a sangria)
    e confirmação antes de gerar
  - Seção «Linhas de corte» virou «Corte e sangria»; `cut_lines` virou
    `cut_guide` (config e presets antigos continuam abrindo)
  - Geometria de corte calculada em mm (`sheet_geometry`), separada do desenho

Novidades da 1.7 (fase F5, etapa 1 — SPEC-F5-arrastar):
  - Soltar arquivos e pastas em qualquer ponto da janela (`tkinterdnd2`,
    opcional — DEC-016); passa pelo mesmo funil do «+ Arquivos»
  - Reordenar a lista arrastando pela alça «≡» (Tk puro, sem dependência)
  - Aviso âmbar quando a margem externa é menor que a sangria
  - Cabeçalho e «Sobre» mostram o estado do arrastar

Novidades da 1.8 (fase F5, etapa 2 — SPEC-F5-tiragem):
  - Rotação por item (botão «⟳»): 0° segue o Auto-Rotate; 90/180/270° são
    exatos, com a fonte vetorial rasterizada já na orientação final
  - «Preencher»: completar a última folha ou exatamente N folhas, mexendo
    nas quantidades à vista

Novidades da 1.8.1: o nucleo sem Tk foi para imposer_core.py (DEC-017); nada muda para quem usa.

Novidades da 1.9 (fase F5, etapa 3 — SPEC-F5-moldura):
  - Seletor «Layout»: Grade ou uma moldura (1 + 2, 2 + 1, 1 + 3, Destaque + 4,
    1 + 2 + 1) com células de tamanhos diferentes na mesma folha (DEC-018)
  - Uma «Proporção (%)» por moldura; as imagens entram nos espaços em ordem
  - Corte, marcas de canto, sangria e guarda de qualidade por espaço

Novidades da 1.9.1: o modo Preencher não deixa mais uma linha preta de 1 px na borda da célula (FIX-007).
"""

import os
import sys
import tempfile
import threading
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog

import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

from PIL import Image, ImageTk

# O motor mora em imposer_core.py (DEC-017). O `*` não traz nomes com `_`; a GUI
# não usa nenhum direto (os testes importam os seus de `imposer_core`).
import imposer_core as core
from imposer_core import *  # noqa: F401,F403


# ══════════════════════════════════════════════════════════════════════════════
# SUPORTE OPCIONAL A ARRASTAR E SOLTAR (DEC-016)
# ══════════════════════════════════════════════════════════════════════════════
# `tkinterdnd2` embrulha o tkDnD. Aqui só dá para saber se o PACOTE importa; a
# capacidade de verdade (FIX-002) só é provada com a janela criada, quando
# `TkinterDnD._require(self)` devolve uma versão — ver PrintImposerApp.__init__.
# Sem o pacote a janela herda só de `ctk.CTk` e o app é igual à 1.6.0.

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES  # type: ignore
    _DnDBase = TkinterDnD.DnDWrapper
    DND_PKG_OK: bool = True
except Exception:
    TkinterDnD = None
    DND_FILES = "DND_Files"
    _DnDBase = object
    DND_PKG_OK = False



# ══════════════════════════════════════════════════════════════════════════════
# WIDGET: MINIATURA DA GRADE
# ══════════════════════════════════════════════════════════════════════════════

class GridPreview(tk.Canvas):
    """Mini-diagrama da grade — para identificar o layout de relance."""

    def __init__(self, master, w=70, h=92, **kw):
        super().__init__(master, width=w, height=h, highlightthickness=0,
                         bg="#1f1f2e", **kw)
        # ATENÇÃO: nunca use self._w / self._h aqui. Em tkinter.Misc, `_w` guarda
        # o pathname Tcl do widget ('.!canvas'); sobrescrever quebra TODA chamada
        # ao Tk com «invalid command name». Prefixo `_box_` evita a colisão. Ver FIX-003.
        self._box_w, self._box_h = w, h
        self.draw(2, 2)

    def draw(self, cols: int, rows: int):
        self.delete("all")
        cols = max(1, cols); rows = max(1, rows)
        pad = 5
        iw = self._box_w - 2 * pad
        ih = self._box_h - 2 * pad

        self.create_rectangle(pad, pad, pad + iw, pad + ih,
                              outline="#6b7ba8", fill="#2b2b3d")

        cw = iw / cols
        ch = ih / rows
        for c in range(1, cols):
            x = pad + c * cw
            self.create_line(x, pad, x, pad + ih, fill="#6b7ba8")
        for r in range(1, rows):
            y = pad + r * ch
            self.create_line(pad, y, pad + iw, y, fill="#6b7ba8")

        # Rótulo só cabe enquanto as células não ficam minúsculas.
        if cw > 13 and ch > 11:
            for c in range(cols):
                for r in range(rows):
                    self.create_text(pad + c * cw + cw / 2, pad + r * ch + ch / 2,
                                     text=str(r * cols + c + 1),
                                     fill="#8f9ec4", font=("Helvetica", 7))

    def draw_frame(self, cells):
        """Desenha uma moldura: `cells` são retângulos em fração da área (0–1),
        numerados na ordem de leitura (a ordem em que as imagens entram)."""
        self.delete("all")
        pad = 5
        iw = self._box_w - 2 * pad
        ih = self._box_h - 2 * pad
        self.create_rectangle(pad, pad, pad + iw, pad + ih,
                              outline="#6b7ba8", fill="#2b2b3d")
        for n, (x0, y0, x1, y1) in enumerate(cells, start=1):
            X0, Y0 = pad + x0 * iw, pad + y0 * ih
            X1, Y1 = pad + x1 * iw, pad + y1 * ih
            self.create_rectangle(X0, Y0, X1, Y1, outline="#6b7ba8")
            if X1 - X0 > 13 and Y1 - Y0 > 11:
                self.create_text((X0 + X1) / 2, (Y0 + Y1) / 2, text=str(n),
                                 fill="#8f9ec4", font=("Helvetica", 7))


# ══════════════════════════════════════════════════════════════════════════════
# WIDGET: LINHA DE IMAGEM
# ══════════════════════════════════════════════════════════════════════════════

class ImageRow(ctk.CTkFrame):
    """Uma linha na lista: alça, miniatura, nome, quantidade e botões de ação."""

    def __init__(self, master, entry: ImageEntry, idx: int,
                 on_remove, on_change, on_move_up, on_move_down,
                 on_drag_start=None, on_drag_move=None, on_drag_end=None,
                 on_rotate=None, **kw):
        super().__init__(master, fg_color=("gray85", "#2a2a3a"), corner_radius=6, **kw)
        self.entry        = entry
        self.idx          = idx
        self.on_remove    = on_remove
        self.on_change    = on_change
        self.on_move_up   = on_move_up
        self.on_move_down = on_move_down
        self.on_drag_start = on_drag_start
        self.on_drag_move  = on_drag_move
        self.on_drag_end   = on_drag_end
        self.on_rotate     = on_rotate
        self._build()

    def _build(self):
        self.columnconfigure(2, weight=1)

        # Alça de arraste: só ela inicia o arraste, senão o clique no campo «Qtd»
        # viraria arraste. O índice (não o widget) vai no callback: a lista
        # recria as linhas a cada mudança.
        handle = ctk.CTkLabel(self, text="≡", width=16, cursor="fleur",
                              font=ctk.CTkFont(size=16))
        handle.grid(row=0, column=0, rowspan=2, padx=(4, 0))
        handle.bind("<ButtonPress-1>",
                    lambda e: self.on_drag_start and self.on_drag_start(self.idx))
        handle.bind("<B1-Motion>",
                    lambda e: self.on_drag_move and self.on_drag_move(e.x_root, e.y_root))
        handle.bind("<ButtonRelease-1>",
                    lambda e: self.on_drag_end and self.on_drag_end(e.x_root, e.y_root))

        self.tk_img = None
        if self.entry.pil_thumb:
            # CTkImage, não PhotoImage: só ele reescala em telas 125%/150%.
            # Gira a CÓPIA exibida; o cache de miniatura guarda a original.
            thumb = self.entry.pil_thumb
            if self.entry.rotation:
                thumb = thumb.rotate(-self.entry.rotation, expand=True)
            self.tk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb,
                                       size=(THUMB_W, THUMB_H))
            lbl_img = ctk.CTkLabel(self, image=self.tk_img, text="")
        else:
            lbl_img = ctk.CTkLabel(self, text="?", font=ctk.CTkFont(size=22))
        lbl_img.grid(row=0, column=1, rowspan=2, padx=(4, 4), pady=4)

        name = self.entry.filename
        if len(name) > 28:
            name = name[:25] + "…"
        # O sufixo da página fica fora do corte: é ele que distingue os itens.
        name += self.entry.page_label
        tag = "  [SVG]" if is_svg(self.entry.path) else ""
        if self.entry.rotation:
            tag += f"  · {self.entry.rotation}°"
        ctk.CTkLabel(self, text=name + tag, anchor="w",
                     font=ctk.CTkFont(size=11)).grid(row=0, column=2,
                                                     sticky="w", padx=2)

        qty = ctk.CTkFrame(self, fg_color="transparent")
        qty.grid(row=1, column=2, sticky="w", padx=2)
        ctk.CTkLabel(qty, text="Qtd:", font=ctk.CTkFont(size=10)).pack(side="left")

        self.qty_var = tk.StringVar(value=str(self.entry.quantity))
        spin = ctk.CTkEntry(qty, textvariable=self.qty_var, width=40,
                            font=ctk.CTkFont(size=11), justify="center")
        spin.pack(side="left", padx=2)
        spin.bind("<FocusOut>", self._qty_changed)
        spin.bind("<Return>",   self._qty_changed)

        ctk.CTkButton(qty, text="+", width=22, height=22,
                      command=self._qty_up).pack(side="left")
        ctk.CTkButton(qty, text="-", width=22, height=22,
                      command=self._qty_down).pack(side="left", padx=(1, 0))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=0, column=3, rowspan=2, padx=(4, 4))
        ctk.CTkButton(btns, text="▲", width=26, height=22,
                      command=lambda: self.on_move_up(self.idx)).pack(pady=(0, 2))
        ctk.CTkButton(btns, text="▼", width=26, height=22,
                      command=lambda: self.on_move_down(self.idx)).pack(pady=(0, 2))
        self._rot_btn = ctk.CTkButton(
            btns, text="⟳", width=26, height=22,
            command=lambda: self.on_rotate and self.on_rotate(self.idx))
        self._rot_btn.pack(pady=(0, 2))
        ctk.CTkButton(btns, text="✕", width=26, height=22,
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
    def __init__(self, master, cfg: LayoutConfig, on_change,
                 drop_enabled: bool = False, **kw):
        super().__init__(master, **kw)
        self.cfg       = cfg
        self.on_change = on_change
        self.drop_enabled = drop_enabled     # só muda o texto da lista vazia
        self.entries: List[ImageEntry] = []
        self._rows: List[ImageRow] = []
        self._dropping = False               # arraste de arquivos passando pela janela
        self._drag_src: Optional[int] = None  # índice da linha cuja alça foi apertada
        self._drag_dst: Optional[int] = None  # índice da linha sob o ponteiro
        self._build()

    def _build(self):
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        tb = ctk.CTkFrame(self, fg_color="transparent")
        tb.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 2))
        ctk.CTkLabel(tb, text="Imagens",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(tb, text="Limpar", width=62, fg_color="#663333",
                      hover_color="#993333", command=self._clear).pack(side="right", padx=2)

        tb2 = ctk.CTkFrame(self, fg_color="transparent")
        tb2.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 2))
        ctk.CTkButton(tb2, text="+ Arquivos", width=96,
                      command=self._add_files).pack(side="left", padx=(0, 4))
        ctk.CTkButton(tb2, text="+ Pasta", width=80,
                      command=self._add_folder).pack(side="left", padx=(0, 4))
        # Menu do tk puro: o CTk não tem menu suspenso que abra sob o botão.
        self._fill_menu = tk.Menu(self, tearoff=0)
        self._fill_menu.add_command(label="Completar a última folha",
                                    command=self._fill_complete)
        self._fill_menu.add_command(label="Exatamente N folhas…",
                                    command=self._fill_exact)
        self._fill_btn = ctk.CTkButton(tb2, text="Preencher ▾", width=96,
                                       command=self._show_fill_menu)
        self._fill_btn.pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, label_text="")
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=4)
        self.scroll.columnconfigure(0, weight=1)

        self.info_var = tk.StringVar(value=self._info_text())
        ctk.CTkLabel(self, textvariable=self.info_var, font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).grid(
            row=3, column=0, sticky="w", padx=10, pady=(2, 6))

    # ── Ações ────────────────────────────────────────────────────────────────

    def _filetypes(self):
        pats = " ".join("*" + e for e in sorted(SUPPORTED_EXT))
        types = [("Imagens", pats)]
        if SVG_BACKEND:
            types.append(("SVG", "*.svg"))
        if PDF_OK:
            types.append(("PDF", "*.pdf"))
        types.append(("Todos", "*.*"))
        return types

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="Selecionar Imagens",
            initialdir=self.cfg.input_dir or str(Path.home()),
            filetypes=self._filetypes())
        if not files:
            return
        # Lembra só a pasta de ENTRADA — não encosta na pasta de saída.
        self.cfg.input_dir = str(Path(files[0]).parent)
        self._ingest(files)

    def _add_folder(self):
        folder = filedialog.askdirectory(
            title="Adicionar todas as imagens de uma pasta",
            initialdir=self.cfg.input_dir or str(Path.home()))
        if not folder:
            return
        self.cfg.input_dir = folder
        # Ordem natural do nome: é a ordem que o usuário vê no Explorer.
        found = sorted(
            (str(p) for p in Path(folder).iterdir()
             if p.is_file() and p.suffix.lower() in SUPPORTED_EXT),
            key=lambda s: os.path.basename(s).lower())
        if not found:
            messagebox.showinfo("Nada encontrado",
                                "Nenhuma imagem suportada nessa pasta.")
            return
        self._ingest(found)

    def ingest_dropped(self, paths):
        """Entrada do soltar na janela: mesmo funil do «+ Arquivos», sem tocar nas pastas lembradas."""
        files, skipped = expand_dropped(paths)
        if not files and not skipped:
            messagebox.showinfo("Nada encontrado",
                                "Nenhuma imagem suportada no que foi solto.")
            return
        self._ingest(files, pre_skipped=skipped)

    def _ingest(self, paths, pre_skipped=()):
        items, skipped = plan_ingest(
            paths, confirm_many=lambda name, n: messagebox.askyesno(
                "PDF grande", f"Adicionar as {n} páginas de {name}?"))
        skipped = list(pre_skipped) + skipped
        for path, page, total in items:
            self.entries.append(ImageEntry(path, page, total))
        if items:
            self._refresh_rows()
            self.on_change()
        if skipped:
            # Uma mensagem só para o lote inteiro, não uma por arquivo.
            messagebox.showwarning(
                "Arquivos pulados",
                "Não entraram na lista:\n" +
                "\n".join(f"• {n}: {why}" for n, why in skipped))

    def _clear(self):
        if self.entries and messagebox.askyesno(
                "Limpar", "Remover todas as imagens da lista?"):
            self.entries.clear()
            self._refresh_rows()
            self.on_change()

    def _remove(self, idx: int):
        if 0 <= idx < len(self.entries):
            self.entries.pop(idx)
            self._refresh_rows()
            self.on_change()

    def _rotate(self, idx: int):
        """Gira o item 90° no sentido horário: 0 → 90 → 180 → 270 → 0."""
        if 0 <= idx < len(self.entries):
            e = self.entries[idx]
            e.rotation = (e.rotation + 90) % 360
            self._refresh_rows()
            self.on_change()

    # ── Preencher folhas (mexe nas quantidades, à vista) ─────────────────────

    def _show_fill_menu(self):
        x = self._fill_btn.winfo_rootx()
        y = self._fill_btn.winfo_rooty() + self._fill_btn.winfo_height()
        try:
            self._fill_menu.tk_popup(x, y)
        finally:
            self._fill_menu.grab_release()

    def _apply_quantities(self, quantities: List[int]):
        for e, q in zip(self.entries, quantities):
            e.quantity = q
        self._refresh_rows()
        self.on_change()

    def _fill_complete(self):
        if not self.entries:
            messagebox.showinfo("Preencher folhas", "A lista está vazia.")
            return
        qtys = [e.quantity for e in self.entries]
        new = fill_last_sheet(qtys, self.cfg.nup())
        if new == qtys:
            messagebox.showinfo("Preencher folhas", "A última folha já está cheia.")
            return
        self._apply_quantities(new)

    def _fill_exact(self):
        if not self.entries:
            messagebox.showinfo("Preencher folhas", "A lista está vazia.")
            return
        nup = self.cfg.nup()
        n = simpledialog.askinteger(
            "Preencher folhas", f"Quantas folhas? ({nup} por folha)",
            parent=self, minvalue=1, maxvalue=999)
        if n is None:
            return
        items = len(self.entries)
        total = n * nup
        new = fill_n_sheets(items, nup, n)
        if new is None:
            messagebox.showinfo(
                "Preencher folhas",
                f"Em {n} folha(s) de {nup} cabem {total} cópias, "
                f"e a lista tem {items} imagens.")
            return
        if not messagebox.askyesno(
                "Preencher folhas",
                f"Isto troca as quantidades: {items} imagens em {n} folha(s) "
                f"de {nup} = {total} cópias. Continuar?"):
            return
        self._apply_quantities(new)

    # ── Retorno visual do soltar e reordenação pela alça ─────────────────────

    def _info_text(self) -> str:
        if self._dropping:
            return "Solte para adicionar à lista"
        if self.entries:
            total = sum(e.quantity for e in self.entries)
            return f"{len(self.entries)} arquivo(s) · {total} cópias no total"
        if self.drop_enabled:
            return "Nenhuma imagem — arraste arquivos ou pastas para cá"
        return "Nenhuma imagem selecionada"

    def set_drop_highlight(self, on: bool):
        """Acende a moldura da lista enquanto um arraste de arquivos passa pela janela."""
        self._dropping = on
        self.scroll.configure(border_width=2 if on else 0, border_color="#3b8ed0")
        self.info_var.set(self._info_text())

    def _row_at(self, x_root: int, y_root: int) -> Optional[int]:
        """Índice da linha sob o ponteiro (sobe pelos pais até achar uma ImageRow)."""
        try:
            w = self.winfo_containing(x_root, y_root)
        except Exception:
            return None      # o Tk levanta KeyError em alguns popups
        while w is not None:
            if w in self._rows:
                return w.idx
            w = getattr(w, "master", None)
        return None

    def _mark_row(self, idx: Optional[int], on: bool):
        if idx is not None and 0 <= idx < len(self._rows):
            self._rows[idx].configure(border_width=2 if on else 0,
                                      border_color="#3b8ed0")

    def _drag_start(self, idx: int):
        self._drag_src, self._drag_dst = idx, None

    def _drag_move(self, x_root: int, y_root: int):
        if self._drag_src is None:
            return
        dst = self._row_at(x_root, y_root)
        if dst != self._drag_dst:
            self._mark_row(self._drag_dst, False)
            self._drag_dst = dst
            self._mark_row(dst, True)

    def _drag_end(self, x_root: int, y_root: int):
        src, dst = self._drag_src, self._row_at(x_root, y_root)
        self._mark_row(self._drag_dst, False)
        self._drag_src = self._drag_dst = None
        # Soltar fora da lista ou na própria linha não muda nada.
        if src is None or dst is None or dst == src:
            return
        move_item(self.entries, src, dst)
        self._refresh_rows()
        self.on_change()

    def _move_up(self, idx: int):
        if idx > 0:
            self.entries[idx-1], self.entries[idx] = self.entries[idx], self.entries[idx-1]
            self._refresh_rows()
            self.on_change()

    def _move_down(self, idx: int):
        if idx < len(self.entries) - 1:
            self.entries[idx+1], self.entries[idx] = self.entries[idx], self.entries[idx+1]
            self._refresh_rows()
            self.on_change()

    def _refresh_rows(self):
        for r in self._rows:
            r.destroy()
        self._rows.clear()

        for i, entry in enumerate(self.entries):
            row = ImageRow(self.scroll, entry, i,
                           on_remove=self._remove, on_change=self.on_change,
                           on_move_up=self._move_up, on_move_down=self._move_down,
                           on_drag_start=self._drag_start, on_drag_move=self._drag_move,
                           on_drag_end=self._drag_end, on_rotate=self._rotate)
            row.grid(row=i, column=0, sticky="ew", padx=2, pady=2)
            self._rows.append(row)

        self.info_var.set(self._info_text())


# ══════════════════════════════════════════════════════════════════════════════
# WIDGET: SEÇÃO RECOLHÍVEL (accordion)
# ══════════════════════════════════════════════════════════════════════════════

class CollapsibleSection(ctk.CTkFrame):
    """Cabeçalho clicável + corpo que some sem ser destruído.

    Fechar usa `grid_remove()`: os widgets e o estado dos campos continuam
    vivos. Todo atributo privado leva o prefixo `_cs_` — nomes como `_w`,
    `master` e `tk` são do Tkinter e sobrescrevê-los quebra o app (FIX-003).
    """

    def __init__(self, master, title: str, key: str,
                 expanded: bool = False, on_toggle=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._cs_title    = title
        self._cs_key      = key
        self._cs_open     = bool(expanded)
        self._cs_on_toggle = on_toggle
        self.columnconfigure(0, weight=1)

        self.header = ctk.CTkButton(
            self, text="", anchor="w", height=30, corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray78", "#232334"), hover_color=("gray70", "#2e2e44"),
            text_color=("gray10", "gray90"), border_color="#5b8def",
            command=self.toggle)
        self.header.grid(row=0, column=0, sticky="ew")
        self._cs_make_focusable()

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="ew", padx=(8, 4), pady=(4, 2))
        self.body.columnconfigure(1, weight=1)
        self._cs_apply()

    def _cs_make_focusable(self):
        """CTkButton não entra na ordem do Tab sozinho: liga o foco no canvas."""
        try:
            self.header._canvas.configure(takefocus=1)
        except Exception:
            pass   # sem foco por teclado, o clique continua funcionando
        for seq in ("<space>", "<Return>"):
            self.header.bind(seq, lambda _e: (self.toggle(), "break")[1])
        self.header.bind("<FocusIn>",
                         lambda _e: self.header.configure(border_width=2))
        self.header.bind("<FocusOut>",
                         lambda _e: self.header.configure(border_width=0))

    def _cs_apply(self):
        self.header.configure(text=("▾ " if self._cs_open else "▸ ") + self._cs_title)
        if self._cs_open:
            self.body.grid()
        else:
            self.body.grid_remove()

    @property
    def key(self) -> str:
        return self._cs_key

    @property
    def expanded(self) -> bool:
        return self._cs_open

    def toggle(self):
        self._cs_open = not self._cs_open
        self._cs_apply()
        if self._cs_on_toggle:
            self._cs_on_toggle(self._cs_key, self._cs_open)


# ══════════════════════════════════════════════════════════════════════════════
# PAINEL: CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════

class ConfigPanel(ctk.CTkFrame):
    """Painel de configuração. Escreve direto no LayoutConfig e avisa o app.

    Três zonas (SPEC-F3-UI §4): grade fixa no topo, accordion rolável no meio,
    resumo fixo embaixo (contador, célula e guarda de qualidade).
    """

    BOTTOM_H = 84   # teto da zona inferior: não empurrar «Gerar» para fora em 768 px

    def __init__(self, master, cfg: LayoutConfig, on_change,
                 sections_open: Optional[Dict[str, bool]] = None,
                 on_sections_change=None, on_output_change=None, **kw):
        super().__init__(master, **kw)
        self.cfg       = cfg
        self.on_change = on_change
        self._on_output_change = on_output_change   # avisa o app (aviso do 2º destino)
        self.presets   = SettingsStore.load_presets()
        self._sections_state     = normalize_sections_open(sections_open)
        self._on_sections_change = on_sections_change
        self._sections: Dict[str, CollapsibleSection] = {}
        self._build()

    # ── Helpers de montagem ──────────────────────────────────────────────────

    def _acc_section(self, key: str, title: str) -> ctk.CTkFrame:
        """Cria uma seção do accordion e devolve o corpo para receber os campos.

        `row=` fixo pela ordem de SECTION_DEFAULTS: abrir/fechar não embaralha.
        """
        sec = CollapsibleSection(self._zone_acc, title, key,
                                 expanded=self._sections_state[key],
                                 on_toggle=self._on_section_toggle)
        sec.grid(row=list(SECTION_DEFAULTS).index(key), column=0,
                 sticky="ew", padx=2, pady=2)
        self._sections[key] = sec
        return sec.body

    def _on_section_toggle(self, key: str, expanded: bool):
        self._sections_state[key] = expanded
        if self._on_sections_change:
            self._on_sections_change(dict(self._sections_state))

    def sections_open(self) -> Dict[str, bool]:
        """Estado atual do accordion, para o app persistir."""
        return dict(self._sections_state)

    @staticmethod
    def _lbl(parent, text, row, col=0):
        ctk.CTkLabel(parent, text=text, anchor="w",
                     font=ctk.CTkFont(size=11)).grid(row=row, column=col,
                                                     sticky="w", padx=4, pady=2)

    def _num_entry(self, parent, var, row, col=1, width=65, cb=None):
        e = ctk.CTkEntry(parent, textvariable=var, width=width,
                         font=ctk.CTkFont(size=11), justify="center")
        e.grid(row=row, column=col, sticky="w", padx=4, pady=2)
        handler = cb or (lambda _: None)
        e.bind("<FocusOut>", handler)
        e.bind("<Return>",   handler)
        return e

    # ── Build ────────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._zone_top = ctk.CTkFrame(self, fg_color="transparent")
        self._zone_top.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        self._zone_acc = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._zone_acc.grid(row=1, column=0, sticky="nsew", padx=2, pady=4)
        self._zone_acc.columnconfigure(0, weight=1)
        self._zone_bottom = ctk.CTkFrame(self, height=self.BOTTOM_H)
        self._zone_bottom.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))
        self._zone_bottom.grid_propagate(False)
        self._zone_bottom.columnconfigure(0, weight=1)

        self._build_grid_zone(self._zone_top)
        self._build_accordion()
        self._build_summary_zone(self._zone_bottom)

    def _build_grid_zone(self, f):
        """Zona fixa do topo: o layout muda a cada trabalho, fica sempre à vista."""
        f.columnconfigure(1, weight=1)
        ctk.CTkLabel(f, text="Layout", anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 2))

        self._lbl(f, "Layout:", 1)
        self._layout_var = tk.StringVar(
            value=LAYOUT_LABELS[LAYOUT_KEYS.index(self.cfg.layout)])
        ctk.CTkOptionMenu(f, variable=self._layout_var, values=LAYOUT_LABELS,
                          command=self._on_layout, width=170).grid(
            row=1, column=1, sticky="w", padx=4)

        # Proporção: só aparece com moldura (a grade não tem).
        self._ratio_box = ctk.CTkFrame(f, fg_color="transparent")
        self._ratio_box.grid(row=2, column=0, columnspan=2, sticky="ew")
        self._lbl(self._ratio_box, "Proporção (%):", 0)
        self._ratio_var = tk.StringVar(value=str(self.cfg.layout_ratio_pct))
        self._num_entry(self._ratio_box, self._ratio_var, 0,
                        cb=lambda _: self._on_ratio())
        self._ratio_hint_var = tk.StringVar(value="")
        ctk.CTkLabel(self._ratio_box, textvariable=self._ratio_hint_var, anchor="w",
                     text_color=("gray50", "gray60"),
                     font=ctk.CTkFont(size=10)).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=4)

        grid_box = ctk.CTkFrame(f, fg_color="transparent")
        grid_box.grid(row=3, column=0, columnspan=2, sticky="ew")

        spin_col = ctk.CTkFrame(grid_box, fg_color="transparent")
        spin_col.pack(side="left", padx=(0, 8))

        self._cols_var = tk.StringVar(value=str(self.cfg.cols))
        self._rows_var = tk.StringVar(value=str(self.cfg.rows))
        # Controles da grade: ficam apagados (com os valores) quando há moldura.
        self._grid_ctrls = []

        for label, var, delta_fn in (("Colunas", self._cols_var, "cols"),
                                     ("Linhas",  self._rows_var, "rows")):
            line = ctk.CTkFrame(spin_col, fg_color="transparent")
            line.pack(anchor="w", pady=1)
            ctk.CTkLabel(line, text=f"{label}:", width=54, anchor="w",
                         font=ctk.CTkFont(size=11)).pack(side="left")
            minus = ctk.CTkButton(line, text="-", width=24, height=24,
                                  command=lambda a=delta_fn: self._bump(a, -1))
            minus.pack(side="left")
            entry = ctk.CTkEntry(line, textvariable=var, width=42, justify="center",
                                 font=ctk.CTkFont(size=11))
            entry.pack(side="left", padx=2)
            plus = ctk.CTkButton(line, text="+", width=24, height=24,
                                 command=lambda a=delta_fn: self._bump(a, +1))
            plus.pack(side="left")
            self._grid_ctrls += [minus, entry, plus]

        apply_btn = ctk.CTkButton(spin_col, text="Aplicar valores digitados", height=24,
                                  font=ctk.CTkFont(size=10),
                                  command=self._apply_typed_grid)
        apply_btn.pack(anchor="w", pady=(4, 0))
        self._grid_ctrls.append(apply_btn)

        self.grid_preview = GridPreview(grid_box)
        self.grid_preview.pack(side="left")

        self._lbl(f, "Atalhos:", 4)
        self._shortcut_var = tk.StringVar(value="—")
        self._shortcut_menu = ctk.CTkOptionMenu(
            f, variable=self._shortcut_var,
            values=["—"] + list(NUP_SHORTCUTS.keys()),
            command=self._on_shortcut, width=170)
        self._shortcut_menu.grid(row=4, column=1, sticky="w", padx=4)
        self._grid_ctrls.append(self._shortcut_menu)

        self._sync_layout_controls()

    def _build_summary_zone(self, f):
        """Zona fixa de baixo: feedback (contador, célula, qualidade), não config."""
        self._sheet_info_var = tk.StringVar(value="")
        ctk.CTkLabel(f, textvariable=self._sheet_info_var, anchor="w", height=16,
                     font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=(2, 0))

        self._cell_var = tk.StringVar(value="")
        ctk.CTkLabel(f, textvariable=self._cell_var, anchor="w", height=14,
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).grid(
            row=1, column=0, sticky="w", padx=8)

        self._sheet_var = tk.StringVar(value="")
        ctk.CTkLabel(f, textvariable=self._sheet_var, anchor="w", height=14,
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).grid(
            row=2, column=0, sticky="w", padx=8)

        self._qual_var = tk.StringVar(value="")
        self._qual_lbl = ctk.CTkLabel(f, textvariable=self._qual_var, anchor="w",
                                      justify="left", wraplength=290, height=28,
                                      font=ctk.CTkFont(size=10))
        self._qual_lbl.grid(row=3, column=0, sticky="nw", padx=8)
        # A quebra de linha acompanha a largura do painel (o divisor é móvel).
        f.bind("<Configure>", lambda e: self._qual_lbl.configure(
            wraplength=max(200, e.width - 24)))

    def _build_accordion(self):
        # ── PAPEL ──
        f2 = self._acc_section("papel", "Papel e resolução")
        self._lbl(f2, "Papel:", 0)
        self._paper_var = tk.StringVar(value=self.cfg.paper_key)
        ctk.CTkOptionMenu(f2, variable=self._paper_var, values=list(PAPER_SIZES.keys()),
                          command=self._on_paper, width=120).grid(
            row=0, column=1, sticky="w", padx=4)

        self._lbl(f2, "Largura (mm):", 1)
        self._pw_var = tk.StringVar(value=str(self.cfg.paper_w_mm))
        self._num_entry(f2, self._pw_var, 1, cb=lambda _: self._on_paper_dim())

        self._lbl(f2, "Altura (mm):", 2)
        self._ph_var = tk.StringVar(value=str(self.cfg.paper_h_mm))
        self._num_entry(f2, self._ph_var, 2, cb=lambda _: self._on_paper_dim())

        self._lbl(f2, "DPI:", 3)
        self._dpi_var = tk.StringVar(value=str(self.cfg.dpi))
        self._num_entry(f2, self._dpi_var, 3, cb=lambda _: self._on_dpi())

        # ── AJUSTE ──
        f1 = self._acc_section("ajuste", "Ajuste da imagem")
        self._lbl(f1, "Modo:", 0)
        self._fit_var = tk.StringVar(
            value=FIT_LABELS[FIT_KEYS.index(self.cfg.fit_mode)])
        ctk.CTkOptionMenu(f1, variable=self._fit_var, values=FIT_LABELS,
                          command=self._on_fit, width=160).grid(
            row=0, column=1, sticky="w", padx=4)

        self._auto_var = tk.BooleanVar(value=self.cfg.auto_rotate)
        ctk.CTkCheckBox(f1, text="Auto-Rotate (girar se necessário)",
                        variable=self._auto_var, command=self._on_auto).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=4, pady=2)

        # ── MARGENS ──
        f3 = self._acc_section("margens", "Margens e espaçamento")
        self._lbl(f3, "Margem ext. (mm):", 0)
        self._mo_var = tk.StringVar(value=str(self.cfg.margin_outer_mm))
        self._num_entry(f3, self._mo_var, 0, cb=lambda _: self._on_margins())

        self._lbl(f3, "Entre colunas (mm):", 1)
        self._mbx_var = tk.StringVar(value=str(self.cfg.margin_between_x_mm))
        self._num_entry(f3, self._mbx_var, 1, cb=lambda _: self._on_margins())

        self._lbl(f3, "Entre linhas (mm):", 2)
        self._mby_var = tk.StringVar(value=str(self.cfg.margin_between_y_mm))
        self._num_entry(f3, self._mby_var, 2, cb=lambda _: self._on_margins())

        self._lbl(f3, "Cor de fundo:", 3)
        self._bg_btn = ctk.CTkButton(f3, text="       ", width=65,
                                     fg_color=self.cfg.bg_color, command=self._pick_bg)
        self._bg_btn.grid(row=3, column=1, sticky="w", padx=4, pady=2)

        # ── CORTE ──
        # Seção «Corte e sangria» (a chave `corte` é a de sempre: o accordion
        # persistido não muda, só o título). Linhas 1–4 só com «Linhas atravessando»;
        # 5–7 só com «Marcas de canto»; o modo da sangria só com sangria > 0.
        f4 = self._acc_section("corte", "Corte e sangria")
        self._lbl(f4, "Guia de corte:", 0)
        self._guide_var = tk.StringVar(
            value=CUT_GUIDE_LABELS[CUT_GUIDE_KEYS.index(self.cfg.cut_guide)])
        ctk.CTkOptionMenu(f4, variable=self._guide_var, values=CUT_GUIDE_LABELS,
                          command=lambda _: self._on_cuts(), width=160).grid(
            row=0, column=1, sticky="w", padx=4)

        def _row(text, row, group):
            """Rótulo de uma linha que entra num grupo mostrável/escondível."""
            lbl = ctk.CTkLabel(f4, text=text, anchor="w", font=ctk.CTkFont(size=11))
            lbl.grid(row=row, column=0, sticky="w", padx=4, pady=2)
            group.append(lbl)

        self._cut_line_widgets: List[Any] = []
        self._cut_mark_widgets: List[Any] = []

        _row("Estilo:", 1, self._cut_line_widgets)
        self._cut_style_var = tk.StringVar(value=self.cfg.cut_style)
        w = ctk.CTkOptionMenu(f4, variable=self._cut_style_var, values=LINE_STYLES,
                              command=lambda _: self._on_cut_opts(), width=120)
        w.grid(row=1, column=1, sticky="w", padx=4)
        self._cut_line_widgets.append(w)

        _row("Espessura (px):", 2, self._cut_line_widgets)
        self._cut_w_var = tk.StringVar(value=str(self.cfg.cut_width_px))
        self._cut_line_widgets.append(
            self._num_entry(f4, self._cut_w_var, 2, cb=lambda _: self._on_cut_opts()))

        _row("Comprimento traço:", 3, self._cut_line_widgets)
        self._cut_dash_var = tk.StringVar(value=str(self.cfg.cut_dash))
        self._cut_line_widgets.append(
            self._num_entry(f4, self._cut_dash_var, 3, cb=lambda _: self._on_cut_opts()))

        _row("Cor da linha:", 4, self._cut_line_widgets)
        self._cut_col_btn = ctk.CTkButton(f4, text="       ", width=65,
                                          fg_color=self.cfg.cut_color,
                                          command=self._pick_cut_color)
        self._cut_col_btn.grid(row=4, column=1, sticky="w", padx=4, pady=2)
        self._cut_line_widgets.append(self._cut_col_btn)

        _row("Comprimento (mm):", 5, self._cut_mark_widgets)
        self._mark_len_var = tk.StringVar(value=str(self.cfg.mark_length_mm))
        self._cut_mark_widgets.append(
            self._num_entry(f4, self._mark_len_var, 5, cb=lambda _: self._on_mark_opts()))

        _row("Distância do corte (mm):", 6, self._cut_mark_widgets)
        self._mark_off_var = tk.StringVar(value=str(self.cfg.mark_offset_mm))
        self._cut_mark_widgets.append(
            self._num_entry(f4, self._mark_off_var, 6, cb=lambda _: self._on_mark_opts()))

        _row("Espessura (pt):", 7, self._cut_mark_widgets)
        self._mark_w_var = tk.StringVar(value=str(self.cfg.mark_width_pt))
        self._cut_mark_widgets.append(
            self._num_entry(f4, self._mark_w_var, 7, cb=lambda _: self._on_mark_opts()))

        self._lbl(f4, "Sangria (mm):", 8)
        self._bleed_var = tk.StringVar(value=str(self.cfg.bleed_mm))
        self._num_entry(f4, self._bleed_var, 8, cb=lambda _: self._on_bleed())

        self._bleed_mode_lbl = ctk.CTkLabel(f4, text="Modo:", anchor="w",
                                            font=ctk.CTkFont(size=11))
        self._bleed_mode_lbl.grid(row=9, column=0, sticky="w", padx=4, pady=2)
        self._bleed_mode_var = tk.StringVar(
            value=BLEED_MODE_LABELS[BLEED_MODE_KEYS.index(self.cfg.bleed_mode)])
        self._bleed_mode_menu = ctk.CTkOptionMenu(
            f4, variable=self._bleed_mode_var, values=BLEED_MODE_LABELS,
            command=lambda _: self._on_bleed(), width=190)
        self._bleed_mode_menu.grid(row=9, column=1, sticky="w", padx=4)

        # Avisos da geometria: âmbar (pede confirmação ao gerar) e cinza (só informa).
        self._cut_warn_var = tk.StringVar(value="")
        self._cut_warn_lbl = ctk.CTkLabel(f4, textvariable=self._cut_warn_var,
                                          anchor="w", justify="left", wraplength=250,
                                          font=ctk.CTkFont(size=10), text_color=WARN_COLOR)
        self._cut_warn_lbl.grid(row=10, column=0, columnspan=2, sticky="w", padx=4)
        self._cut_info_var = tk.StringVar(value="")
        self._cut_info_lbl = ctk.CTkLabel(f4, textvariable=self._cut_info_var,
                                          anchor="w", justify="left", wraplength=250,
                                          font=ctk.CTkFont(size=10),
                                          text_color=("gray50", "gray60"))
        self._cut_info_lbl.grid(row=11, column=0, columnspan=2, sticky="w", padx=4)
        self._sync_cut_controls()

        # ── SAÍDA ──
        f5 = self._acc_section("saida", "Saída")
        self._lbl(f5, "Formato:", 0)
        self._fmt_var = tk.StringVar(value=self.cfg.output_format)
        ctk.CTkOptionMenu(f5, variable=self._fmt_var, values=OUT_FORMATS,
                          command=lambda _: self._on_output(), width=100).grid(
            row=0, column=1, sticky="w", padx=4)

        # Compressão (só PDF) e qualidade (JPEG e PDF-JPEG): aparecem conforme o
        # formato — ver _sync_output_controls. Widgets guardados para esconder.
        self._comp_lbl = ctk.CTkLabel(f5, text="Compressão:", anchor="w",
                                      font=ctk.CTkFont(size=11))
        self._comp_lbl.grid(row=1, column=0, sticky="w", padx=4, pady=2)
        self._comp_var = tk.StringVar(
            value=PDF_COMP_LABELS[PDF_COMP_KEYS.index(self.cfg.pdf_compression)])
        self._comp_menu = ctk.CTkOptionMenu(
            f5, variable=self._comp_var, values=PDF_COMP_LABELS,
            command=lambda _: self._on_output(), width=100)
        self._comp_menu.grid(row=1, column=1, sticky="w", padx=4)

        # Compressão do WebP ocupa a mesma célula da do PDF; só um dos dois aparece.
        self._wcomp_var = tk.StringVar(
            value=WEBP_COMP_LABELS[WEBP_COMP_KEYS.index(self.cfg.webp_compression)])
        self._wcomp_menu = ctk.CTkOptionMenu(
            f5, variable=self._wcomp_var, values=WEBP_COMP_LABELS,
            command=lambda _: self._on_output(), width=100)
        self._wcomp_menu.grid(row=1, column=1, sticky="w", padx=4)

        self._q_lbl = ctk.CTkLabel(f5, text="Qualidade (50–100):", anchor="w",
                                   font=ctk.CTkFont(size=11))
        self._q_lbl.grid(row=2, column=0, sticky="w", padx=4, pady=2)
        self._q_var = tk.StringVar(value=str(self.cfg.jpeg_quality))
        self._q_entry = self._num_entry(f5, self._q_var, 2,
                                        cb=lambda _: self._on_output())

        self._lbl(f5, "Prefixo:", 3)
        self._pfx_var = tk.StringVar(value=self.cfg.output_prefix)
        self._num_entry(f5, self._pfx_var, 3, width=130, cb=lambda _: self._on_output())

        self._lbl(f5, "Sufixo:", 4)
        self._sfx_var = tk.StringVar(value=self.cfg.output_suffix)
        self._num_entry(f5, self._sfx_var, 4, width=130, cb=lambda _: self._on_output())

        ctk.CTkLabel(f5, text="Pasta de saída:", anchor="w",
                     font=ctk.CTkFont(size=11)).grid(row=5, column=0, columnspan=2,
                                                     sticky="w", padx=4, pady=(6, 0))
        dir_row = ctk.CTkFrame(f5, fg_color="transparent")
        dir_row.grid(row=6, column=0, columnspan=2, sticky="ew", padx=4)
        dir_row.columnconfigure(0, weight=1)
        self._dir_var = tk.StringVar(value=self.cfg.output_dir)
        ctk.CTkEntry(dir_row, textvariable=self._dir_var,
                     font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(dir_row, text="…", width=30,
                      command=self._pick_dir).grid(row=0, column=1, padx=(4, 0))

        self._dir2_on_var = tk.BooleanVar(value=self.cfg.output_dir2_on)
        ctk.CTkCheckBox(f5, text="Salvar cópia em outro destino",
                        variable=self._dir2_on_var, command=self._on_output).grid(
            row=7, column=0, columnspan=2, sticky="w", padx=4, pady=(6, 0))

        dir2_row = ctk.CTkFrame(f5, fg_color="transparent")
        dir2_row.grid(row=8, column=0, columnspan=2, sticky="ew", padx=4)
        dir2_row.columnconfigure(0, weight=1)
        self._dir2_var = tk.StringVar(value=self.cfg.output_dir2)
        dir2_entry = ctk.CTkEntry(dir2_row, textvariable=self._dir2_var,
                                  font=ctk.CTkFont(size=10))
        dir2_entry.grid(row=0, column=0, sticky="ew")
        dir2_entry.bind("<FocusOut>", lambda _: self._on_output())
        ctk.CTkButton(dir2_row, text="…", width=30,
                      command=self._pick_dir2).grid(row=0, column=1, padx=(4, 0))
        # Aviso de uso (WEBP/AVIF): fica no fim da seção, a coluna é estreita.
        self._share_lbl = ctk.CTkLabel(
            f5, text="Para compartilhar — gráficas e impressoras pedem PDF, TIFF, PNG ou JPEG.",
            anchor="w", justify="left", wraplength=230, text_color="gray60",
            font=ctk.CTkFont(size=10))
        self._share_lbl.grid(row=9, column=0, columnspan=2, sticky="w",
                             padx=4, pady=(6, 0))
        self._sync_output_controls()

    # ── Callbacks: grade ─────────────────────────────────────────────────────

    def _bump(self, which: str, delta: int):
        cap = MAX_COLS if which == "cols" else MAX_ROWS
        val = max(1, min(cap, getattr(self.cfg, which) + delta))
        setattr(self.cfg, which, val)
        (self._cols_var if which == "cols" else self._rows_var).set(str(val))
        self._sync_grid()

    def _apply_typed_grid(self):
        for var, attr, cap in ((self._cols_var, "cols", MAX_COLS),
                               (self._rows_var, "rows", MAX_ROWS)):
            try:
                setattr(self.cfg, attr, max(1, min(cap, int(var.get()))))
            except ValueError:
                pass
            var.set(str(getattr(self.cfg, attr)))
        self._sync_grid()

    def _on_shortcut(self, label: str):
        if label in NUP_SHORTCUTS:
            self.cfg.cols, self.cfg.rows = NUP_SHORTCUTS[label]
            self._cols_var.set(str(self.cfg.cols))
            self._rows_var.set(str(self.cfg.rows))
            self._sync_grid()

    def _sync_grid(self):
        self._draw_mini()
        self._shortcut_var.set(self._matching_shortcut())
        self.on_change()

    def _draw_mini(self):
        """Miniatura do layout: a grade, ou os slots da moldura numerados."""
        if self.cfg.layout == "grid":
            self.grid_preview.draw(self.cfg.cols, self.cfg.rows)
        else:
            cells, _ = frame_cells(self.cfg.layout, self.cfg.layout_ratio_pct,
                                   (0.0, 0.0, 1.0, 1.0), 0.0, 0.0)
            self.grid_preview.draw_frame(cells)

    def _sync_layout_controls(self):
        """Com moldura: apaga os controles da grade (valores preservados) e mostra
        a proporção com a dica. Voltar à grade reativa tudo como estava."""
        framed = self.cfg.layout != "grid"
        for w in self._grid_ctrls:
            w.configure(state="disabled" if framed else "normal")
        if framed:
            self._ratio_hint_var.set(LAYOUT_HINTS[self.cfg.layout])
            self._ratio_box.grid()
        else:
            self._ratio_box.grid_remove()
        self._draw_mini()

    def _on_layout(self, label: str):
        self.cfg.layout = LAYOUT_KEYS[LAYOUT_LABELS.index(label)]
        self._sync_layout_controls()
        self.on_change()

    def _on_ratio(self):
        """Proporção da moldura: fora da faixa vai ao limite; ilegível volta ao valor."""
        self.cfg.layout_ratio_pct = int(round(clamp_float(
            self._ratio_var.get().replace(",", "."), *LAYOUT_RATIO_RANGE,
            self.cfg.layout_ratio_pct)))
        self._ratio_var.set(str(self.cfg.layout_ratio_pct))
        self._draw_mini()
        self.on_change()

    def _matching_shortcut(self) -> str:
        for name, (c, rr) in NUP_SHORTCUTS.items():
            if (c, rr) == (self.cfg.cols, self.cfg.rows):
                return name
        return "—"

    # ── Callbacks: demais ────────────────────────────────────────────────────

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
            self.cfg.paper_w_mm, self.cfg.paper_h_mm = w, h
            self._pw_var.set(str(w)); self._ph_var.set(str(h))
        self.on_change()

    def _on_paper_dim(self):
        for var, attr in ((self._pw_var, "paper_w_mm"), (self._ph_var, "paper_h_mm")):
            try:
                setattr(self.cfg, attr, max(1.0, float(var.get())))
            except ValueError:
                pass
            var.set(str(getattr(self.cfg, attr)))
        self.cfg.paper_key = "Custom"
        self._paper_var.set("Custom")
        self.on_change()

    def _on_dpi(self):
        try:
            self.cfg.dpi = max(72, min(1200, int(self._dpi_var.get())))
        except ValueError:
            pass
        self._dpi_var.set(str(self.cfg.dpi))
        self.on_change()

    def _on_margins(self):
        for var, attr in ((self._mo_var, "margin_outer_mm"),
                          (self._mbx_var, "margin_between_x_mm"),
                          (self._mby_var, "margin_between_y_mm")):
            try:
                setattr(self.cfg, attr, max(0.0, float(var.get())))
            except ValueError:
                pass
            var.set(str(getattr(self.cfg, attr)))
        self.on_change()

    def _pick_bg(self):
        c = colorchooser.askcolor(color=self.cfg.bg_color, title="Cor de fundo")[1]
        if c:
            self.cfg.bg_color = c
            self._bg_btn.configure(fg_color=c)
            self.on_change()

    def _on_cuts(self):
        self.cfg.cut_guide = CUT_GUIDE_KEYS[CUT_GUIDE_LABELS.index(self._guide_var.get())]
        self._sync_cut_controls()
        self.on_change()

    def _sync_cut_controls(self):
        """Mostra só os controles que valem para a guia e a sangria atuais."""
        for group, shown in ((self._cut_line_widgets, self.cfg.cut_guide == "lines"),
                             (self._cut_mark_widgets, self.cfg.cut_guide == "marks")):
            for widget in group:
                widget.grid() if shown else widget.grid_remove()
        for widget in (self._bleed_mode_lbl, self._bleed_mode_menu):
            widget.grid() if self.cfg.bleed_mm > 0 else widget.grid_remove()
        self._refresh_cut_notes()

    def _refresh_cut_notes(self):
        """Escreve os avisos da geometria (âmbar e cinza) sob os campos."""
        warnings = sheet_geometry(self.cfg).warnings
        self._cut_warn_var.set("\n".join(t for lvl, t in warnings if lvl == "warn"))
        self._cut_info_var.set("\n".join(t for lvl, t in warnings if lvl == "info"))

    def _on_mark_opts(self):
        """Comprimento, distância e espessura das marcas: fora de faixa vai ao limite."""
        for var, attr, rng in ((self._mark_len_var, "mark_length_mm", MARK_LEN_RANGE),
                               (self._mark_off_var, "mark_offset_mm", MARK_OFFSET_RANGE),
                               (self._mark_w_var, "mark_width_pt", MARK_WIDTH_RANGE)):
            setattr(self.cfg, attr, clamp_float(var.get().replace(",", "."), *rng,
                                                getattr(self.cfg, attr)))
            var.set(str(getattr(self.cfg, attr)))
        self._sync_cut_controls()
        self.on_change()

    def _on_bleed(self):
        """Sangria (0–10 mm) e modo; o modo só aparece com sangria > 0."""
        self.cfg.bleed_mm = clamp_float(self._bleed_var.get().replace(",", "."),
                                        *BLEED_RANGE, self.cfg.bleed_mm)
        self._bleed_var.set(str(self.cfg.bleed_mm))
        self.cfg.bleed_mode = BLEED_MODE_KEYS[
            BLEED_MODE_LABELS.index(self._bleed_mode_var.get())]
        self._sync_cut_controls()
        self.on_change()

    def _on_cut_opts(self):
        self.cfg.cut_style = self._cut_style_var.get()
        for var, attr, lo in ((self._cut_w_var, "cut_width_px", 1),
                              (self._cut_dash_var, "cut_dash", 2)):
            try:
                setattr(self.cfg, attr, max(lo, int(var.get())))
            except ValueError:
                pass
            var.set(str(getattr(self.cfg, attr)))
        self.on_change()

    def _pick_cut_color(self):
        c = colorchooser.askcolor(color=self.cfg.cut_color,
                                  title="Cor das linhas de corte")[1]
        if c:
            self.cfg.cut_color = c
            self._cut_col_btn.configure(fg_color=c)
            self.on_change()

    def _on_output(self):
        self.cfg.output_format  = self._fmt_var.get()
        self.cfg.pdf_compression = PDF_COMP_KEYS[
            PDF_COMP_LABELS.index(self._comp_var.get())]
        # Fora de 50–100 é ajustado ao limite e o campo mostra o valor usado.
        self.cfg.webp_compression = WEBP_COMP_KEYS[
            WEBP_COMP_LABELS.index(self._wcomp_var.get())]
        self.cfg.jpeg_quality = clamp_jpeg_quality(self._q_var.get(),
                                                   self.cfg.jpeg_quality)
        self._q_var.set(str(self.cfg.jpeg_quality))
        self._sync_output_controls()
        self.cfg.output_prefix  = self._pfx_var.get()
        self.cfg.output_suffix  = self._sfx_var.get()
        self.cfg.output_dir     = self._dir_var.get()
        self.cfg.output_dir2    = self._dir2_var.get()
        self.cfg.output_dir2_on = self._dir2_on_var.get()
        if self._on_output_change:
            self._on_output_change()

    def _sync_output_controls(self):
        """Mostra «Compressão» no PDF e no WebP, e «Qualidade» quando há perda no
        caminho (JPEG, PDF-JPEG, WebP com perda, AVIF). PNG/TIFF não têm controle."""
        fmt = self._fmt_var.get()
        is_pdf = fmt == "PDF"
        is_webp = fmt == "WEBP"
        if is_pdf:
            self._comp_menu.grid()
        else:
            self._comp_menu.grid_remove()
        if is_webp:
            self._wcomp_menu.grid()
        else:
            self._wcomp_menu.grid_remove()
        if is_pdf or is_webp:
            self._comp_lbl.grid()
        else:
            self._comp_lbl.grid_remove()
        if fmt in SHARE_FORMATS:
            self._share_lbl.grid()
        else:
            self._share_lbl.grid_remove()
        jpeg_q = fmt in ("JPEG", "AVIF") or (
            is_pdf and self._comp_var.get() == PDF_COMP_LABELS[1]) or (
            is_webp and self._wcomp_var.get() == WEBP_COMP_LABELS[1])
        if jpeg_q:
            self._q_lbl.grid(); self._q_entry.grid()
        else:
            self._q_lbl.grid_remove(); self._q_entry.grid_remove()

    def _pick_dir(self):
        d = filedialog.askdirectory(title="Pasta de saída",
                                    initialdir=self.cfg.output_dir or str(Path.home()))
        if d:
            self.cfg.output_dir = d
            self._dir_var.set(d)

    def _pick_dir2(self):
        d = filedialog.askdirectory(
            title="Segundo destino",
            initialdir=self.cfg.output_dir2 or self.cfg.output_dir or str(Path.home()))
        if d:
            self.cfg.output_dir2 = d
            self._dir2_var.set(d)
            self._dir2_on_var.set(True)
            self._on_output()

    # ── Presets ──────────────────────────────────────────────────────────────
    # O menu que os lista vive no app e é reconstruído a cada abertura; aqui
    # ficam só os dados e as ações.

    def preset_names(self) -> List[str]:
        return sorted(self.presets.keys())

    def save_preset(self):
        dlg = ctk.CTkInputDialog(text="Nome do preset:", title="Salvar preset")
        name = (dlg.get_input() or "").strip()
        if not name:
            return
        self.presets[name] = self.cfg.preset_dict()
        if SettingsStore.save_presets(self.presets):
            messagebox.showinfo("Preset salvo", f"Preset «{name}» salvo.")
        else:
            messagebox.showwarning("Não foi possível salvar",
                                   "Falha ao gravar o arquivo de presets.")

    def delete_preset(self, name: str):
        if name in self.presets and messagebox.askyesno(
                "Excluir preset", f"Excluir o preset «{name}»?"):
            self.presets.pop(name, None)
            SettingsStore.save_presets(self.presets)

    def load_preset(self, name: str):
        data = self.presets.get(name)
        if not data:
            return
        self.cfg.from_dict(data)
        self.refresh_from_config()
        self.on_change()

    # ── Sincronização UI ← config ────────────────────────────────────────────

    def refresh_from_config(self):
        """Reescreve todos os campos a partir do LayoutConfig (usado por preset)."""
        c = self.cfg
        self._cols_var.set(str(c.cols)); self._rows_var.set(str(c.rows))
        self._layout_var.set(LAYOUT_LABELS[LAYOUT_KEYS.index(c.layout)])
        self._ratio_var.set(str(c.layout_ratio_pct))
        self._sync_layout_controls()
        self._shortcut_var.set(self._matching_shortcut())
        self._fit_var.set(FIT_LABELS[FIT_KEYS.index(c.fit_mode)])
        self._auto_var.set(c.auto_rotate)
        self._paper_var.set(c.paper_key)
        self._pw_var.set(str(c.paper_w_mm)); self._ph_var.set(str(c.paper_h_mm))
        self._dpi_var.set(str(c.dpi))
        self._mo_var.set(str(c.margin_outer_mm)); self._mbx_var.set(str(c.margin_between_x_mm))
        self._mby_var.set(str(c.margin_between_y_mm))
        self._bg_btn.configure(fg_color=c.bg_color)
        self._guide_var.set(CUT_GUIDE_LABELS[CUT_GUIDE_KEYS.index(c.cut_guide)])
        self._cut_style_var.set(c.cut_style)
        self._cut_w_var.set(str(c.cut_width_px)); self._cut_dash_var.set(str(c.cut_dash))
        self._cut_col_btn.configure(fg_color=c.cut_color)
        self._mark_len_var.set(str(c.mark_length_mm))
        self._mark_off_var.set(str(c.mark_offset_mm))
        self._mark_w_var.set(str(c.mark_width_pt))
        self._bleed_var.set(str(c.bleed_mm))
        self._bleed_mode_var.set(BLEED_MODE_LABELS[BLEED_MODE_KEYS.index(c.bleed_mode)])
        self._sync_cut_controls()
        self._fmt_var.set(c.output_format)
        self._comp_var.set(PDF_COMP_LABELS[PDF_COMP_KEYS.index(c.pdf_compression)])
        self._q_var.set(str(c.jpeg_quality))
        self._wcomp_var.set(WEBP_COMP_LABELS[WEBP_COMP_KEYS.index(c.webp_compression)])
        self._sync_output_controls()
        self._pfx_var.set(c.output_prefix); self._sfx_var.set(c.output_suffix)
        self._dir_var.set(c.output_dir); self._dir2_var.set(c.output_dir2)
        self._dir2_on_var.set(c.output_dir2_on)

    def update_info(self, n_images: int, n_pages: int, engine: "ImpositionEngine"):
        """Atualiza contadores, tamanho de célula e a guarda de qualidade."""
        self._refresh_cut_notes()      # margem/espaçamento mudaram → avisos de corte também
        self._sheet_info_var.set(
            f"{n_images} imagem(ns) · {self.cfg.nup()} por folha · {n_pages} folha(s)")

        framed = self.cfg.layout != "grid"
        q = engine.quality_report()
        if framed:
            # O menor slot é o que limita a qualidade; mostra ele, em mm e em px.
            mm_rects = engine.slot_rects_mm()
            px_rects = engine.slot_rects_px()
            k = min(range(len(mm_rects)),
                    key=lambda i: (mm_rects[i][2] - mm_rects[i][0])
                    * (mm_rects[i][3] - mm_rects[i][1]))
            m = mm_rects[k]
            pr = px_rects[k]
            self._cell_var.set(
                f"Células: {len(mm_rects)} · menor {m[2] - m[0]:.1f} × {m[3] - m[1]:.1f} mm"
                f"  ({pr[2] - pr[0]} × {pr[3] - pr[1]} px @ {self.cfg.dpi} DPI)")
            cw_px, ch_px = q["needed"]
        else:
            cw_mm, ch_mm = engine.cell_mm()
            cw_px, ch_px = engine.cell_px()
            self._cell_var.set(
                f"Célula: {cw_mm:.1f} × {ch_mm:.1f} mm  ({cw_px} × {ch_px} px @ {self.cfg.dpi} DPI)")

        sw, sh, mb_raw = engine.sheet_info()
        self._sheet_var.set(
            f"Folha: {sw} × {sh} px · {mb_raw:.1f} MB bruto".replace(".", ","))

        if q["level"] == "none":
            self._qual_var.set("")
            return
        pct = q["ratio"] * 100
        if q["level"] == "ok":
            self._qual_var.set(f"✔ Qualidade OK — a menor fonte cobre {pct:.0f}% da célula.")
            self._qual_lbl.configure(text_color="#5dbb63")
        elif q["level"] == "warn":
            self._qual_var.set(
                f"⚠ Atenção — «{q['worst']}» cobre só {pct:.0f}% da célula; "
                f"haverá ampliação leve. Ideal: ≥ {cw_px}×{ch_px} px.")
            self._qual_lbl.configure(text_color="#d6a13a")
        else:
            self._qual_var.set(
                f"✖ Perda visível — «{q['worst']}» cobre {pct:.0f}% da célula. "
                f"Reexporte com pelo menos {cw_px}×{ch_px} px, ou baixe o DPI.")
            self._qual_lbl.configure(text_color="#d15b5b")


# ══════════════════════════════════════════════════════════════════════════════
# PAINEL: PREVIEW
# ══════════════════════════════════════════════════════════════════════════════

class PreviewPanel(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._tk_img = None
        self._build()

    def _build(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        ctk.CTkLabel(nav, text="Preview",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self._nav_lbl = ctk.CTkLabel(nav, text="", font=ctk.CTkFont(size=11))
        self._nav_lbl.pack(side="left", padx=12)
        ctk.CTkButton(nav, text="▶", width=32, command=self._next).pack(side="right")
        ctk.CTkButton(nav, text="◀", width=32, command=self._prev).pack(side="right", padx=4)

        self._canvas = tk.Canvas(self, bg="#1a1a2a", highlightthickness=0,
                                 width=PREVIEW_MAX[0], height=PREVIEW_MAX[1])
        self._canvas.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))
        self._canvas.create_text(PREVIEW_MAX[0] // 2, PREVIEW_MAX[1] // 2,
                                 text="Adicione imagens para ver o preview",
                                 fill="#555577", font=("Helvetica", 11))

    def update_preview(self, img: Optional[Image.Image], page_idx: int, total: int):
        self._nav_lbl.configure(
            text=f"Folha {page_idx+1} / {total}" if total > 0 else "Sem folhas")
        self._canvas.delete("all")

        if img is None:
            self._canvas.create_text(PREVIEW_MAX[0] // 2, PREVIEW_MAX[1] // 2,
                                     text="Nenhuma imagem para exibir",
                                     fill="#555577", font=("Helvetica", 11))
            return

        cw = self._canvas.winfo_width()  or PREVIEW_MAX[0]
        ch = self._canvas.winfo_height() or PREVIEW_MAX[1]
        self._tk_img = ImageTk.PhotoImage(img)
        x = (cw - img.width) // 2
        y = (ch - img.height) // 2
        self._canvas.create_rectangle(x + 4, y + 4, x + img.width + 4,
                                      y + img.height + 4, fill="#000000", outline="")
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

class PrintImposerApp(ctk.CTk, _DnDBase):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self._dnd_ok = self._setup_dnd()

        self.cfg = LayoutConfig()
        self._load_persisted()

        self._preview_idx = 0
        self._preview_job = None
        self._generating  = False

        self._setup_geometry()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._on_change()

    # ── Arrastar e soltar (DEC-016) ──────────────────────────────────────────

    def _setup_dnd(self) -> bool:
        """Liga o soltar na janela inteira; só devolve True com a capacidade PROVADA.

        Importar o pacote não basta (FIX-002): o tkDnD precisa carregar no Tcl desta
        janela, e o registro do alvo precisa passar. Qualquer falha desliga o recurso
        e o app segue como na 1.6.0.
        """
        if not DND_PKG_OK:
            return False
        try:
            if not TkinterDnD._require(self):
                return False
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<DropEnter>>", self._on_drop_enter)
            self.dnd_bind("<<DropLeave>>", self._on_drop_leave)
            self.dnd_bind("<<Drop>>", self._on_drop)
            return True
        except Exception:
            return False

    def _on_drop_enter(self, event):
        self.img_panel.set_drop_highlight(True)
        return event.action

    def _on_drop_leave(self, event):
        self.img_panel.set_drop_highlight(False)
        return event.action

    def _on_drop(self, event):
        self.img_panel.set_drop_highlight(False)
        # `splitlist`, nunca `split()`: caminho com espaço chega entre chaves.
        try:
            paths = self.tk.splitlist(event.data)
        except tk.TclError:
            paths = ()
        # Adiar: os diálogos da ingestão são modais e segurariam o Explorer preso
        # dentro do callback do soltar.
        self.after(10, lambda: self.img_panel.ingest_dropped(paths))
        return event.action

    # ── Persistência ─────────────────────────────────────────────────────────

    def _load_persisted(self):
        data = SettingsStore.load_settings()
        cfg_data = data.get("config") or {}
        if isinstance(cfg_data, dict):
            self.cfg.from_dict(cfg_data)
        # Pasta que sumiu do disco não deve travar o app.
        if not Path(self.cfg.output_dir or "").is_dir():
            self.cfg.output_dir = default_output_dir()
        if not Path(self.cfg.input_dir or "").is_dir():
            self.cfg.input_dir = str(Path.home())
        self._saved_geometry = data.get("geometry", "")
        # Arquivo da 1.1.x não tem a chave: cai no padrão (só «saida» aberta).
        self._sections_open = normalize_sections_open(data.get("sections_open"))

    def _persist(self):
        try:
            geo = self.winfo_geometry()
        except Exception:
            geo = ""
        sections = (self.cfg_panel.sections_open() if hasattr(self, "cfg_panel")
                    else self._sections_open)
        SettingsStore.save_settings({"config": self.cfg.to_dict(),
                                     "geometry": geo,
                                     "sections_open": sections,
                                     "version": VERSION})

    def _on_close(self):
        if hasattr(self, "cfg_panel"):
            self.cfg_panel._on_output()   # captura o que foi digitado sem sair do campo
        self._persist()
        self.destroy()

    # ── Geometria da janela ──────────────────────────────────────────────────

    def _work_area(self) -> Tuple[int, int, int, int]:
        """Área ÚTIL da tela — sem a barra de tarefas. Retorna (x, y, w, h).

        `winfo_screenheight()` devolve a tela física; usar isso deixava a barra
        de ação ("Gerar Arquivos") escondida sob a barra de tarefas em telas
        baixas. No Windows a área útil vem do SPI_GETWORKAREA. Ver FIX-005.
        """
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes
                rect = wintypes.RECT()
                SPI_GETWORKAREA = 0x0030
                if ctypes.windll.user32.SystemParametersInfoW(
                        SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
                    return (rect.left, rect.top,
                            rect.right - rect.left, rect.bottom - rect.top)
            except Exception:
                pass

        # Fora do Windows, ou se a API falhar: desconta uma faixa de cortesia.
        return 0, 0, sw, max(400, sh - 60)

    def _setup_geometry(self):
        """Centraliza a janela dentro da ÁREA ÚTIL da tela.
        Dois cuidados: o clamp usa a área útil (não a tela física), para a barra
        de ação não ficar sob a barra de tarefas; e a posição salva só é
        reaproveitada se ainda couber no monitor atual. Ver HISTORY §6 e FIX-005.
        """
        self.update_idletasks()
        ax, ay, aw, ah = self._work_area()

        def place(w: int, h: int):
            w = max(880, min(w, aw))
            h = max(600, min(h, ah))
            x = ax + max(0, (aw - w) // 2)
            y = ay + max(0, (ah - h) // 3)   # levemente acima do centro
            self.geometry(f"{w}x{h}+{x}+{y}")
            self.minsize(880, 600)

        if self._saved_geometry:
            try:
                w, h = (int(v) for v in self._saved_geometry.split("+")[0].split("x"))
                if w <= aw and h <= ah:
                    place(w, h)
                    return
            except Exception:
                pass

        place(min(1180, int(aw * 0.92)), min(820, int(ah * 0.92)))

    def _place_sashes(self):
        """Define a posição inicial dos divisores.

        O PanedWindow distribui o espaço no primeiro render e ignora `width=`
        como valor firme; sem isto um painel engolia o outro. Ver HISTORY §6.
        """
        try:
            total = self.winfo_width()
            if total < 400:
                return
            self._pane.sash_place(0, int(total * 0.28), 0)
            right_total = self._right_pane.winfo_width()
            if right_total > 300:
                self._right_pane.sash_place(0, int(right_total * 0.48), 0)
        except Exception:
            pass  # geometria ainda não resolvida: fica o padrão do Tk

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, height=44, corner_radius=0,
                              fg_color=("gray80", "#12121e"))
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(header, text=APP_NAME,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
            side="left", padx=(14, 10), pady=8)
        self._menu_buttons: Dict[str, ctk.CTkButton] = {}
        for title in MENU_TITLES:
            btn = ctk.CTkButton(header, text=title, width=70, height=28,
                                fg_color="transparent",
                                hover_color=("gray70", "#2e2e44"),
                                text_color=("gray10", "gray90"),
                                command=lambda t=title: self._popup_menu(t))
            btn.pack(side="left", padx=1, pady=8)
            self._menu_buttons[title] = btn
        svg_note = f"SVG: {SVG_BACKEND}" if SVG_BACKEND else "SVG: indisponível"
        pdf_note = f"PDF: {PDF_BACKEND}" if PDF_BACKEND else "PDF: indisponível"
        dnd_note = "Arrastar: tkinterdnd2" if self._dnd_ok else "Arrastar: indisponível"
        ctk.CTkLabel(header, text=f"v{VERSION}   ·   {svg_note}   ·   {pdf_note}   ·   {dnd_note}",
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray50")).pack(side="right", padx=14)

        self._pane = tk.PanedWindow(self, orient="horizontal", sashwidth=5,
                                    bg="#2a2a3a", sashrelief="flat")
        self._pane.grid(row=1, column=0, sticky="nsew")

        # ARMADILHA nº1 (FIX-001): widget CTk com canvas interno não pode ir
        # direto para o PanedWindow — sempre um tk.Frame neutro de permeio.
        list_outer = tk.Frame(self._pane, bg="#2a2a3a")
        list_outer.rowconfigure(0, weight=1); list_outer.columnconfigure(0, weight=1)
        self.img_panel = ImageListPanel(list_outer, self.cfg, on_change=self._on_change,
                                        drop_enabled=self._dnd_ok)
        self.img_panel.grid(row=0, column=0, sticky="nsew")
        self._pane.add(list_outer, minsize=270)

        right_outer = tk.Frame(self._pane, bg="#2a2a3a")
        right_outer.rowconfigure(0, weight=1); right_outer.columnconfigure(0, weight=1)
        self._right_pane = tk.PanedWindow(right_outer, orient="horizontal",
                                          sashwidth=5, bg="#2a2a3a", sashrelief="flat")
        self._right_pane.grid(row=0, column=0, sticky="nsew")
        self._pane.add(right_outer, minsize=560)

        cfg_outer = tk.Frame(self._right_pane, bg="#2a2a3a")
        cfg_outer.rowconfigure(0, weight=1); cfg_outer.columnconfigure(0, weight=1)
        self.cfg_panel = ConfigPanel(cfg_outer, self.cfg, on_change=self._on_change,
                                     on_output_change=self._refresh_dest_notice,
                                     sections_open=self._sections_open)
        self.cfg_panel.grid(row=0, column=0, sticky="nsew")
        self._right_pane.add(cfg_outer, minsize=300)

        prev_outer = tk.Frame(self._right_pane, bg="#2a2a3a")
        prev_outer.rowconfigure(0, weight=1); prev_outer.columnconfigure(0, weight=1)
        self.preview_panel = PreviewPanel(prev_outer)
        self.preview_panel.grid(row=0, column=0, sticky="nsew")
        self._right_pane.add(prev_outer, minsize=270)

        self.preview_panel.canvas.bind("<<PreviewPrev>>", lambda _: self._nav_preview(-1))
        self.preview_panel.canvas.bind("<<PreviewNext>>", lambda _: self._nav_preview(+1))

        bottom = ctk.CTkFrame(self, height=54, corner_radius=0,
                              fg_color=("gray80", "#12121e"))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(1, weight=1)

        self._gen_btn = ctk.CTkButton(bottom, text="Gerar Arquivos",
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      height=36, width=170, command=self._start_generate)
        self._gen_btn.grid(row=0, column=0, padx=12, pady=9)

        self._prog_var = tk.DoubleVar(value=0)
        ctk.CTkProgressBar(bottom, variable=self._prog_var, height=12).grid(
            row=0, column=1, sticky="ew", padx=8)

        self._status_var = tk.StringVar(value="Pronto")
        ctk.CTkLabel(bottom, textvariable=self._status_var, font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).grid(row=0, column=2, padx=12)

        # Aviso do segundo destino: só aparece com ele ligado (ver second_dest_notice).
        self._dest_var = tk.StringVar(value="")
        self._dest_lbl = ctk.CTkLabel(bottom, textvariable=self._dest_var,
                                      font=ctk.CTkFont(size=10))
        self._dest_lbl.grid(row=0, column=3, padx=(0, 12))
        self._refresh_dest_notice()

        self._build_menus()
        self._bind_shortcuts()

        # Sashes só depois que o Tk resolveu a geometria real.
        self.after(120, self._place_sashes)

    # ── Menubar ──────────────────────────────────────────────────────────────
    # Botões na topbar + tk.Menu.tk_popup: a faixa fica no tema escuro e o
    # dropdown continua nativo (teclado, dismissal). Ver SPEC-F3-UI §5.

    def _build_menus(self):
        L = MENU_LABELS
        self._menus: Dict[str, tk.Menu] ={t: tk.Menu(self, tearoff=0) for t in MENU_TITLES}

        m = self._menus["Arquivo"]
        m.add_command(label=L["add_files"], accelerator="Ctrl+O",
                      command=lambda: self.img_panel._add_files())
        m.add_command(label=L["add_folder"], accelerator="Ctrl+Shift+O",
                      command=lambda: self.img_panel._add_folder())
        m.add_command(label=L["clear"], command=lambda: self.img_panel._clear())
        m.add_separator()
        m.add_command(label=L["generate"], accelerator="Ctrl+G",
                      command=self._start_generate)
        m.add_command(label=L["open_out"], command=self._open_output_folder)
        m.add_separator()
        m.add_command(label=L["quit"], accelerator="Alt+F4", command=self._on_close)

        # Presets entra vazio: é reconstruído a CADA abertura (ver _popup_menu).
        self._presets_menu = tk.Menu(self._menus["Opções"], tearoff=0)
        m = self._menus["Opções"]
        m.add_cascade(label=L["presets"], menu=self._presets_menu)
        m.add_separator()
        m.add_command(label=L["make_bat"], command=self._show_shortcut_dialog)
        m.add_separator()
        m.add_command(label=L["reset"], command=self._reset_defaults)

        m = self._menus["Ajuda"]
        m.add_command(label=L["guide"], command=self._show_guide)
        m.add_separator()
        m.add_command(label=L["about"], command=self._show_about)

    def _rebuild_presets_menu(self):
        """Reconstrói o submenu a partir dos presets atuais (o bug de 1.1.x
        era a lista só atualizar ao reabrir o app)."""
        L = MENU_LABELS
        pm = self._presets_menu
        pm.delete(0, "end")
        names = self.cfg_panel.preset_names()
        for name in names:
            pm.add_command(label=name,
                           command=lambda n=name: self.cfg_panel.load_preset(n))
        if names:
            pm.add_separator()
        pm.add_command(label=L["save_preset"], command=self.cfg_panel.save_preset)
        del_menu = tk.Menu(pm, tearoff=0)
        for name in names:
            del_menu.add_command(
                label=name, command=lambda n=name: self.cfg_panel.delete_preset(n))
        pm.add_cascade(label=L["delete_preset"], menu=del_menu,
                       state="normal" if names else "disabled")

    def _popup_menu(self, title: str):
        if title == "Opções":
            self._rebuild_presets_menu()
        btn = self._menu_buttons[title]
        try:
            self._menus[title].tk_popup(btn.winfo_rootx(),
                                        btn.winfo_rooty() + btn.winfo_height())
        finally:
            self._menus[title].grab_release()

    def _bind_shortcuts(self):
        # bind_all: valem com o foco em qualquer painel. Shift+O chega como «O».
        self.bind_all("<Control-o>", lambda _e: self.img_panel._add_files())
        self.bind_all("<Control-O>", lambda _e: self.img_panel._add_folder())
        self.bind_all("<Control-g>", lambda _e: self._start_generate())
        self.bind_all("<Control-G>", lambda _e: self._start_generate())

    def _open_output_folder(self):
        self.cfg_panel._on_output()   # captura o que foi digitado sem sair do campo
        if self.cfg.output_dir and Path(self.cfg.output_dir).is_dir():
            self._open_folder(self.cfg.output_dir)
        else:
            messagebox.showinfo("Pasta de saída",
                                "A pasta de saída ainda não existe. "
                                "Gere os arquivos ou escolha outra pasta.")

    def _reset_defaults(self):
        if not messagebox.askyesno(
                "Restaurar padrões",
                "Voltar grade, papel, margens, corte e saída (formato e nomes) "
                "aos valores padrão?\nAs pastas de entrada e saída não mudam."):
            return
        self.cfg.from_dict(LayoutConfig().preset_dict())
        self.cfg_panel.refresh_from_config()
        self._on_change()

    def _show_guide(self):
        win = ctk.CTkToplevel(self)
        win.title(MENU_LABELS["guide"])
        win.geometry("520x380")
        win.transient(self)
        box = ctk.CTkTextbox(win, wrap="word", font=ctk.CTkFont(size=12))
        box.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        box.insert("1.0", QUICK_GUIDE)
        box.configure(state="disabled")
        ctk.CTkButton(win, text="Fechar", width=90, command=win.destroy).pack(pady=(0, 12))

    def _show_about(self):
        svg = SVG_BACKEND or "indisponível"
        messagebox.showinfo(
            f"Sobre o {APP_NAME}",
            f"{APP_NAME} v{VERSION}\n"
            "Imposição de páginas para impressão.\n\n"
            f"SVG: {svg}\n"
            f"Formatos extras: AVIF {'sim' if AVIF_OK else 'não'} · "
            f"HEIC {'sim' if HEIF_OK else 'não'} · "
            f"PDF {'sim' if PDF_OK else 'não'}\n"
            f"Arrastar e soltar: {'sim' if self._dnd_ok else 'não'}\n"
            f"Configuração: {SettingsStore.SETTINGS}")

    def _show_shortcut_dialog(self):
        """Explica o que é o atalho .bat ANTES de gerar (SPEC-F3-UI §6)."""
        win = ctk.CTkToplevel(self)
        win.title("Criar atalho")
        win.geometry("420x330")
        win.resizable(False, False)
        win.transient(self)
        pyw = Path(sys.executable).with_name("pythonw.exe")
        interp = str(pyw) if pyw.exists() else sys.executable
        script = str(Path(__file__).resolve())
        text = (
            "Um atalho .bat abre o PrintImposer com dois cliques, sem janela de console.\n\n"
            "Sugerimos salvá-lo na pasta acima da pasta do projeto, fora da área de "
            "trabalho. Qualquer pasta serve: o .bat grava caminhos absolutos.\n\n"
            "Se você mover a ferramenta, o atalho para de funcionar — gere outro.\n\n"
            f"Interpretador: {interp}\nScript: {script}")
        ctk.CTkLabel(win, text=text, justify="left", anchor="nw", wraplength=390,
                     font=ctk.CTkFont(size=11)).pack(fill="both", expand=True,
                                                    padx=14, pady=(14, 6))
        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(pady=(0, 12))
        ctk.CTkButton(row, text="Criar atalho…", width=120,
                      command=lambda: self._make_bat(win)).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Fechar", width=90, fg_color="#444455",
                      command=win.destroy).pack(side="left", padx=4)
        # CTkToplevel ainda não está mapeado aqui: grab_set antes falha no Windows.
        win.after(150, lambda: (win.winfo_exists() and (win.grab_set(), win.focus())))

    def _refresh_dest_notice(self):
        """Atualiza o «Também grava em: …» da barra inferior."""
        if not hasattr(self, "_dest_lbl"):
            return   # painel de config avisa durante a montagem, antes da barra existir
        show, text, level = second_dest_notice(self.cfg)
        if not show:
            self._dest_lbl.grid_remove()
            return
        self._dest_var.set(text)
        self._dest_lbl.configure(
            text_color=WARN_COLOR if level == "warn" else ("gray50", "gray60"))
        self._dest_lbl.grid()

    # ── Reatividade ──────────────────────────────────────────────────────────

    def _on_change(self):
        entries = self.img_panel.entries
        engine  = ImpositionEngine(entries, self.cfg)
        n_pgs   = engine.total_pages()

        self.cfg_panel.update_info(engine.total_expanded(), n_pgs, engine)

        if n_pgs > 0:
            self._preview_idx = max(0, min(self._preview_idx, n_pgs - 1))

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

        idx = self._preview_idx

        def task():
            try:
                img = engine.preview_page(idx)
                self.after(0, lambda: self.preview_panel.update_preview(img, idx, n_pages))
            except Exception as e:
                self.after(0, lambda: self._status_var.set(f"Erro no preview: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def _nav_preview(self, delta: int):
        if not self.img_panel.entries:
            return
        n = ImpositionEngine(self.img_panel.entries, self.cfg).total_pages()
        if n:
            self._preview_idx = (self._preview_idx + delta) % n
            self._refresh_preview()

    # ── Gerador de .bat ──────────────────────────────────────────────────────

    def _make_bat(self, parent=None):
        script = str(Path(__file__).resolve())
        content = build_launcher_bat(script)
        dest = filedialog.asksaveasfilename(
            parent=parent or self,
            title="Salvar atalho .bat", defaultextension=".bat",
            initialfile="printimposer.bat", initialdir=shortcut_initial_dir(),
            filetypes=[("Arquivo de lote", "*.bat")])
        if not dest:
            return
        try:
            # ASCII puro + CRLF: é o que o console do Windows espera.
            Path(dest).write_text(content, encoding="ascii", newline="")
            messagebox.showinfo("Atalho criado",
                                f"Atalho salvo em:\n{dest}\n\n"
                                "Dê um duplo clique para abrir a ferramenta sem console.")
        except Exception as e:
            messagebox.showerror("Erro ao criar atalho", str(e))

    # ── Geração ──────────────────────────────────────────────────────────────

    def _start_generate(self):
        if self._generating:
            return
        if not self.img_panel.entries:
            messagebox.showwarning("Sem imagens",
                                   "Adicione pelo menos uma imagem antes de gerar.")
            return

        self.cfg_panel._on_output()
        if not self.cfg.output_dir:
            self.cfg.output_dir = default_output_dir()

        # Cópias congeladas: guarda de qualidade e geração veem o mesmo estado,
        # mesmo que o dono mexa na tela enquanto a thread trabalha.
        entries, cfg = snapshot_for_generation(self.img_panel.entries, self.cfg)

        # Aviso honesto antes de gastar tempo gerando algo que vai sair ruim.
        q = ImpositionEngine(entries, cfg).quality_report()
        if q["level"] == "bad":
            cw, ch = q["cell"]
            if not messagebox.askyesno(
                    "Qualidade baixa",
                    f"«{q['worst']}» cobre apenas {q['ratio']*100:.0f}% da célula.\n"
                    f"A impressão vai sair ampliada e menos nítida.\n\n"
                    f"Ideal: reexportar com pelo menos {cw}×{ch} px.\n\nGerar mesmo assim?"):
                return

        # Marcas que não cabem na margem / sangria que não cabe no vão: não sai
        # cortado pela metade em silêncio (mesmo espírito da guarda de qualidade).
        cut_msg = cut_confirm_text(cfg)
        if cut_msg and not messagebox.askyesno("Corte e sangria", cut_msg):
            return

        self._generating = True
        self._gen_btn.configure(state="disabled", text="Gerando…")
        self._prog_var.set(0)
        self._status_var.set("Iniciando geração…")
        threading.Thread(target=self._generate_worker, args=(entries, cfg),
                         daemon=True).start()

    def _generate_worker(self, entries: List[ImageEntry], cfg: LayoutConfig):
        try:
            engine = ImpositionEngine(entries, cfg)

            def prog_compose(done, total):
                self.after(0, lambda: self._prog_var.set((done / total) * 0.7))
                self.after(0, lambda: self._status_var.set(
                    f"Compondo folha {done}/{total}…"))

            pages = engine.generate_all(progress_cb=prog_compose)
            self.after(0, lambda: self._status_var.set("Salvando arquivos…"))

            def prog_save(done, total):
                self.after(0, lambda: self._prog_var.set(0.7 + (done / total) * 0.3))

            saved = engine.save(pages, progress_cb=prog_save)
            self.after(0, lambda: self._on_generate_done(saved))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.after(0, lambda: self._on_generate_error(str(e), tb))

    def _on_generate_done(self, saved: List[str]):
        self._generating = False
        self._gen_btn.configure(state="normal", text="Gerar Arquivos")
        self._prog_var.set(1.0)
        self._persist()   # config validada por um uso real: vale gravar

        if not saved:
            self._status_var.set("Nada foi salvo — verifique as pastas de saída.")
            messagebox.showwarning("Nada salvo",
                                   "Nenhum arquivo foi gravado. Confira as pastas de saída.")
            return

        folders = sorted({str(Path(p).parent) for p in saved})
        self._status_var.set(f"{len(saved)} arquivo(s) em {len(folders)} pasta(s)")
        msg = (f"{len(saved)} arquivo(s) gerado(s)!\n\n" +
               "\n".join(folders) + "\n\nAbrir a pasta?")
        if messagebox.askyesno("Concluído", msg):
            self._open_folder(folders[0])

    def _on_generate_error(self, err: str, tb: str):
        self._generating = False
        self._gen_btn.configure(state="normal", text="Gerar Arquivos")
        self._prog_var.set(0)
        self._status_var.set(f"Erro: {err}")
        messagebox.showerror("Erro ao gerar",
                             f"Ocorreu um erro durante a geração:\n\n{err}\n\n{tb[:400]}")

    @staticmethod
    def _open_folder(path: str):
        import subprocess, platform
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(path)          # type: ignore[attr-defined]
            elif system == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def enable_dpi_awareness():
    """Declara consciência de DPI no Windows.

    Sem isto, o SO escala a janela por bitmap em telas com zoom (125%/150%):
    texto borrado e geometria calculada em coordenadas erradas. Precisa rodar
    ANTES de criar qualquer janela. Ver HISTORY §6.
    """
    if sys.platform != "win32":
        return
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)   # System DPI aware
    except Exception:
        try:
            from ctypes import windll
            windll.user32.SetProcessDPIAware()    # Windows mais antigo
        except Exception:
            pass  # segue sem DPI awareness: degradação aceitável


def _show_startup_error(summary: str, log: Optional[Path]):
    """Janela de erro que não depende da janela que falhou.

    `Tk()` novo e escondido; se o próprio Tk caiu, `MessageBoxW` no Windows;
    se nada disso der, sobra o log.
    """
    title = f"{APP_NAME} — erro ao abrir"
    msg = f"O {APP_NAME} não conseguiu abrir.\n\n{summary}"
    if log:
        msg += f"\n\nDetalhes em:\n{log}"
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            messagebox.showerror(title, msg, parent=root)
        finally:
            root.destroy()
        return
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, title, 0x10)   # MB_ICONERROR
        except Exception:
            pass


def report_startup_error(exc: BaseException, notify=None) -> Optional[Path]:
    """Grava `last_error.log` e avisa o dono. Devolve o caminho do log (ou None).

    Via `.bat` (pythonw) não há console: sem isto o app simplesmente não abre
    e ninguém sabe por quê. O log cai em `SettingsStore.DIR`; se a pasta não
    puder ser criada, na pasta temporária do sistema. `notify(resumo, log)` é
    injetável para o teste não abrir janela.
    """
    import traceback, datetime
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    body = (f"Data/hora: {datetime.datetime.now().isoformat(timespec='seconds')}\n"
            f"Versão: {VERSION}\n"
            f"Python: {sys.version}\n"
            f"Executável: {sys.executable}\n\n{tb}")
    log: Optional[Path] = None
    for folder in (SettingsStore.DIR, Path(tempfile.gettempdir())):
        try:
            folder.mkdir(parents=True, exist_ok=True)
            candidate = folder / "last_error.log"
            candidate.write_text(body, encoding="utf-8")
            log = candidate
            break
        except Exception:
            continue
    lines = tb.strip().splitlines()
    summary = lines[-1] if lines else repr(exc)
    try:
        (notify or _show_startup_error)(summary, log)
    except Exception:
        pass   # relatar o erro nunca pode virar outro erro
    return log


def main():
    # Exception, não BaseException: fechar a janela ou Ctrl+C não é erro.
    try:
        enable_dpi_awareness()
        app = PrintImposerApp()
        app.mainloop()
    except Exception as exc:
        report_startup_error(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
