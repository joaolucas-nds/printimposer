#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrintImposer v1.2.0
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
"""

import os
import sys
import math
import json
import threading
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser

import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

from PIL import Image, ImageDraw, ImageTk


# ══════════════════════════════════════════════════════════════════════════════
# SUPORTE OPCIONAL A SVG
# ══════════════════════════════════════════════════════════════════════════════
# Pillow não rasteriza SVG. Tentamos dois back-ends, em ordem de fidelidade:
#   1. cairosvg  — melhor cobertura da spec, mas exige libcairo (nativo, chato no Windows)
#   2. svglib    — Python puro, sem dependência nativa; cobre o caso comum
# Se nenhum estiver disponível, SVG some da lista de formatos aceitos e o app
# segue funcionando normalmente. Dependência opcional nunca derruba a UI.

SVG_BACKEND: Optional[str] = None
_SVG_MODS: Dict[str, Any] = {}   # módulos do back-end escolhido, prontos para uso


def _probe_svg_backend() -> Optional[str]:
    """Descobre um back-end de SVG que realmente RENDERIZA.

    Importar a biblioteca não basta: `svglib` importa sem erro mas depende do
    `renderPM`, que por sua vez precisa de `rlPyCairo` ou da extensão C
    `_rl_renderPM`. Sem isso, o SVG seria aceito na lista de arquivos e só
    quebraria na hora de gerar a folha. Por isso sondamos com um render real
    de um SVG mínimo em memória — se não desenhar, o back-end não conta.
    """
    import io

    probe = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4" '
             b'width="4" height="4"><rect width="4" height="4" fill="#000"/></svg>')

    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(bytestring=probe, output_width=4)
        _SVG_MODS["cairosvg"] = cairosvg
        return "cairosvg"
    except Exception:
        pass

    try:
        from svglib.svglib import svg2rlg          # type: ignore
        from reportlab.graphics import renderPM    # type: ignore
        drawing = svg2rlg(io.BytesIO(probe))
        if drawing is not None:
            renderPM.drawToString(drawing, fmt="PNG")
            _SVG_MODS["svg2rlg"]  = svg2rlg
            _SVG_MODS["renderPM"] = renderPM
            return "svglib"
    except Exception:
        pass

    return None


SVG_BACKEND = _probe_svg_backend()


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

VERSION  = "1.2.0"
APP_NAME = "PrintImposer"
MM_TO_INCH = 1.0 / 25.4

RASTER_EXT = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp', '.gif'}
SVG_EXT    = {'.svg'} if SVG_BACKEND else set()
SUPPORTED_EXT = RASTER_EXT | SVG_EXT

THUMB_W, THUMB_H = 56, 56
PREVIEW_MAX = (460, 580)

# Teto da grade: acima disso as células ficam pequenas demais para uso real.
MAX_COLS, MAX_ROWS = 12, 12

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

# Atalhos de grade. NÃO são mais a única forma de escolher layout: os spinners
# de colunas/linhas aceitam qualquer combinação (DEC-009). Isto é só conveniência.
NUP_SHORTCUTS: Dict[str, Tuple[int, int]] = {
    "1 por folha  (1×1)":   (1, 1),
    "2 lado a lado (2×1)":  (2, 1),
    "2 empilhadas (1×2)":   (1, 2),
    "4 por folha  (2×2)":   (2, 2),
    "6 por folha  (3×2)":   (3, 2),
    "6 por folha  (2×3)":   (2, 3),
    "8 por folha  (4×2)":   (4, 2),
    "9 por folha  (3×3)":   (3, 3),
    "12 por folha (2×6)":   (2, 6),
    "12 por folha (4×3)":   (4, 3),
    "16 por folha (4×4)":   (4, 4),
}

LINE_STYLES  = ["Sólida", "Tracejada", "Pontilhada"]
FIT_LABELS   = ["Ajustar (fit)", "Preencher (fill)", "Esticar (stretch)"]
FIT_KEYS     = ["fit",           "fill",              "stretch"]
OUT_FORMATS  = ["PNG", "PDF", "JPEG", "TIFF"]   # PNG primeiro: é o padrão agora

# Limiares da guarda de qualidade (razão entre pixels da fonte e da célula).
QUALITY_OK   = 1.00   # fonte >= célula: sem upscale
QUALITY_WARN = 0.75   # abaixo disso a perda começa a aparecer na impressão

# Seções do accordion: chave estável (persistida) → estado inicial. Só "saida"
# nasce aberta: é a que muda a cada trabalho (SPEC-F3-UI §2 e §9).
SECTION_DEFAULTS: Dict[str, bool] = {
    "papel": False, "ajuste": False, "margens": False, "corte": False, "saida": True,
}

# Rótulos do menubar (SPEC-F3-UI §5). Uma fonte só: a montagem e os testes leem daqui.
MENU_TITLES = ("Arquivo", "Opções", "Ajuda")
MENU_LABELS: Dict[str, str] = {
    "add_files":     "Adicionar arquivos…",
    "add_folder":    "Adicionar pasta…",
    "clear":         "Limpar lista",
    "generate":      "Gerar arquivos",
    "open_out":      "Abrir pasta de saída",
    "quit":          "Sair",
    "presets":       "Presets",
    "save_preset":   "Salvar atual…",
    "delete_preset": "Excluir…",
    "make_bat":      "Criar atalho…",
    "reset":         "Restaurar configurações padrão",
    "guide":         "Guia rápido: Figma → impressão",
    "about":         "Sobre o PrintImposer",
}

# Guia rápido (Ajuda). O README continua sendo a versão longa deste texto.
QUICK_GUIDE = (
    "1. No Figma\n"
    "   Use frames A6 e exporte PNG com pelo menos 1240×1748 px\n"
    "   (ou SVG, se o cabeçalho do app mostrar um back-end de SVG).\n"
    "\n"
    "2. No PrintImposer\n"
    "   Adicione a pasta com as imagens, escolha a grade 2×2, confira o\n"
    "   selo de qualidade no rodapé do painel e clique em «Gerar Arquivos».\n"
    "\n"
    "3. Na impressora\n"
    "   Escolha «Tamanho real» / 100%. Nunca «ajustar à página»: isso\n"
    "   reescala a folha e as linhas de corte deixam de bater."
)


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTÊNCIA
# ══════════════════════════════════════════════════════════════════════════════

class SettingsStore:
    """Lê e grava configuração e presets em ~/.printimposer/.

    Falha silenciosamente: se o disco não colaborar, o app abre com os padrões
    em vez de quebrar. Persistência é conveniência, não requisito.
    """

    DIR      = Path.home() / ".printimposer"
    SETTINGS = DIR / "settings.json"
    PRESETS  = DIR / "presets.json"

    @classmethod
    def _ensure_dir(cls) -> bool:
        try:
            cls.DIR.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    @classmethod
    def load_settings(cls) -> dict:
        try:
            if cls.SETTINGS.exists():
                return json.loads(cls.SETTINGS.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    @classmethod
    def save_settings(cls, data: dict) -> bool:
        if not cls._ensure_dir():
            return False
        try:
            cls.SETTINGS.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return True
        except Exception:
            return False

    @classmethod
    def load_presets(cls) -> Dict[str, dict]:
        try:
            if cls.PRESETS.exists():
                d = json.loads(cls.PRESETS.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    return d
        except Exception:
            pass
        return {}

    @classmethod
    def save_presets(cls, presets: Dict[str, dict]) -> bool:
        if not cls._ensure_dir():
            return False
        try:
            cls.PRESETS.write_text(
                json.dumps(presets, indent=2, ensure_ascii=False), encoding="utf-8")
            return True
        except Exception:
            return False


def normalize_sections_open(raw: Any) -> Dict[str, bool]:
    """Estado do accordion a partir do que veio do settings.json.

    Chave ausente cai no padrão; chave desconhecida e valor que não é booleano
    são ignorados. Arquivo da 1.1.x (sem `sections_open`) devolve o padrão.
    """
    state = dict(SECTION_DEFAULTS)
    if isinstance(raw, dict):
        for key in SECTION_DEFAULTS:
            if isinstance(raw.get(key), bool):
                state[key] = raw[key]
    return state


def shortcut_initial_dir() -> str:
    """Pasta onde o seletor do atalho .bat abre: a PAI da raiz do projeto.

    O dono prefere o .bat fora da área de trabalho, numa pasta acima do projeto
    (SPEC-F3-UI §6). Se ela não existir, cai para a home.
    """
    parent = Path(__file__).resolve().parent.parent
    return str(parent if parent.is_dir() else Path.home())


def default_output_dir() -> str:
    """Pasta de saída inicial: Downloads, com Desktop e home como reserva."""
    for candidate in (Path.home() / "Downloads", Path.home() / "Desktop", Path.home()):
        if candidate.is_dir():
            return str(candidate)
    return str(Path.home())


# ══════════════════════════════════════════════════════════════════════════════
# CARREGAMENTO DE IMAGEM
# ══════════════════════════════════════════════════════════════════════════════

def rasterize_svg(path: str, box_w: int, box_h: int) -> Image.Image:
    """Rasteriza um SVG dentro da caixa (box_w × box_h), preservando a proporção.

    O ganho central: como o desenho é recalculado na resolução da célula, um SVG
    nunca sofre upscale — imprime nítido em qualquer DPI. É a razão de o SVG ter
    sido antecipado da F3 para a F2.
    """
    import io

    if SVG_BACKEND == "cairosvg":
        cairosvg = _SVG_MODS["cairosvg"]
        # Rasteriza pela largura; se estourar a altura, refaz limitando pela altura.
        png = cairosvg.svg2png(url=path, output_width=box_w)
        img = Image.open(io.BytesIO(png)).convert("RGBA")
        if img.height > box_h:
            png = cairosvg.svg2png(url=path, output_height=box_h)
            img = Image.open(io.BytesIO(png)).convert("RGBA")
        return img

    if SVG_BACKEND == "svglib":
        svg2rlg  = _SVG_MODS["svg2rlg"]
        renderPM = _SVG_MODS["renderPM"]
        drawing = svg2rlg(path)
        if drawing is None:
            raise ValueError("SVG ilegível")
        # svglib desenha no tamanho intrínseco; escalamos o desenho antes do render.
        dw = float(drawing.width) or 1.0
        dh = float(drawing.height) or 1.0
        scale = min(box_w / dw, box_h / dh)
        drawing.width  = dw * scale
        drawing.height = dh * scale
        drawing.scale(scale, scale)
        buf = io.BytesIO()
        renderPM.drawToFile(drawing, buf, fmt="PNG", bg=0xFFFFFF)
        buf.seek(0)
        return Image.open(buf).convert("RGBA")

    raise RuntimeError("Nenhum back-end de SVG disponível")


def is_svg(path: str) -> bool:
    return Path(path).suffix.lower() == ".svg"


def open_source(path: str, box_w: int = 0, box_h: int = 0) -> Image.Image:
    """Abre uma imagem-fonte. SVG é rasterizado na caixa pedida; raster abre direto."""
    if is_svg(path):
        if box_w <= 0 or box_h <= 0:
            box_w = box_h = 1000  # tamanho de cortesia para inspeção/miniatura
        return rasterize_svg(path, box_w, box_h)
    return Image.open(path).convert("RGBA")


# ══════════════════════════════════════════════════════════════════════════════
# MODELO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

class ImageEntry:
    """Uma imagem da lista, com sua quantidade de cópias e miniatura."""

    # Cache de miniatura por (caminho, mtime): evita reprocessar ao reordenar
    # ou mexer na quantidade. Ver HISTORY §8 (otimização segura).
    _thumb_cache: Dict[Tuple[str, float], Image.Image] = {}

    def __init__(self, path: str):
        self.path     = path
        self.filename = Path(path).name
        self.quantity = 1
        self.src_size: Optional[Tuple[int, int]] = None   # px da fonte (None p/ SVG)
        self.pil_thumb: Optional[Image.Image] = None
        self._load_thumb()

    def _load_thumb(self):
        try:
            key = (self.path, os.path.getmtime(self.path))
        except OSError:
            key = (self.path, 0.0)

        cached = ImageEntry._thumb_cache.get(key)
        if cached is not None:
            self.pil_thumb = cached
            return

        try:
            if is_svg(self.path):
                img = rasterize_svg(self.path, THUMB_W * 3, THUMB_H * 3)
                self.src_size = None          # vetor: não tem tamanho nativo em px
            else:
                img = Image.open(self.path)
                # draft() faz o decodificador JPEG entregar já reduzido (1/2, 1/4, 1/8).
                # Ignorado silenciosamente nos demais formatos — seguro por construção.
                try:
                    img.draft("RGB", (THUMB_W * 4, THUMB_H * 4))
                except Exception:
                    pass
                img = img.convert("RGBA")
                self.src_size = img.size

            img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)

            bg = Image.new("RGB", (THUMB_W, THUMB_H), (50, 50, 60))
            x = (THUMB_W - img.width)  // 2
            y = (THUMB_H - img.height) // 2
            bg.paste(img, (x, y), img.split()[3] if img.mode == "RGBA" else None)

            self.pil_thumb = bg
            ImageEntry._thumb_cache[key] = bg
        except Exception:
            self.pil_thumb = None

    def real_size(self) -> Optional[Tuple[int, int]]:
        """Tamanho real da fonte em px, sem decodificar a imagem inteira."""
        if self.src_size:
            return self.src_size
        if is_svg(self.path):
            return None
        try:
            with Image.open(self.path) as im:
                self.src_size = im.size
                return self.src_size
        except Exception:
            return None


class LayoutConfig:
    """Estado completo de configuração. Serializa para JSON (presets e settings)."""

    # Campos que compõem um preset nomeado (tudo menos caminhos de pasta).
    PRESET_FIELDS = (
        "cols", "rows", "paper_key", "paper_w_mm", "paper_h_mm", "dpi",
        "margin_outer_mm", "margin_between_mm", "bg_color", "fit_mode",
        "auto_rotate", "cut_lines", "cut_color", "cut_width_px", "cut_style",
        "cut_dash", "output_format", "output_prefix", "output_suffix",
    )

    def __init__(self):
        # Grade livre (DEC-009): não há mais lista fechada de layouts.
        self.cols:              int   = 2
        self.rows:              int   = 2
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
        self.output_format:     str   = "PNG"          # PNG é o padrão agora
        self.output_prefix:     str   = "folha_"
        self.output_suffix:     str   = ""
        # Pastas independentes: abrir imagens não mexe em onde salvar.
        self.input_dir:         str   = str(Path.home())
        self.output_dir:        str   = default_output_dir()
        self.output_dir2:       str   = ""             # destino extra opcional
        self.output_dir2_on:    bool  = False

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def from_dict(self, d: dict):
        for k, v in d.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def preset_dict(self) -> dict:
        """Só os campos de layout — um preset não carrega caminhos de pasta."""
        return {k: getattr(self, k) for k in self.PRESET_FIELDS}

    def nup(self) -> int:
        return max(1, self.cols) * max(1, self.rows)


# ══════════════════════════════════════════════════════════════════════════════
# MOTOR DE IMPOSIÇÃO
# ══════════════════════════════════════════════════════════════════════════════

class ImpositionEngine:
    """Compõe as folhas. Não depende de Tkinter — testável headless (DEC-004)."""

    def __init__(self, entries: List[ImageEntry], cfg: LayoutConfig):
        self.entries = entries
        self.cfg     = cfg

    # ── Geometria ────────────────────────────────────────────────────────────

    def _mm_px(self, mm: float, dpi: Optional[int] = None) -> int:
        """Converte mm para px. O `dpi` explícito existe para NÃO mutar cfg.dpi:
        preview e geração rodam em threads distintas sobre o mesmo LayoutConfig."""
        return max(0, int(round(mm * (dpi or self.cfg.dpi) * MM_TO_INCH)))

    def _page_px(self, dpi: Optional[int] = None) -> Tuple[int, int]:
        return (self._mm_px(self.cfg.paper_w_mm, dpi),
                self._mm_px(self.cfg.paper_h_mm, dpi))

    def _grid(self) -> Tuple[int, int]:
        return max(1, self.cfg.cols), max(1, self.cfg.rows)

    def cell_px(self, dpi: Optional[int] = None) -> Tuple[int, int]:
        """Tamanho da célula em pixels. Base da guarda de qualidade e da composição."""
        cols, rows = self._grid()
        pw, ph = self._page_px(dpi)
        mo = self._mm_px(self.cfg.margin_outer_mm, dpi)
        mb = self._mm_px(self.cfg.margin_between_mm, dpi)
        cw = max(1, (pw - 2*mo - (cols-1)*mb) // cols)
        ch = max(1, (ph - 2*mo - (rows-1)*mb) // rows)
        return cw, ch

    def cell_mm(self) -> Tuple[float, float]:
        cols, rows = self._grid()
        cw = (self.cfg.paper_w_mm - 2*self.cfg.margin_outer_mm
              - (cols-1)*self.cfg.margin_between_mm) / cols
        ch = (self.cfg.paper_h_mm - 2*self.cfg.margin_outer_mm
              - (rows-1)*self.cfg.margin_between_mm) / rows
        return max(0.0, cw), max(0.0, ch)

    # ── Contagem ─────────────────────────────────────────────────────────────

    def _expand(self) -> List[str]:
        out = []
        for e in self.entries:
            out.extend([e.path] * max(1, e.quantity))
        return out

    def total_expanded(self) -> int:
        return len(self._expand())

    def total_pages(self) -> int:
        paths = self._expand()
        if not paths:
            return 0
        return math.ceil(len(paths) / self.cfg.nup())

    # ── Guarda de qualidade ──────────────────────────────────────────────────

    def quality_report(self) -> dict:
        """Compara pixels da fonte com a célula e classifica o risco de upscale.

        Retorna {'level': 'ok'|'warn'|'bad'|'none', 'ratio': float, 'worst': str,
                 'cell': (w,h), 'needed': (w,h)}.
        SVG é ignorado: rasteriza na resolução da célula, então nunca dá upscale.
        """
        cw, ch = self.cell_px()
        worst_ratio = None
        worst_name  = ""

        for e in self.entries:
            if is_svg(e.path):
                continue
            size = e.real_size()
            if not size:
                continue
            # Auto-Rotate pode girar a imagem; considera a orientação mais favorável.
            ratios = [min(size[0] / cw, size[1] / ch)]
            if self.cfg.auto_rotate:
                ratios.append(min(size[1] / cw, size[0] / ch))
            r = max(ratios)
            if worst_ratio is None or r < worst_ratio:
                worst_ratio, worst_name = r, e.filename

        if worst_ratio is None:
            return {"level": "none", "ratio": 0.0, "worst": "",
                    "cell": (cw, ch), "needed": (cw, ch)}

        level = ("ok"   if worst_ratio >= QUALITY_OK else
                 "warn" if worst_ratio >= QUALITY_WARN else "bad")
        return {"level": level, "ratio": worst_ratio, "worst": worst_name,
                "cell": (cw, ch), "needed": (cw, ch)}

    # ── Composição ───────────────────────────────────────────────────────────

    @staticmethod
    def _hex_rgb(h: str) -> Tuple[int, int, int]:
        h = (h or "#FFFFFF").lstrip('#')
        try:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except ValueError:
            return 255, 255, 255

    def _place_image(self, img: Image.Image, cw: int, ch: int,
                     bg: Tuple[int, int, int]) -> Image.Image:
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

        scale = (max(cw / iw, ch / ih) if cfg.fit_mode == "fill"
                 else min(cw / iw, ch / ih))
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        img = img.resize((nw, nh), Image.LANCZOS)

        if cfg.fit_mode == "fill":
            l = (nw - cw) // 2
            t = (nh - ch) // 2
            img = img.crop((l, t, l + cw, t + ch))
            cell.paste(img.convert("RGB"), (0, 0))
        else:
            mask = img.split()[3] if img.mode == "RGBA" else None
            cell.paste(img.convert("RGB"), ((cw - nw) // 2, (ch - nh) // 2), mask)

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
                    if on:
                        draw.line([(x1, y), (x2, min(y + dash, y2))], fill=col, width=lw)
                    y += dash; on = not on
            else:
                x, on = x1, True
                while x <= x2:
                    if on:
                        draw.line([(x, y1), (min(x + dash, x2), y2)], fill=col, width=lw)
                    x += dash; on = not on

        def dotted(x1, y1, x2, y2):
            r, gap = max(1, lw), max(1, lw) * 4
            if x1 == x2:
                y = y1
                while y <= y2:
                    draw.ellipse([(x1 - r, y - r), (x1 + r, y + r)], fill=col)
                    y += gap
            else:
                x = x1
                while x <= x2:
                    draw.ellipse([(x - r, y1 - r), (x + r, y1 + r)], fill=col)
                    x += gap

        fn = {"Sólida": solid, "Tracejada": dashed, "Pontilhada": dotted}.get(
            cfg.cut_style, solid)

        for c in range(1, cols):
            x = mo + c * cw + (c - 1) * mb + (mb // 2 if mb > 0 else 0)
            fn(x, 0, x, ph)
        for r in range(1, rows):
            y = mo + r * ch + (r - 1) * mb + (mb // 2 if mb > 0 else 0)
            fn(0, y, pw, y)

    def compose_page(self, page_idx: int, image_paths: List[str],
                     override_dpi: Optional[int] = None) -> Image.Image:
        """Compõe uma folha no DPI pedido (ou no do config).
        NÃO muta `cfg.dpi`. A versão anterior trocava o valor e restaurava num
        `finally` — correto em uso sequencial, mas preview e geração rodam em
        threads distintas sobre o MESMO LayoutConfig: gerar enquanto o preview
        compunha produzia a folha em 72 DPI, silenciosamente. Ver FIX-004.
        """
        cfg = self.cfg
        cols, rows = self._grid()
        nup    = cols * rows
        pw, ph = self._page_px(override_dpi)
        mo     = self._mm_px(cfg.margin_outer_mm, override_dpi)
        mb     = self._mm_px(cfg.margin_between_mm, override_dpi)
        cw, ch = self.cell_px(override_dpi)

        bg   = self._hex_rgb(cfg.bg_color)
        page = Image.new("RGB", (pw, ph), bg)

        start = page_idx * nup
        for slot in range(nup):
            idx = start + slot
            if idx >= len(image_paths):
                break

            col = slot % cols
            row = slot // cols
            x   = mo + col * (cw + mb)
            y   = mo + row * (ch + mb)

            try:
                # SVG rasteriza direto no tamanho da célula: zero upscale.
                img  = open_source(image_paths[idx], cw, ch)
                cell = self._place_image(img, cw, ch, bg)
            except Exception:
                cell = Image.new("RGB", (cw, ch), (200, 190, 190))
                ImageDraw.Draw(cell).text(
                    (4, max(0, ch // 2 - 8)), "Erro ao carregar", fill=(160, 30, 30))

            page.paste(cell, (x, y))

        if cfg.cut_lines:
            self._draw_cuts(page, cols, rows, cw, ch, mo, mb)

        return page

    def generate_all(self, progress_cb=None) -> List[Image.Image]:
        paths = self._expand()
        n_pages = max(1, math.ceil(len(paths) / self.cfg.nup()))
        pages = []
        for i in range(n_pages):
            pages.append(self.compose_page(i, paths))
            if progress_cb:
                progress_cb(i + 1, n_pages)
        return pages

    def preview_page(self, page_idx: int) -> Image.Image:
        preview = self.compose_page(page_idx, self._expand(), override_dpi=72)
        preview.thumbnail(PREVIEW_MAX, Image.LANCZOS)
        return preview

    # ── Saída ────────────────────────────────────────────────────────────────

    def output_dirs(self) -> List[str]:
        """Destinos de gravação — um ou dois, sem duplicar o mesmo caminho."""
        dirs = [self.cfg.output_dir or default_output_dir()]
        if self.cfg.output_dir2_on and self.cfg.output_dir2:
            if os.path.normpath(self.cfg.output_dir2) != os.path.normpath(dirs[0]):
                dirs.append(self.cfg.output_dir2)
        return dirs

    def save(self, pages: List[Image.Image], progress_cb=None) -> List[str]:
        cfg   = self.cfg
        fmt   = cfg.output_format
        ext   = {"PDF": "pdf", "PNG": "png", "JPEG": "jpg", "TIFF": "tif"}[fmt]
        saved: List[str] = []

        targets = self.output_dirs()
        total_steps = max(1, len(targets) * (1 if fmt == "PDF" else len(pages)))
        step = 0

        for out_dir in targets:
            try:
                os.makedirs(out_dir, exist_ok=True)
            except Exception:
                continue

            def unique_path(name: str) -> str:
                p = os.path.join(out_dir, name)
                if not os.path.exists(p):
                    return p
                base, ext_ = os.path.splitext(name)
                i = 2
                while True:
                    cand = os.path.join(out_dir, f"{base}_{i}{ext_}")
                    if not os.path.exists(cand):
                        return cand
                    i += 1

            if fmt == "PDF":
                fpath = unique_path(f"{cfg.output_prefix}001{cfg.output_suffix}.pdf")
                if len(pages) == 1:
                    pages[0].save(fpath, "PDF", resolution=cfg.dpi)
                else:
                    pages[0].save(fpath, "PDF", resolution=cfg.dpi,
                                  save_all=True, append_images=pages[1:])
                saved.append(fpath)
                step += 1
                if progress_cb:
                    progress_cb(step, total_steps)
            else:
                for i, page in enumerate(pages):
                    fpath = unique_path(
                        f"{cfg.output_prefix}{i+1:03d}{cfg.output_suffix}.{ext}")
                    if fmt == "JPEG":
                        page.convert("RGB").save(fpath, "JPEG", quality=95,
                                                 dpi=(cfg.dpi, cfg.dpi))
                    elif fmt == "TIFF":
                        page.save(fpath, "TIFF", dpi=(cfg.dpi, cfg.dpi),
                                  compression="lzw")
                    else:
                        page.save(fpath, "PNG", dpi=(cfg.dpi, cfg.dpi))
                    saved.append(fpath)
                    step += 1
                    if progress_cb:
                        progress_cb(step, total_steps)

        return saved


# ══════════════════════════════════════════════════════════════════════════════
# GERADOR DE .BAT
# ══════════════════════════════════════════════════════════════════════════════

def build_launcher_bat(script_path: str) -> str:
    """Monta o conteúdo de um .bat que abre a GUI sem janela de console.

    Todo o texto sai em ASCII puro de propósito: o console do Windows usa
    codepage legado (cp850/cp437) e corrompe acentos vindos de arquivo UTF-8.
    """
    exe = Path(sys.executable)
    # pythonw.exe é o interpretador sem console. Se não existir (caso raro),
    # cai para o python.exe normal — melhor abrir com console do que não abrir.
    pyw = exe.with_name("pythonw.exe")
    interp = str(pyw) if pyw.exists() else str(exe)
    workdir = str(Path(script_path).parent)

    return (
        "@echo off\r\n"
        "rem ===========================================================================\r\n"
        f"rem  {APP_NAME} v{VERSION} - abre a interface grafica (UI).\r\n"
        "rem  Copie este .bat para onde quiser (area de trabalho, etc.) para acesso rapido.\r\n"
        "rem  Sem janela de console (pythonw). Ajuste os caminhos se mover a ferramenta.\r\n"
        "rem  Gerado automaticamente pela propria ferramenta.\r\n"
        "rem ===========================================================================\r\n"
        f'start "" /d "{workdir}" "{interp}" "{script_path}"\r\n'
    )


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


# ══════════════════════════════════════════════════════════════════════════════
# WIDGET: LINHA DE IMAGEM
# ══════════════════════════════════════════════════════════════════════════════

class ImageRow(ctk.CTkFrame):
    """Uma linha na lista: miniatura, nome, quantidade e botões de ação."""

    def __init__(self, master, entry: ImageEntry, idx: int,
                 on_remove, on_change, on_move_up, on_move_down, **kw):
        super().__init__(master, fg_color=("gray85", "#2a2a3a"), corner_radius=6, **kw)
        self.entry        = entry
        self.idx          = idx
        self.on_remove    = on_remove
        self.on_change    = on_change
        self.on_move_up   = on_move_up
        self.on_move_down = on_move_down
        self._build()

    def _build(self):
        self.columnconfigure(2, weight=1)

        self.tk_img = None
        if self.entry.pil_thumb:
            # CTkImage, não PhotoImage: só ele reescala em telas 125%/150%.
            self.tk_img = ctk.CTkImage(light_image=self.entry.pil_thumb,
                                       dark_image=self.entry.pil_thumb,
                                       size=(THUMB_W, THUMB_H))
            lbl_img = ctk.CTkLabel(self, image=self.tk_img, text="")
        else:
            lbl_img = ctk.CTkLabel(self, text="?", font=ctk.CTkFont(size=22))
        lbl_img.grid(row=0, column=0, rowspan=2, padx=(6, 4), pady=4)

        name = self.entry.filename
        if len(name) > 28:
            name = name[:25] + "…"
        tag = "  [SVG]" if is_svg(self.entry.path) else ""
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
    def __init__(self, master, cfg: LayoutConfig, on_change, **kw):
        super().__init__(master, **kw)
        self.cfg       = cfg
        self.on_change = on_change
        self.entries: List[ImageEntry] = []
        self._rows: List[ImageRow] = []
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
                      command=self._add_folder).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, label_text="")
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=4)
        self.scroll.columnconfigure(0, weight=1)

        self.info_var = tk.StringVar(value="Nenhuma imagem selecionada")
        ctk.CTkLabel(self, textvariable=self.info_var, font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).grid(
            row=3, column=0, sticky="w", padx=10, pady=(2, 6))

    # ── Ações ────────────────────────────────────────────────────────────────

    def _filetypes(self):
        pats = " ".join("*" + e for e in sorted(SUPPORTED_EXT))
        types = [("Imagens", pats)]
        if SVG_BACKEND:
            types.append(("SVG", "*.svg"))
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

    def _ingest(self, paths):
        added = 0
        for f in paths:
            if Path(f).suffix.lower() in SUPPORTED_EXT:
                self.entries.append(ImageEntry(f))
                added += 1
        if added:
            self._refresh_rows()
            self.on_change()

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
                           on_move_up=self._move_up, on_move_down=self._move_down)
            row.grid(row=i, column=0, sticky="ew", padx=2, pady=2)
            self._rows.append(row)

        if self.entries:
            total = sum(e.quantity for e in self.entries)
            self.info_var.set(f"{len(self.entries)} arquivo(s) · {total} cópias no total")
        else:
            self.info_var.set("Nenhuma imagem selecionada")


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
                 on_sections_change=None, **kw):
        super().__init__(master, **kw)
        self.cfg       = cfg
        self.on_change = on_change
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
        """Zona fixa do topo: a grade muda a cada trabalho, fica sempre à vista."""
        f.columnconfigure(1, weight=1)
        ctk.CTkLabel(f, text="Grade (colunas × linhas)", anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 2))

        grid_box = ctk.CTkFrame(f, fg_color="transparent")
        grid_box.grid(row=1, column=0, columnspan=2, sticky="ew")

        spin_col = ctk.CTkFrame(grid_box, fg_color="transparent")
        spin_col.pack(side="left", padx=(0, 8))

        self._cols_var = tk.StringVar(value=str(self.cfg.cols))
        self._rows_var = tk.StringVar(value=str(self.cfg.rows))

        for label, var, delta_fn in (("Colunas", self._cols_var, "cols"),
                                     ("Linhas",  self._rows_var, "rows")):
            line = ctk.CTkFrame(spin_col, fg_color="transparent")
            line.pack(anchor="w", pady=1)
            ctk.CTkLabel(line, text=f"{label}:", width=54, anchor="w",
                         font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkButton(line, text="-", width=24, height=24,
                          command=lambda a=delta_fn: self._bump(a, -1)).pack(side="left")
            ctk.CTkEntry(line, textvariable=var, width=42, justify="center",
                         font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            ctk.CTkButton(line, text="+", width=24, height=24,
                          command=lambda a=delta_fn: self._bump(a, +1)).pack(side="left")

        ctk.CTkButton(spin_col, text="Aplicar valores digitados", height=24,
                      font=ctk.CTkFont(size=10),
                      command=self._apply_typed_grid).pack(anchor="w", pady=(4, 0))

        self.grid_preview = GridPreview(grid_box)
        self.grid_preview.pack(side="left")
        self.grid_preview.draw(self.cfg.cols, self.cfg.rows)

        self._lbl(f, "Atalhos:", 2)
        self._shortcut_var = tk.StringVar(value="—")
        ctk.CTkOptionMenu(f, variable=self._shortcut_var,
                          values=["—"] + list(NUP_SHORTCUTS.keys()),
                          command=self._on_shortcut, width=170).grid(
            row=2, column=1, sticky="w", padx=4)

    def _build_summary_zone(self, f):
        """Zona fixa de baixo: feedback (contador, célula, qualidade), não config."""
        self._sheet_info_var = tk.StringVar(value="")
        ctk.CTkLabel(f, textvariable=self._sheet_info_var, anchor="w",
                     font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=(2, 0))

        self._cell_var = tk.StringVar(value="")
        ctk.CTkLabel(f, textvariable=self._cell_var, anchor="w",
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).grid(
            row=1, column=0, sticky="w", padx=8)

        self._qual_var = tk.StringVar(value="")
        self._qual_lbl = ctk.CTkLabel(f, textvariable=self._qual_var, anchor="w",
                                      justify="left", wraplength=290,
                                      font=ctk.CTkFont(size=10))
        self._qual_lbl.grid(row=2, column=0, sticky="nw", padx=8)
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

        self._lbl(f3, "Entre imagens (mm):", 1)
        self._mb_var = tk.StringVar(value=str(self.cfg.margin_between_mm))
        self._num_entry(f3, self._mb_var, 1, cb=lambda _: self._on_margins())

        self._lbl(f3, "Cor de fundo:", 2)
        self._bg_btn = ctk.CTkButton(f3, text="       ", width=65,
                                     fg_color=self.cfg.bg_color, command=self._pick_bg)
        self._bg_btn.grid(row=2, column=1, sticky="w", padx=4, pady=2)

        # ── CORTE ──
        f4 = self._acc_section("corte", "Linhas de corte")
        self._cuts_var = tk.BooleanVar(value=self.cfg.cut_lines)
        ctk.CTkCheckBox(f4, text="Habilitar linhas de corte", variable=self._cuts_var,
                        command=self._on_cuts).grid(row=0, column=0, columnspan=2,
                                                    sticky="w", padx=4, pady=2)
        self._lbl(f4, "Estilo:", 1)
        self._cut_style_var = tk.StringVar(value=self.cfg.cut_style)
        ctk.CTkOptionMenu(f4, variable=self._cut_style_var, values=LINE_STYLES,
                          command=lambda _: self._on_cut_opts(), width=120).grid(
            row=1, column=1, sticky="w", padx=4)

        self._lbl(f4, "Espessura (px):", 2)
        self._cut_w_var = tk.StringVar(value=str(self.cfg.cut_width_px))
        self._num_entry(f4, self._cut_w_var, 2, cb=lambda _: self._on_cut_opts())

        self._lbl(f4, "Comprimento traço:", 3)
        self._cut_dash_var = tk.StringVar(value=str(self.cfg.cut_dash))
        self._num_entry(f4, self._cut_dash_var, 3, cb=lambda _: self._on_cut_opts())

        self._lbl(f4, "Cor da linha:", 4)
        self._cut_col_btn = ctk.CTkButton(f4, text="       ", width=65,
                                          fg_color=self.cfg.cut_color,
                                          command=self._pick_cut_color)
        self._cut_col_btn.grid(row=4, column=1, sticky="w", padx=4, pady=2)

        # ── SAÍDA ──
        f5 = self._acc_section("saida", "Saída")
        self._lbl(f5, "Formato:", 0)
        self._fmt_var = tk.StringVar(value=self.cfg.output_format)
        ctk.CTkOptionMenu(f5, variable=self._fmt_var, values=OUT_FORMATS,
                          command=lambda _: self._on_output(), width=100).grid(
            row=0, column=1, sticky="w", padx=4)

        self._lbl(f5, "Prefixo:", 1)
        self._pfx_var = tk.StringVar(value=self.cfg.output_prefix)
        self._num_entry(f5, self._pfx_var, 1, width=130, cb=lambda _: self._on_output())

        self._lbl(f5, "Sufixo:", 2)
        self._sfx_var = tk.StringVar(value=self.cfg.output_suffix)
        self._num_entry(f5, self._sfx_var, 2, width=130, cb=lambda _: self._on_output())

        ctk.CTkLabel(f5, text="Pasta de saída:", anchor="w",
                     font=ctk.CTkFont(size=11)).grid(row=3, column=0, columnspan=2,
                                                     sticky="w", padx=4, pady=(6, 0))
        dir_row = ctk.CTkFrame(f5, fg_color="transparent")
        dir_row.grid(row=4, column=0, columnspan=2, sticky="ew", padx=4)
        dir_row.columnconfigure(0, weight=1)
        self._dir_var = tk.StringVar(value=self.cfg.output_dir)
        ctk.CTkEntry(dir_row, textvariable=self._dir_var,
                     font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(dir_row, text="…", width=30,
                      command=self._pick_dir).grid(row=0, column=1, padx=(4, 0))

        self._dir2_on_var = tk.BooleanVar(value=self.cfg.output_dir2_on)
        ctk.CTkCheckBox(f5, text="Salvar também em um segundo destino",
                        variable=self._dir2_on_var, command=self._on_output).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=4, pady=(6, 0))

        dir2_row = ctk.CTkFrame(f5, fg_color="transparent")
        dir2_row.grid(row=6, column=0, columnspan=2, sticky="ew", padx=4)
        dir2_row.columnconfigure(0, weight=1)
        self._dir2_var = tk.StringVar(value=self.cfg.output_dir2)
        ctk.CTkEntry(dir2_row, textvariable=self._dir2_var,
                     font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(dir2_row, text="…", width=30,
                      command=self._pick_dir2).grid(row=0, column=1, padx=(4, 0))

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
        self.grid_preview.draw(self.cfg.cols, self.cfg.rows)
        self._shortcut_var.set(self._matching_shortcut())
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
                          (self._mb_var, "margin_between_mm")):
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
        self.cfg.cut_lines = self._cuts_var.get()
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
        self.cfg.output_prefix  = self._pfx_var.get()
        self.cfg.output_suffix  = self._sfx_var.get()
        self.cfg.output_dir     = self._dir_var.get()
        self.cfg.output_dir2    = self._dir2_var.get()
        self.cfg.output_dir2_on = self._dir2_on_var.get()

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
        self.grid_preview.draw(c.cols, c.rows)
        self._shortcut_var.set(self._matching_shortcut())
        self._fit_var.set(FIT_LABELS[FIT_KEYS.index(c.fit_mode)])
        self._auto_var.set(c.auto_rotate)
        self._paper_var.set(c.paper_key)
        self._pw_var.set(str(c.paper_w_mm)); self._ph_var.set(str(c.paper_h_mm))
        self._dpi_var.set(str(c.dpi))
        self._mo_var.set(str(c.margin_outer_mm)); self._mb_var.set(str(c.margin_between_mm))
        self._bg_btn.configure(fg_color=c.bg_color)
        self._cuts_var.set(c.cut_lines)
        self._cut_style_var.set(c.cut_style)
        self._cut_w_var.set(str(c.cut_width_px)); self._cut_dash_var.set(str(c.cut_dash))
        self._cut_col_btn.configure(fg_color=c.cut_color)
        self._fmt_var.set(c.output_format)
        self._pfx_var.set(c.output_prefix); self._sfx_var.set(c.output_suffix)
        self._dir_var.set(c.output_dir); self._dir2_var.set(c.output_dir2)
        self._dir2_on_var.set(c.output_dir2_on)

    def update_info(self, n_images: int, n_pages: int, engine: "ImpositionEngine"):
        """Atualiza contadores, tamanho de célula e a guarda de qualidade."""
        self._sheet_info_var.set(
            f"{n_images} imagem(ns) · {self.cfg.nup()} por folha · {n_pages} folha(s)")

        cw_mm, ch_mm = engine.cell_mm()
        cw_px, ch_px = engine.cell_px()
        self._cell_var.set(
            f"Célula: {cw_mm:.1f} × {ch_mm:.1f} mm  ({cw_px} × {ch_px} px @ {self.cfg.dpi} DPI)")

        q = engine.quality_report()
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

class PrintImposerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")

        self.cfg = LayoutConfig()
        self._load_persisted()

        self._preview_idx = 0
        self._preview_job = None
        self._generating  = False

        self._setup_geometry()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._on_change()

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
        ctk.CTkLabel(header, text=f"v{VERSION}   ·   {svg_note}",
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray50")).pack(side="right", padx=14)

        self._pane = tk.PanedWindow(self, orient="horizontal", sashwidth=5,
                                    bg="#2a2a3a", sashrelief="flat")
        self._pane.grid(row=1, column=0, sticky="nsew")

        # ARMADILHA nº1 (FIX-001): widget CTk com canvas interno não pode ir
        # direto para o PanedWindow — sempre um tk.Frame neutro de permeio.
        list_outer = tk.Frame(self._pane, bg="#2a2a3a")
        list_outer.rowconfigure(0, weight=1); list_outer.columnconfigure(0, weight=1)
        self.img_panel = ImageListPanel(list_outer, self.cfg, on_change=self._on_change)
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
        win.title("Guia rápido: Figma → impressão")
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

        # Aviso honesto antes de gastar tempo gerando algo que vai sair ruim.
        q = ImpositionEngine(self.img_panel.entries, self.cfg).quality_report()
        if q["level"] == "bad":
            cw, ch = q["cell"]
            if not messagebox.askyesno(
                    "Qualidade baixa",
                    f"«{q['worst']}» cobre apenas {q['ratio']*100:.0f}% da célula.\n"
                    f"A impressão vai sair ampliada e menos nítida.\n\n"
                    f"Ideal: reexportar com pelo menos {cw}×{ch} px.\n\nGerar mesmo assim?"):
                return

        self._generating = True
        self._gen_btn.configure(state="disabled", text="Gerando…")
        self._prog_var.set(0)
        self._status_var.set("Iniciando geração…")
        threading.Thread(target=self._generate_worker, daemon=True).start()

    def _generate_worker(self):
        try:
            engine = ImpositionEngine(self.img_panel.entries, self.cfg)

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


def main():
    enable_dpi_awareness()
    app = PrintImposerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
