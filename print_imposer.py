#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrintImposer v1.8.0
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
"""

import os
import sys
import copy
import math
import json
import tempfile
import threading
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, NamedTuple

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog

import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

import struct
from PIL import Image, ImageDraw, ImageTk
from PIL import features as _pil_features


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
# SUPORTE OPCIONAL A PDF (ENTRADA)
# ══════════════════════════════════════════════════════════════════════════════
# `pypdfium2` traz o PDFium embutido (sem cairo, sem compilar). Como no SVG,
# sondamos por render real (FIX-002) e GUARDAMOS o módulo: importar não basta,
# e perder a referência quebraria o render só na hora de gerar a folha.

PDF_BACKEND: Optional[str] = None
_PDF_MODS: Dict[str, Any] = {}


def _probe_pdf() -> Optional[str]:
    """Cria um PDF mínimo em memória e o RENDERIZA; só então o back-end conta."""
    try:
        import pypdfium2 as pdfium  # type: ignore
        doc = pdfium.PdfDocument.new()
        page = doc.new_page(16, 16)
        img = page.render(scale=1).to_pil()
        page.close()
        doc.close()
        if isinstance(img, Image.Image) and img.width > 0:
            _PDF_MODS["pdfium"] = pdfium
            return "pypdfium2"
    except Exception:
        pass
    return None


PDF_BACKEND = _probe_pdf()
PDF_OK: bool = PDF_BACKEND is not None


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
# SUPORTE OPCIONAL A AVIF / HEIC
# ══════════════════════════════════════════════════════════════════════════════
# AVIF: o Pillow 12 lê sozinho, mas só se foi compilado com o codec — sondamos
# a capacidade (FIX-002), não o import. HEIC/HEIF: precisa do `pillow-heif`;
# sem ele a extensão nem aparece no seletor e o app abre igual.

def _probe_avif() -> bool:
    try:
        return bool(_pil_features.check("avif"))
    except Exception:
        return False


def _probe_heif() -> bool:
    try:
        import pillow_heif  # type: ignore
        pillow_heif.register_heif_opener()
        return True
    except Exception:
        return False


def _probe_can_save(fmt: str) -> bool:
    """Grava uma imagem mínima em memória: `features.check` verdadeiro não
    garante a GRAVAÇÃO (FIX-002) — o codec pode estar só de leitura."""
    import io
    try:
        Image.new("RGB", (8, 8)).save(io.BytesIO(), fmt)
        return True
    except Exception:
        return False


AVIF_OK: bool = _probe_avif()
HEIF_OK: bool = _probe_heif()


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

VERSION  = "1.8.0"
APP_NAME = "PrintImposer"
MM_TO_INCH = 1.0 / 25.4

RASTER_EXT = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp', '.gif'}
if AVIF_OK:
    RASTER_EXT |= {'.avif'}
if HEIF_OK:
    RASTER_EXT |= {'.heic', '.heif'}
SVG_EXT    = {'.svg'} if SVG_BACKEND else set()
PDF_EXT    = {'.pdf'} if PDF_OK else set()
SUPPORTED_EXT = RASTER_EXT | SVG_EXT | PDF_EXT

# Acima disso o PDF pede confirmação antes de virar uma página por item.
PDF_CONFIRM_PAGES = 50

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

# Guia de corte: chave persistida → rótulo na UI (substitui o antigo `cut_lines`).
CUT_GUIDE_KEYS   = ["none", "lines", "marks"]
CUT_GUIDE_LABELS = ["Nenhuma", "Linhas atravessando", "Marcas de canto"]
# Sangria: chave persistida → rótulo na UI.
BLEED_MODE_KEYS   = ["mirror", "included"]
BLEED_MODE_LABELS = ["Estender a borda (espelhar)", "A arte já tem sangria"]
# Faixas aceitas (valor fora é ajustado ao limite) e padrões de mercado.
MARK_LEN_RANGE    = (1.0, 15.0)    # mm
MARK_OFFSET_RANGE = (0.0, 15.0)    # mm
MARK_WIDTH_RANGE  = (0.1, 2.0)     # pt
BLEED_RANGE       = (0.0, 10.0)    # mm
MARK_COLOR = (0, 0, 0)             # preto 100%
FIT_LABELS  = ["Ajustar (fit)", "Preencher (fill)", "Esticar (stretch)"]
FIT_KEYS     = ["fit",           "fill",              "stretch"]
def build_out_formats(can_save=_probe_can_save) -> List[str]:
    """Formatos de saída oferecidos: WEBP e AVIF só se o Pillow GRAVA de fato."""
    fmts = ["PNG", "PDF", "JPEG", "TIFF"]   # PNG primeiro: é o padrão agora
    for extra in ("WEBP", "AVIF"):
        if can_save(extra):
            fmts.append(extra)
    return fmts


OUT_FORMATS  = build_out_formats()
OUT_EXT      = {"PDF": "pdf", "PNG": "png", "JPEG": "jpg", "TIFF": "tif",
                "WEBP": "webp", "AVIF": "avif"}
# Formatos só para compartilhar: a UI avisa que gráfica não pede isso.
SHARE_FORMATS = ("WEBP", "AVIF")

# Compressão do PDF: chave persistida → rótulo na UI (DEC-014).
PDF_COMP_KEYS   = ["lossless", "jpeg"]
PDF_COMP_LABELS = ["Sem perda", "JPEG"]
JPEG_Q_MIN, JPEG_Q_MAX = 50, 100
PDF_HEADER = b"%PDF-1.4\n"

# Compressão do WebP: chave persistida → rótulo na UI.
WEBP_COMP_KEYS   = ["lossless", "lossy"]
WEBP_COMP_LABELS = ["Sem perda", "Com perda"]

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
    "guide":         "Guia rápido: da arte à impressão",
    "about":         "Sobre o PrintImposer",
}

# Guia rápido (Ajuda). O README continua sendo a versão longa deste texto.
QUICK_GUIDE = (
    "1. Na sua ferramenta (Figma, Canva, Affinity, Photoshop, Corel...)\n"
    "   Crie as artes no tamanho final (ex.: A6) e exporte em PDF —\n"
    "   melhor, se o cabeçalho mostrar «PDF: pypdfium2» — ou em PNG com\n"
    "   pelo menos 1240×1748 px para A6. Fotos do celular entram direto.\n"
    "\n"
    "2. No PrintImposer\n"
    "   Adicione a pasta com as artes, escolha a grade (ex.: 2×2), confira\n"
    "   o selo de qualidade no rodapé e clique em «Gerar Arquivos».\n"
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

_SVG_UNITS = {"": 1.0, "px": 1.0, "pt": 4.0 / 3.0, "pc": 16.0,
              "mm": 96.0 / 25.4, "cm": 96.0 / 2.54, "in": 96.0}
_svg_size_cache: Dict[Tuple[str, float], Tuple[float, float]] = {}


def _svg_length(raw: Optional[str]) -> Optional[float]:
    """Comprimento SVG (`210mm`, `100px`, `50`) em px de CSS; None se ausente ou relativo (%)."""
    import re
    if not raw:
        return None
    m = re.fullmatch(r"\s*([0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*([a-zA-Z]*)\s*", raw)
    if not m or m.group(2).lower() not in _SVG_UNITS:
        return None
    val = float(m.group(1)) * _SVG_UNITS[m.group(2).lower()]
    return val if val > 0 else None


def _svg_backend_size(path: str) -> Tuple[float, float]:
    """Tamanho intrínseco medido pelo back-end (renderiza pequeno) — último recurso."""
    import io
    if SVG_BACKEND == "cairosvg":
        png = _SVG_MODS["cairosvg"].svg2png(url=path, output_width=64)
        return Image.open(io.BytesIO(png)).size
    if SVG_BACKEND == "svglib":
        drawing = _SVG_MODS["svg2rlg"](path)
        if drawing is None:
            raise ValueError("SVG ilegível")
        return float(drawing.width), float(drawing.height)
    raise RuntimeError("Nenhum back-end de SVG disponível")


def svg_intrinsic_size(path: str) -> Tuple[float, float]:
    """Tamanho intrínseco (w, h) do SVG: width/height, senão viewBox, senão medida pelo back-end.

    Só a PROPORÇÃO importa para escolher a escala. Cache por (caminho, mtime):
    a guarda e o preview consultam o mesmo arquivo muitas vezes.
    """
    try:
        key = (path, os.path.getmtime(path))
    except OSError:
        key = (path, 0.0)
    hit = _svg_size_cache.get(key)
    if hit:
        return hit
    size: Optional[Tuple[float, float]] = None
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(path).getroot()
        w, h = _svg_length(root.get("width")), _svg_length(root.get("height"))
        if w and h:
            size = (w, h)
        else:
            vb = (root.get("viewBox") or "").replace(",", " ").split()
            if len(vb) == 4 and float(vb[2]) > 0 and float(vb[3]) > 0:
                size = (float(vb[2]), float(vb[3]))
    except Exception:
        size = None
    if size is None:
        size = _svg_backend_size(path)
    _svg_size_cache[key] = (float(size[0]), float(size[1]))
    return _svg_size_cache[key]


def _svg_backend_render(path: str, out_w: int, out_h: int) -> Image.Image:
    """Desenha o SVG exatamente em (out_w × out_h) com o back-end ativo."""
    import io

    if SVG_BACKEND == "cairosvg":
        png = _SVG_MODS["cairosvg"].svg2png(url=path, output_width=out_w,
                                            output_height=out_h)
        return Image.open(io.BytesIO(png)).convert("RGBA")

    if SVG_BACKEND == "svglib":
        svg2rlg  = _SVG_MODS["svg2rlg"]
        renderPM = _SVG_MODS["renderPM"]
        drawing = svg2rlg(path)
        if drawing is None:
            raise ValueError("SVG ilegível")
        # svglib desenha no tamanho intrínseco; escalamos o desenho antes do render.
        dw = float(drawing.width) or 1.0
        dh = float(drawing.height) or 1.0
        drawing.width  = out_w
        drawing.height = out_h
        drawing.scale(out_w / dw, out_h / dh)
        buf = io.BytesIO()
        renderPM.drawToFile(drawing, buf, fmt="PNG", bg=0xFFFFFF)
        buf.seek(0)
        return Image.open(buf).convert("RGBA")

    raise RuntimeError("Nenhum back-end de SVG disponível")


def rasterize_svg(path: str, box_w: int, box_h: int,
                  fit_mode: str = "fit") -> Image.Image:
    """Rasteriza um SVG para caber (ou cobrir) a caixa, sem ampliar depois.

    O ganho central: como o desenho é recalculado na resolução da célula, um SVG
    nunca sofre upscale — imprime nítido em qualquer DPI. Mesma regra do PDF:
    fit: escala que cabe; fill: escala que cobre (o `_place_image` recorta);
    stretch: cobre e reduz até (box_w, box_h).
    """
    iw, ih = svg_intrinsic_size(path)
    pick = max if fit_mode in ("fill", "stretch") else min
    scale = pick(box_w / iw, box_h / ih)
    out_w, out_h = max(1, round(iw * scale)), max(1, round(ih * scale))
    img = _svg_backend_render(path, out_w, out_h)
    if fit_mode == "stretch" and img.size != (box_w, box_h):
        img = img.resize((box_w, box_h), Image.LANCZOS)
    return img


def is_svg(path: str) -> bool:
    return Path(path).suffix.lower() == ".svg"


def is_pdf(path: str) -> bool:
    return Path(path).suffix.lower() == ".pdf"


def is_vector(path: str) -> bool:
    """SVG e PDF são desenhados no tamanho da célula: não têm tamanho nativo em px."""
    return is_svg(path) or is_pdf(path)


class SourceRef(NamedTuple):
    """Referência de fonte: arquivo + página (0 para tudo que não é PDF) + rotação manual."""
    path: str
    page: int = 0
    rotation: int = 0       # 0 = Auto-Rotate decide; 90/180/270 = exato, sentido horário


def as_ref(src: Any) -> SourceRef:
    """Aceita caminho puro (str) ou SourceRef — o motor trabalha sempre com SourceRef."""
    return src if isinstance(src, SourceRef) else SourceRef(str(src))


def pdf_page_count(path: str) -> int:
    """Número de páginas do PDF. Levanta se estiver ilegível ou com senha."""
    pdfium = _PDF_MODS["pdfium"]
    doc = pdfium.PdfDocument(path)
    try:
        return len(doc)
    finally:
        doc.close()


def pdf_page_size(path: str, page: int) -> Tuple[float, float]:
    """Tamanho da página em pontos (já considerando a rotação da página)."""
    pdfium = _PDF_MODS["pdfium"]
    doc = pdfium.PdfDocument(path)
    try:
        pg = doc[page]
        try:
            w, h = pg.get_size()
        finally:
            pg.close()
        return float(w), float(h)
    finally:
        doc.close()


def effective_rotation(src_w: float, src_h: float, cell_w: float, cell_h: float,
                       auto_rotate: bool, manual: int = 0) -> int:
    """Giro (graus, horário) que a fonte recebe na célula.

    Manual ≠ 0 é exato e o Auto-Rotate não age; manual 0 devolve 90 quando o
    Auto-Rotate está ligado e a orientação da fonte difere da célula. Única
    fonte da decisão: caixa de render, `_place_image` e guarda de qualidade
    passam por aqui (FIX-006: decidir em dois lugares amplia a arte em silêncio).
    """
    if manual:
        return manual
    if auto_rotate and src_w > 0 and src_h > 0 and (cell_w >= cell_h) != (src_w >= src_h):
        return 90
    return 0


def vector_render_box(w: float, h: float, cw: int, ch: int,
                      auto_rotate: bool, manual: int = 0) -> Tuple[int, int]:
    """Caixa onde uma fonte vetorial (PDF ou SVG) deve ser rasterizada, JÁ na orientação final.

    Se o motor girará a imagem 90° ou 270° (Auto-Rotate ou rotação manual),
    renderizar na caixa (cw, ch) e girar depois desenharia a arte pequena e a
    ampliaria. Por isso a caixa nasce girada: (ch, cw).
    """
    if effective_rotation(w, h, cw, ch, auto_rotate, manual) in (90, 270):
        return ch, cw
    return cw, ch


def pdf_render_box(w_pt: float, h_pt: float, cw: int, ch: int,
                   auto_rotate: bool, manual: int = 0) -> Tuple[int, int]:
    """Caixa de render da página PDF — ver `vector_render_box`."""
    return vector_render_box(w_pt, h_pt, cw, ch, auto_rotate, manual)


PDF_IMG_MIN_COVER = 0.10    # imagem que cobre menos que isso da página é logo/ícone
_pdf_img_cache: Dict[Tuple[str, float, int], List[Tuple[int, int, float, float]]] = {}


def pdf_inner_images(path: str, page: int) -> List[Tuple[int, int, float, float]]:
    """Imagens raster relevantes dentro da página: [(px_w, px_h, w_pt, h_pt)].

    w_pt/h_pt são a caixa da imagem na página; se a imagem está girada 90° no
    PDF os px são trocados para casar com a caixa. Imagens que cobrem menos de
    10% da página (logos, ícones) ficam de fora. Levanta se o PDF não abre —
    o chamador decide ignorar o item.
    """
    try:
        key = (path, os.path.getmtime(path), page)
    except OSError:
        key = (path, 0.0, page)
    hit = _pdf_img_cache.get(key)
    if hit is not None:
        return hit
    pdfium = _PDF_MODS["pdfium"]
    import pypdfium2.raw as pdfium_raw  # type: ignore
    out: List[Tuple[int, int, float, float]] = []
    doc = pdfium.PdfDocument(path)
    try:
        pg = doc[page]
        try:
            pw, ph = pg.get_size()
            for obj in pg.get_objects(filter=[pdfium_raw.FPDF_PAGEOBJ_IMAGE]):
                left, bottom, right, top = obj.get_bounds()
                bw, bh = abs(right - left), abs(top - bottom)
                if bw <= 0 or bh <= 0 or bw * bh < PDF_IMG_MIN_COVER * pw * ph:
                    continue
                meta = obj.get_metadata()
                px_w, px_h = int(meta.width), int(meta.height)
                m = obj.get_matrix()
                if abs(m.a) < abs(m.b):          # girada 90°: largura do bitmap vira altura
                    px_w, px_h = px_h, px_w
                if px_w > 0 and px_h > 0:
                    out.append((px_w, px_h, float(bw), float(bh)))
        finally:
            pg.close()
    finally:
        doc.close()
    _pdf_img_cache[key] = out
    return out


def pdf_inner_ratio(path: str, page: int, cw: int, ch: int,
                    auto_rotate: bool, fit_mode: str, manual: int = 0) -> Optional[float]:
    """Pior razão (px da imagem / px que ela ocupa na célula) entre as imagens da página.

    A escala da página na célula é a MESMA do `rasterize_pdf` (inclusive a caixa
    girada do Auto-Rotate). None = página sem imagem relevante (vetor puro).
    """
    imgs = pdf_inner_images(path, page)
    if not imgs:
        return None
    w_pt, h_pt = pdf_page_size(path, page)
    box_w, box_h = vector_render_box(w_pt, h_pt, cw, ch, auto_rotate, manual)
    if fit_mode == "stretch":
        sx, sy = box_w / w_pt, box_h / h_pt
    else:
        pick = max if fit_mode == "fill" else min
        sx = sy = pick(box_w / w_pt, box_h / h_pt)
    return min(min(px_w / (bw * sx), px_h / (bh * sy))
               for px_w, px_h, bw, bh in imgs)


def rasterize_pdf(path: str, page: int, box_w: int, box_h: int,
                  fit_mode: str = "fit") -> Image.Image:
    """Rasteriza uma página de PDF para caber (ou cobrir) a caixa, sem ampliar depois.

    fit: escala que cabe na caixa; fill: escala que a cobre (o `_place_image`
    recorta); stretch: cobre a caixa e reduz até (box_w, box_h) — reduzir nunca
    borra como ampliar. Fundo branco opaco: PDF sem fundo sairia preto/transparente.
    """
    pdfium = _PDF_MODS["pdfium"]
    doc = pdfium.PdfDocument(path)
    try:
        pg = doc[page]
        try:
            w_pt, h_pt = pg.get_size()
            if w_pt <= 0 or h_pt <= 0:
                raise ValueError("PDF com página de tamanho zero")
            pick = max if fit_mode in ("fill", "stretch") else min
            scale = pick(box_w / w_pt, box_h / h_pt)
            img = pg.render(scale=scale, fill_color=(255, 255, 255, 255)).to_pil()
        finally:
            pg.close()
    finally:
        doc.close()
    img = img.convert("RGBA")
    if fit_mode == "stretch" and img.size != (box_w, box_h):
        img = img.resize((box_w, box_h), Image.LANCZOS)
    return img


def open_source(path: str, box_w: int = 0, box_h: int = 0, page: int = 0,
                auto_rotate: bool = False, fit_mode: str = "fit",
                rotation: int = 0) -> Image.Image:
    """Abre uma imagem-fonte. SVG e PDF são rasterizados na caixa pedida; raster abre direto."""
    if is_pdf(path):
        if box_w <= 0 or box_h <= 0:
            box_w = box_h = 1000  # tamanho de cortesia para inspeção/miniatura
        else:
            w_pt, h_pt = pdf_page_size(path, page)
            box_w, box_h = vector_render_box(w_pt, h_pt, box_w, box_h, auto_rotate, rotation)
        return rasterize_pdf(path, page, box_w, box_h, fit_mode)
    if is_svg(path):
        if box_w <= 0 or box_h <= 0:
            box_w = box_h = 1000  # tamanho de cortesia para inspeção/miniatura
        else:
            iw, ih = svg_intrinsic_size(path)
            box_w, box_h = vector_render_box(iw, ih, box_w, box_h, auto_rotate, rotation)
        return rasterize_svg(path, box_w, box_h, fit_mode)
    return Image.open(path).convert("RGBA")


# ══════════════════════════════════════════════════════════════════════════════
# MODELO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

class ImageEntry:
    """Uma imagem da lista, com sua quantidade de cópias e miniatura."""

    # Cache de miniatura por (caminho, mtime): evita reprocessar ao reordenar
    # ou mexer na quantidade. Ver HISTORY §8 (otimização segura).
    _thumb_cache: Dict[Tuple[str, float, int], Image.Image] = {}

    def __init__(self, path: str, page_index: int = 0, page_count: int = 1):
        self.path     = path
        self.filename = Path(path).name
        self.page_index = page_index      # só PDF: qual página este item representa
        self.page_count = page_count
        self.quantity = 1
        self.rotation = 0                 # 0 = Auto-Rotate; 90/180/270 horário, exato
        self.src_size: Optional[Tuple[int, int]] = None   # px da fonte (None p/ SVG)
        self.pil_thumb: Optional[Image.Image] = None
        self._load_thumb()

    @property
    def page_label(self) -> str:
        """Sufixo « · p. 2/5» — só para PDF de mais de uma página."""
        if self.page_count > 1:
            return f" · p. {self.page_index + 1}/{self.page_count}"
        return ""

    @property
    def ref(self) -> SourceRef:
        return SourceRef(self.path, self.page_index, self.rotation)

    def _load_thumb(self):
        try:
            key = (self.path, os.path.getmtime(self.path), self.page_index)
        except OSError:
            key = (self.path, 0.0, self.page_index)

        cached = ImageEntry._thumb_cache.get(key)
        if cached is not None:
            self.pil_thumb = cached
            return

        try:
            if is_pdf(self.path):
                img = rasterize_pdf(self.path, self.page_index,
                                    THUMB_W * 3, THUMB_H * 3)
                self.src_size = None
            elif is_svg(self.path):
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
        if is_vector(self.path):
            return None
        try:
            with Image.open(self.path) as im:
                self.src_size = im.size
                return self.src_size
        except Exception:
            return None


def clamp_jpeg_quality(value: Any, default: int = 95) -> int:
    """Qualidade JPEG ajustada a 50–100; valor ilegível cai no `default`."""
    try:
        return max(JPEG_Q_MIN, min(JPEG_Q_MAX, int(value)))
    except (TypeError, ValueError):
        return default


def clamp_float(value: Any, lo: float, hi: float, default: float) -> float:
    """Número ajustado a [lo, hi]; valor ilegível (ou NaN) cai no `default`."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    if v != v:
        return default
    return max(lo, min(hi, v))


class LayoutConfig:
    """Estado completo de configuração. Serializa para JSON (presets e settings)."""

    # Campos que compõem um preset nomeado (tudo menos caminhos de pasta).
    PRESET_FIELDS = (
        "cols", "rows", "paper_key", "paper_w_mm", "paper_h_mm", "dpi",
        "margin_outer_mm", "margin_between_x_mm", "margin_between_y_mm",
        "bg_color", "fit_mode",
        "auto_rotate", "cut_guide", "cut_color", "cut_width_px", "cut_style",
        "cut_dash", "mark_length_mm", "mark_offset_mm", "mark_width_pt",
        "bleed_mm", "bleed_mode", "output_format", "output_prefix",
        "output_suffix", "pdf_compression", "jpeg_quality", "webp_compression",
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
        self.margin_between_x_mm: float = 0.0          # entre colunas
        self.margin_between_y_mm: float = 0.0          # entre linhas
        self.bg_color:         str   = "#FFFFFF"
        self.fit_mode:          str   = "fit"
        self.auto_rotate:       bool  = True
        self.cut_guide:         str   = "none"         # none | lines | marks
        self.cut_color:         str   = "#999999"
        self.cut_width_px:      int   = 1
        self.cut_style:         str   = "Sólida"
        self.cut_dash:          int   = 10
        self.mark_length_mm:    float = 4.0            # marcas de canto
        self.mark_offset_mm:    float = 3.0
        self.mark_width_pt:     float = 0.25
        self.bleed_mm:          float = 0.0            # 0 = sem sangria
        self.bleed_mode:        str   = "mirror"       # mirror | included
        self.output_format:     str   = "PNG"          # PNG é o padrão agora
        self.output_prefix:     str   = "folha_"
        self.output_suffix:     str   = ""
        self.pdf_compression:   str   = "lossless"     # DEC-014: sem perda é o padrão
        self.jpeg_quality:      int   = 95             # serve ao JPEG, PDF-JPEG, WebP com perda e AVIF
        self.webp_compression:  str   = "lossless"
        # Pastas independentes: abrir imagens não mexe em onde salvar.
        self.input_dir:         str   = str(Path.home())
        self.output_dir:        str   = default_output_dir()
        self.output_dir2:       str   = ""             # destino extra opcional
        self.output_dir2_on:    bool  = False

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def from_dict(self, d: dict):
        # Configuração/preset da 1.2 trazia um espaçamento só: vira X = Y,
        # a menos que o dado já traga os campos novos (eles mandam).
        if "margin_between_mm" in d:
            d = dict(d)   # não muta o dict do chamador (preset em memória)
            legacy = d.pop("margin_between_mm")
            d.setdefault("margin_between_x_mm", legacy)
            d.setdefault("margin_between_y_mm", legacy)
        # Config/preset da 1.5 trazia `cut_lines` (bool): vira `cut_guide`, a menos
        # que o dado já traga o campo novo (ele manda). Sem isto o corte ligado
        # sumiria em silêncio ao abrir um preset antigo.
        if "cut_lines" in d:
            d = dict(d)
            legacy_cut = d.pop("cut_lines")
            d.setdefault("cut_guide", "lines" if legacy_cut else "none")
        for k, v in d.items():
            if hasattr(self, k):
                setattr(self, k, v)
        if self.cut_guide not in CUT_GUIDE_KEYS:
            self.cut_guide = "none"
        if self.bleed_mode not in BLEED_MODE_KEYS:
            self.bleed_mode = "mirror"
        self.mark_length_mm = clamp_float(self.mark_length_mm, *MARK_LEN_RANGE, 4.0)
        self.mark_offset_mm = clamp_float(self.mark_offset_mm, *MARK_OFFSET_RANGE, 3.0)
        self.mark_width_pt  = clamp_float(self.mark_width_pt, *MARK_WIDTH_RANGE, 0.25)
        self.bleed_mm       = clamp_float(self.bleed_mm, *BLEED_RANGE, 0.0)
        self.jpeg_quality = clamp_jpeg_quality(self.jpeg_quality, self.jpeg_quality)
        if self.pdf_compression not in PDF_COMP_KEYS:
            self.pdf_compression = "lossless"
        if self.webp_compression not in WEBP_COMP_KEYS:
            self.webp_compression = "lossless"
        # Preset com AVIF aberto numa máquina que não grava AVIF: volta ao padrão.
        if self.output_format not in OUT_FORMATS:
            self.output_format = "PNG"

    def preset_dict(self) -> dict:
        """Só os campos de layout — um preset não carrega caminhos de pasta."""
        return {k: getattr(self, k) for k in self.PRESET_FIELDS}

    def nup(self) -> int:
        return max(1, self.cols) * max(1, self.rows)


# ══════════════════════════════════════════════════════════════════════════════
# GEOMETRIA DE CORTE E SANGRIA (em mm, pura — F4 etapa 4)
# ══════════════════════════════════════════════════════════════════════════════

Rect = Tuple[float, float, float, float]          # (x0, y0, x1, y1) em mm
Segment = Tuple[float, float, float, float]       # (x1, y1, x2, y2) em mm


class SheetGeometry(NamedTuple):
    """Tudo que o desenho precisa saber sobre corte e sangria, em mm.

    `cells` e `bleeds` seguem a ordem dos slots (linha a linha). `bleed_sides` é a
    sangria que COUBE em cada lado de cada célula: (esq, topo, dir, base).
    `warnings` é uma lista de (nível, texto): «warn» (âmbar) ou «info» (cinza).
    """
    cells: List[Rect]
    bleeds: List[Rect]
    bleed_sides: List[Tuple[float, float, float, float]]
    cut_x: List[float]
    cut_y: List[float]
    marks: List[Segment]
    mark_offset: float          # distância efetiva: nunca menor que a sangria
    grid: Rect                  # caixa que envolve todas as células
    warnings: List[Tuple[str, str]]


def _fmt_mm(v: float) -> str:
    """Milímetro para aviso: sem zeros à toa («7», «1.5»)."""
    return f"{round(v, 2):g}"


def _unique_sorted(values: List[float]) -> List[float]:
    """Posições de corte sem duplicata (células coladas dividem a mesma borda)."""
    out: List[float] = []
    for v in sorted(values):
        if not out or abs(v - out[-1]) > 1e-6:
            out.append(v)
    return out


def sheet_geometry(cfg: "LayoutConfig") -> SheetGeometry:
    """Calcula em mm: retângulos de corte e de sangria, posições de corte, marcas e avisos.

    Função pura (sem Tk, sem Pillow): o motor raster converte para px na hora de
    desenhar, e o desenhista vetorial da F5 reusa a MESMA geometria (DEC-015).
    A sangria nunca invade a célula vizinha (vai até metade do espaçamento) nem
    passa da margem externa; as marcas ficam fora da grade, a `mark_offset` dela.
    """
    cols, rows = max(1, int(cfg.cols)), max(1, int(cfg.rows))
    mo  = max(0.0, float(cfg.margin_outer_mm))
    mbx = max(0.0, float(cfg.margin_between_x_mm))
    mby = max(0.0, float(cfg.margin_between_y_mm))
    cw = max(0.0, (cfg.paper_w_mm - 2 * mo - (cols - 1) * mbx) / cols)
    ch = max(0.0, (cfg.paper_h_mm - 2 * mo - (rows - 1) * mby) / rows)

    bleed = clamp_float(cfg.bleed_mm, *BLEED_RANGE, 0.0)
    length = clamp_float(cfg.mark_length_mm, *MARK_LEN_RANGE, 4.0)
    offset = max(clamp_float(cfg.mark_offset_mm, *MARK_OFFSET_RANGE, 3.0), bleed)

    cells: List[Rect] = []
    bleeds: List[Rect] = []
    sides: List[Tuple[float, float, float, float]] = []
    for row in range(rows):
        for col in range(cols):
            x0 = mo + col * (cw + mbx)
            y0 = mo + row * (ch + mby)
            cells.append((x0, y0, x0 + cw, y0 + ch))
            l = min(bleed, mo if col == 0 else mbx / 2)
            r = min(bleed, mo if col == cols - 1 else mbx / 2)
            t = min(bleed, mo if row == 0 else mby / 2)
            b = min(bleed, mo if row == rows - 1 else mby / 2)
            sides.append((l, t, r, b))
            bleeds.append((x0 - l, y0 - t, x0 + cw + r, y0 + ch + b))

    gx0, gy0 = mo, mo
    gx1 = mo + cols * cw + (cols - 1) * mbx
    gy1 = mo + rows * ch + (rows - 1) * mby

    cut_x = _unique_sorted([c[0] for c in cells] + [c[2] for c in cells])
    cut_y = _unique_sorted([c[1] for c in cells] + [c[3] for c in cells])

    marks: List[Segment] = []
    if cfg.cut_guide == "marks":
        for x in cut_x:        # traços verticais, acima e abaixo da grade
            marks.append((x, gy0 - offset - length, x, gy0 - offset))
            marks.append((x, gy1 + offset, x, gy1 + offset + length))
        for y in cut_y:        # traços horizontais, à esquerda e à direita
            marks.append((gx0 - offset - length, y, gx0 - offset, y))
            marks.append((gx1 + offset, y, gx1 + offset + length, y))

    warnings: List[Tuple[str, str]] = []
    if cfg.cut_guide == "marks" and mo + 1e-9 < offset + length:
        warnings.append(("warn", "A margem externa precisa de pelo menos "
                                 f"{_fmt_mm(offset + length)} mm para as marcas."))
    if bleed > 0:
        for count, gap, nome in ((cols, mbx, "colunas"), (rows, mby, "linhas")):
            if count > 1 and gap + 1e-9 < 2 * bleed:
                warnings.append(("warn",
                                 f"Espaçamento entre {nome} menor que 2× a sangria: "
                                 f"entre as {nome} coube {_fmt_mm(gap / 2)} mm."))
        # Margem 0 não avisa: a célula encosta no papel e não há corte externo a proteger.
        if mo > 1e-9 and mo + 1e-9 < bleed:
            warnings.append(("warn",
                             f"A margem externa ({_fmt_mm(mo)} mm) é menor que a sangria "
                             f"({_fmt_mm(bleed)} mm): na borda da folha, a sangria vai "
                             f"só até {_fmt_mm(mo)} mm."))
        if cfg.cut_guide == "lines":
            warnings.append(("info", "Com sangria, use marcas de canto: "
                                     "as linhas riscam a sangria."))

    return SheetGeometry(cells, bleeds, sides, cut_x, cut_y, marks, offset,
                         (gx0, gy0, gx1, gy1), warnings)


def cut_confirm_text(cfg: "LayoutConfig") -> Optional[str]:
    """Texto da confirmação antes de gerar quando há aviso âmbar de corte; None se não há.

    Só os avisos âmbar pedem confirmação (marcas que não cabem, sangria que não
    cabe); o aviso cinza das linhas com sangria apenas informa.
    """
    amber = [t for lvl, t in sheet_geometry(cfg).warnings if lvl == "warn"]
    if not amber:
        return None
    return "\n".join(amber) + "\n\nGerar mesmo assim?"


def snapshot_for_generation(entries: List["ImageEntry"],
                            cfg: LayoutConfig) -> Tuple[List["ImageEntry"], LayoutConfig]:
    """Cópias independentes da lista e da configuração para uma geração.

    Geração roda em thread por minutos; o dono pode mexer em papel, grade ou
    lista nesse meio-tempo. Com o motor lendo o `cfg` vivo, as folhas saíam
    com tamanhos misturados. O preview continua no `cfg` vivo. A cópia da
    entrada é rasa de propósito: path, página e quantidade são valores, e a
    miniatura (imutável na prática) não precisa ser duplicada.
    """
    frozen = LayoutConfig()
    frozen.from_dict(cfg.to_dict())
    return [copy.copy(e) for e in entries], frozen


# ══════════════════════════════════════════════════════════════════════════════
# AVISO DO SEGUNDO DESTINO
# ══════════════════════════════════════════════════════════════════════════════

DEST_NOTICE_MAX = 60          # caracteres do caminho antes de encurtar no meio
WARN_COLOR      = "#d6a13a"   # âmbar — o mesmo do selo de atenção


def shorten_middle(text: str, limit: int = DEST_NOTICE_MAX) -> str:
    """Encurta no meio com «…» (o fim do caminho é o que identifica a pasta)."""
    if len(text) <= limit:
        return text
    keep = limit - 1
    head = keep // 2
    return text[:head] + "…" + text[len(text) - (keep - head):]


def _path_inside(path: str, parent: str) -> bool:
    """True se `path` é `parent` ou está debaixo dele (sem diferenciar caixa no Windows)."""
    try:
        p = os.path.normcase(str(Path(path).resolve()))
        q = os.path.normcase(str(Path(parent).resolve())).rstrip("\\/")
    except Exception:
        return False
    return p == q or p.startswith(q + os.sep)


def second_dest_notice(cfg: LayoutConfig) -> Tuple[bool, str, str]:
    """(mostrar, texto, nível) do aviso «Também grava em: …» da barra inferior.

    Nível «warn» (âmbar): pasta inexistente ou dentro da pasta temporária — o
    segundo destino já ficou ligado dias numa pasta de teste sem ninguém ver.
    """
    path = (cfg.output_dir2 or "").strip()
    if not (cfg.output_dir2_on and path):
        return False, "", "normal"
    text = f"Também grava em: {shorten_middle(path)}"
    warn = (not Path(path).is_dir()) or _path_inside(path, tempfile.gettempdir())
    return True, text, "warn" if warn else "normal"


# ══════════════════════════════════════════════════════════════════════════════
# ESCRITOR DE PDF (DEC-014)
# ══════════════════════════════════════════════════════════════════════════════

def png_idat(png: bytes) -> Tuple[int, int, bytes]:
    """Extrai (largura, altura, dados IDAT concatenados) de um PNG RGB 8 bits.

    Só serve PNG sem entrelaçamento: o `/Predictor 15` do PDF espera linhas
    sequenciais, e um PNG entrelaçado abriria embaralhado, sem erro nenhum.
    """
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("não é um PNG")
    pos, idat, hdr = 8, [], None
    while pos + 8 <= len(png):
        length, ctype = struct.unpack(">I4s", png[pos:pos + 8])
        data = png[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", data)
        elif ctype == b"IDAT":
            idat.append(data)
        elif ctype == b"IEND":
            break
        pos += 12 + length          # tamanho + tipo + dados + CRC
    if hdr is None or not idat:
        raise ValueError("PNG sem IHDR/IDAT")
    w, h, depth, ctype_, _comp, _filt, interlace = hdr
    if (depth, ctype_, interlace) != (8, 2, 0):
        raise ValueError("PNG precisa ser RGB, 8 bits, sem entrelaçamento")
    return w, h, b"".join(idat)


def _pdf_num(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".")


def write_pdf(pages: List[Image.Image], path: str, dpi: int,
              mode: str = "lossless", quality: int = 95) -> None:
    """Grava as folhas num PDF sem depender de biblioteca de PDF.

    `lossless` embute o fluxo Deflate do PNG da folha (`/FlateDecode`,
    `/Predictor 15`) sem recomprimir — sem perda por construção. `jpeg` embute
    os bytes do JPEG na qualidade pedida (`/DCTDecode`). O Pillow não serve:
    grava RGB em PDF sempre como JPEG, sem opção de qualidade.
    """
    import io
    quality = clamp_jpeg_quality(quality)
    objs: List[bytes] = []            # objs[i] é o objeto de número i+1

    def add(body: bytes) -> int:
        objs.append(body)
        return len(objs)

    n_pages = len(pages)
    # 1 = catálogo, 2 = árvore de páginas; cada folha usa 3 objetos seguidos.
    add(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + 3 * i} 0 R" for i in range(n_pages))
    add(f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode())

    for i, page in enumerate(pages):
        page = page.convert("RGB")
        buf = io.BytesIO()
        if mode == "jpeg":
            page.save(buf, "JPEG", quality=quality)
            w, h = page.size
            data = buf.getvalue()
            extra = "/Filter /DCTDecode"
        else:
            page.save(buf, "PNG")
            w, h, data = png_idat(buf.getvalue())
            extra = (f"/Filter /FlateDecode /DecodeParms << /Predictor 15 "
                     f"/Colors 3 /BitsPerComponent 8 /Columns {w} >>")

        w_pt, h_pt = w * 72.0 / dpi, h * 72.0 / dpi
        content = (f"q {_pdf_num(w_pt)} 0 0 {_pdf_num(h_pt)} 0 0 cm /Im0 Do Q"
                   ).encode()
        pg, ct, im = 3 + 3 * i, 4 + 3 * i, 5 + 3 * i
        add(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {_pdf_num(w_pt)} "
            f"{_pdf_num(h_pt)}] /Resources << /XObject << /Im0 {im} 0 R >> >> "
            f"/Contents {ct} 0 R >>".encode())
        add(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        add((f"<< /Type /XObject /Subtype /Image /Width {w} /Height {h} "
             f"/ColorSpace /DeviceRGB /BitsPerComponent 8 {extra} "
             f"/Length {len(data)} >>\nstream\n").encode()
            + data + b"\nendstream")

    out = bytearray(PDF_HEADER)
    offsets = []
    for num, body in enumerate(objs, start=1):
        offsets.append(len(out))                  # offset em BYTES
        out += f"{num} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode()
    out += b"0000000000 65535 f \n"               # cada entrada tem 20 bytes
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n").encode()

    with open(path, "wb") as fh:
        fh.write(out)


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
        mbx = self._mm_px(self.cfg.margin_between_x_mm, dpi)
        mby = self._mm_px(self.cfg.margin_between_y_mm, dpi)
        cw = max(1, (pw - 2*mo - (cols-1)*mbx) // cols)
        ch = max(1, (ph - 2*mo - (rows-1)*mby) // rows)
        return cw, ch

    def cell_mm(self) -> Tuple[float, float]:
        cols, rows = self._grid()
        cw = (self.cfg.paper_w_mm - 2*self.cfg.margin_outer_mm
              - (cols-1)*self.cfg.margin_between_x_mm) / cols
        ch = (self.cfg.paper_h_mm - 2*self.cfg.margin_outer_mm
              - (rows-1)*self.cfg.margin_between_y_mm) / rows
        return max(0.0, cw), max(0.0, ch)

    def bleed_px(self, dpi: Optional[int] = None) -> int:
        """Sangria configurada em px (0 = desligada), sem recorte pelo espaço livre."""
        return self._mm_px(clamp_float(self.cfg.bleed_mm, *BLEED_RANGE, 0.0), dpi)

    def bleed_px_included(self, dpi: Optional[int] = None) -> int:
        """Sangria que aumenta a caixa de encaixe: só no modo «A arte já tem sangria»."""
        return self.bleed_px(dpi) if self.cfg.bleed_mode == "included" else 0

    def sheet_info(self, dpi: Optional[int] = None) -> Tuple[int, int, float]:
        """(largura px, altura px, MB bruto) da folha. Bruto = RGB sem compressão:
        o tamanho comprimido depende do conteúdo, então não é estimado."""
        pw, ph = self._page_px(dpi)
        return pw, ph, pw * ph * 3 / (1024 * 1024)

    # ── Contagem ─────────────────────────────────────────────────────────────

    def _expand(self) -> List[SourceRef]:
        out: List[SourceRef] = []
        for e in self.entries:
            out.extend([e.ref] * max(1, e.quantity))
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
        PDF: o vetor também não, mas as imagens EMBUTIDAS na página ampliam — entram
        pela pior razão delas (sem `pypdfium2` ou com PDF ilegível o item sai da guarda).
        """
        cw, ch = self.cell_px()
        # «A arte já tem sangria»: a fonte cobre a célula AUMENTADA pela sangria.
        bp = self.bleed_px_included()
        cw, ch = cw + 2 * bp, ch + 2 * bp
        worst_ratio = None
        worst_name  = ""

        for e in self.entries:
            if is_pdf(e.path):
                if not PDF_OK:
                    continue
                try:
                    r = pdf_inner_ratio(e.path, e.page_index, cw, ch,
                                        self.cfg.auto_rotate, self.cfg.fit_mode,
                                        e.rotation)
                except Exception:
                    continue                  # PDF ilegível nunca derruba a guarda
                if r is not None and (worst_ratio is None or r < worst_ratio):
                    worst_ratio = r
                    worst_name = f"{e.filename} · p. {e.page_index + 1} (imagem interna)"
                continue
            if is_vector(e.path):
                continue
            size = e.real_size()
            if not size:
                continue
            # Rotação manual é exata: só a orientação girada entra. Em 0°, o
            # Auto-Rotate pode girar a imagem; considera a orientação mais favorável.
            straight = min(size[0] / cw, size[1] / ch)
            turned   = min(size[1] / cw, size[0] / ch)
            if e.rotation:
                r = turned if e.rotation in (90, 270) else straight
            else:
                r = max(straight, turned) if self.cfg.auto_rotate else straight
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
                     bg: Tuple[int, int, int], rotation: int = 0) -> Image.Image:
        cfg = self.cfg
        iw, ih = img.size

        turn = effective_rotation(iw, ih, cw, ch, cfg.auto_rotate, rotation)
        if turn:
            # Pillow gira ANTI-horário: o manual (horário) entra negativo. O
            # giro do Auto-Rotate (manual 0) segue `rotate(90)` — a saída de
            # quem não usa o botão não muda nem 1 px.
            img = img.rotate(90 if not rotation else -turn, expand=True)
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
                   cw: int, ch: int, mo: int, mbx: int, mby: int):
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
            x = mo + c * cw + (c - 1) * mbx + (mbx // 2 if mbx > 0 else 0)
            fn(x, 0, x, ph)
        for r in range(1, rows):
            y = mo + r * ch + (r - 1) * mby + (mby // 2 if mby > 0 else 0)
            fn(0, y, pw, y)

    @staticmethod
    def _mirror_extend(cell: Image.Image, l: int, t: int, r: int, b: int) -> Image.Image:
        """Acrescenta em volta da célula faixas com a borda espelhada (sangria «espelhar»).

        Primeiro estende na horizontal e depois na vertical sobre o resultado: os
        cantos saem espelhados nos dois eixos. Faixa maior que a célula é limitada a ela.
        """
        cw, ch = cell.size
        l, r = min(l, cw), min(r, cw)
        t, b = min(t, ch), min(b, ch)
        if not (l or t or r or b):
            return cell
        flip_h, flip_v = Image.FLIP_LEFT_RIGHT, Image.FLIP_TOP_BOTTOM
        ww = l + cw + r
        wide = Image.new("RGB", (ww, ch))
        wide.paste(cell, (l, 0))
        if l:
            wide.paste(cell.crop((0, 0, l, ch)).transpose(flip_h), (0, 0))
        if r:
            wide.paste(cell.crop((cw - r, 0, cw, ch)).transpose(flip_h), (l + cw, 0))
        out = Image.new("RGB", (ww, t + ch + b))
        out.paste(wide, (0, t))
        if t:
            out.paste(wide.crop((0, 0, ww, t)).transpose(flip_v), (0, 0))
        if b:
            out.paste(wide.crop((0, ch - b, ww, ch)).transpose(flip_v), (0, t + ch))
        return out

    def _draw_marks(self, page: Image.Image, geo: SheetGeometry, dpi: int,
                    grid_px: Tuple[int, int, int, int]):
        """Desenha as marcas de canto (preto, espessura em pt) a partir da geometria em mm.

        O arredondamento para px é feito AQUI, por marca — nunca somando px de
        célula em célula. O fim interno de cada traço é recuado para fora da sangria
        em px, medida a partir da grade REAL em px (`grid_px`): o arredondamento de
        mm podia encostar 1 px na sangria.
        """
        s = dpi * MM_TO_INCH

        def px(v: float) -> int:
            return int(math.floor(v * s + 0.5))

        w = max(1, int(round(self.cfg.mark_width_pt * dpi / 72)))
        bp = self.bleed_px(dpi)
        gx0, gy0, gx1, gy1 = grid_px
        draw = ImageDraw.Draw(page)
        for x1, y1, x2, y2 in geo.marks:
            if x1 == x2:                                   # vertical
                xl = px(x1) - w // 2
                ya, yb = sorted((px(y1), px(y2)))
                if y2 <= geo.grid[1]:                      # acima da grade
                    yb = min(yb, gy0 - bp)
                else:                                      # abaixo
                    ya = max(ya, gy1 + bp)
                if yb > ya:
                    draw.rectangle([xl, ya, xl + w - 1, yb - 1], fill=MARK_COLOR)
            else:                                          # horizontal
                yt = px(y1) - w // 2
                xa, xb = sorted((px(x1), px(x2)))
                if x2 <= geo.grid[0]:                      # à esquerda
                    xb = min(xb, gx0 - bp)
                else:                                      # à direita
                    xa = max(xa, gx1 + bp)
                if xb > xa:
                    draw.rectangle([xa, yt, xb - 1, yt + w - 1], fill=MARK_COLOR)

    def compose_page(self, page_idx: int, image_paths: List[Any],
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
        mbx    = self._mm_px(cfg.margin_between_x_mm, override_dpi)
        mby    = self._mm_px(cfg.margin_between_y_mm, override_dpi)
        cw, ch = self.cell_px(override_dpi)
        dpi    = override_dpi or cfg.dpi

        bg   = self._hex_rgb(cfg.bg_color)
        page = Image.new("RGB", (pw, ph), bg)

        # Posição das células vem da geometria em mm, arredondada UMA vez por célula
        # (somar px arredondados célula a célula acumula erro). O tamanho continua o
        # de `cell_px`, que é o que a guarda de qualidade e os rasterizadores usam.
        geo = sheet_geometry(cfg)
        s   = dpi * MM_TO_INCH

        def px(v: float) -> int:
            return int(math.floor(v * s + 0.5))

        org_x = [px(c[0]) for c in geo.cells]
        org_y = [px(c[1]) for c in geo.cells]
        bp_full = self.bleed_px(dpi)

        start = page_idx * nup
        for slot in range(nup):
            idx = start + slot
            if idx >= len(image_paths):
                break

            col = slot % cols
            row = slot // cols
            x   = org_x[slot]
            y   = org_y[slot]

            # Sangria que coube em cada lado, em px: a da geometria, limitada ao vão
            # REAL em px (metade dele entre células; a margem na borda da folha).
            l = t = r = b = 0
            if bp_full > 0:
                sl, st, sr, sb = (px(v) for v in geo.bleed_sides[slot])
                l = min(sl, x if col == 0 else (x - (org_x[slot - 1] + cw)) // 2)
                r = min(sr, pw - (x + cw) if col == cols - 1
                        else (org_x[slot + 1] - (x + cw)) // 2)
                t = min(st, y if row == 0 else (y - (org_y[slot - cols] + ch)) // 2)
                b = min(sb, ph - (y + ch) if row == rows - 1
                        else (org_y[slot + cols] - (y + ch)) // 2)
                l, t, r, b = max(0, l), max(0, t), max(0, r), max(0, b)

            try:
                # SVG/PDF rasterizam direto no tamanho da célula: zero upscale.
                src  = as_ref(image_paths[idx])
                if bp_full > 0 and cfg.bleed_mode == "included":
                    # A arte traz a sangria: encaixa na célula AUMENTADA e recorta o
                    # que cabe — a parte de dentro cai exatamente no corte.
                    bw, bh = cw + 2 * bp_full, ch + 2 * bp_full
                    img  = open_source(src.path, bw, bh, page=src.page,
                                       auto_rotate=cfg.auto_rotate,
                                       fit_mode=cfg.fit_mode,
                                       rotation=src.rotation)
                    big  = self._place_image(img, bw, bh, bg, src.rotation)
                    cell = big.crop((bp_full - l, bp_full - t,
                                     bp_full + cw + r, bp_full + ch + b))
                else:
                    img  = open_source(src.path, cw, ch, page=src.page,
                                       auto_rotate=cfg.auto_rotate,
                                       fit_mode=cfg.fit_mode,
                                       rotation=src.rotation)
                    cell = self._mirror_extend(self._place_image(img, cw, ch, bg,
                                                                 src.rotation),
                                               l, t, r, b)
            except Exception:
                l = t = 0
                cell = Image.new("RGB", (cw, ch), (200, 190, 190))
                ImageDraw.Draw(cell).text(
                    (4, max(0, ch // 2 - 8)), "Erro ao carregar", fill=(160, 30, 30))

            page.paste(cell, (x - l, y - t))

        if cfg.cut_guide == "lines":
            self._draw_cuts(page, cols, rows, cw, ch, mo, mbx, mby)
        elif cfg.cut_guide == "marks":
            self._draw_marks(page, geo, dpi,
                             (min(org_x), min(org_y),
                              max(org_x) + cw, max(org_y) + ch))

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
        ext   = OUT_EXT[fmt]
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
                write_pdf(pages, fpath, cfg.dpi, cfg.pdf_compression,
                          cfg.jpeg_quality)
                saved.append(fpath)
                step += 1
                if progress_cb:
                    progress_cb(step, total_steps)
            else:
                for i, page in enumerate(pages):
                    fpath = unique_path(
                        f"{cfg.output_prefix}{i+1:03d}{cfg.output_suffix}.{ext}")
                    if fmt == "JPEG":
                        page.convert("RGB").save(fpath, "JPEG", quality=clamp_jpeg_quality(cfg.jpeg_quality),
                                                 dpi=(cfg.dpi, cfg.dpi))
                    elif fmt == "TIFF":
                        page.save(fpath, "TIFF", dpi=(cfg.dpi, cfg.dpi),
                                  compression="lzw")
                    elif fmt == "WEBP":
                        rgb = page.convert("RGB")
                        if cfg.webp_compression == "lossy":
                            rgb.save(fpath, "WEBP",
                                     quality=clamp_jpeg_quality(cfg.jpeg_quality))
                        else:
                            rgb.save(fpath, "WEBP", lossless=True)
                    elif fmt == "AVIF":
                        page.convert("RGB").save(
                            fpath, "AVIF", quality=clamp_jpeg_quality(cfg.jpeg_quality))
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
# INGESTÃO DE ARQUIVOS
# ══════════════════════════════════════════════════════════════════════════════

def plan_ingest(paths, confirm_many=None) -> Tuple[List[Tuple[str, int, int]],
                                                   List[Tuple[str, str]]]:
    """Decide o que entra na lista a partir dos caminhos escolhidos.

    Devolve ([(caminho, página, total)], [(arquivo pulado, motivo)]). Cada página
    de PDF vira um item. `confirm_many(nome, n)` é chamado quando o PDF passa de
    PDF_CONFIRM_PAGES páginas (False = não adiciona). PDF com senha, corrompido
    ou sem páginas vai para os pulados e não derruba o lote. Sem I/O de tela.
    """
    items: List[Tuple[str, int, int]] = []
    skipped: List[Tuple[str, str]] = []
    for f in paths:
        ext = Path(f).suffix.lower()
        if ext not in SUPPORTED_EXT:
            continue
        if ext != ".pdf":
            items.append((str(f), 0, 1))
            continue
        name = Path(f).name
        try:
            n = pdf_page_count(str(f))
        except Exception as exc:
            msg = str(exc).lower()
            skipped.append((name, "protegido por senha" if "password" in msg
                                  else "ilegível ou corrompido"))
            continue
        if n < 1:
            skipped.append((name, "sem páginas"))
            continue
        if n > PDF_CONFIRM_PAGES and confirm_many and not confirm_many(name, n):
            skipped.append((name, "não confirmado"))
            continue
        items.extend((str(f), i, n) for i in range(n))
    return items, skipped


def expand_dropped(paths) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Transforma o que foi solto na janela em (arquivos, [(pulado, motivo)]).

    Pasta entra como no «+ Pasta»: só o primeiro nível, sem subpastas, e no lugar
    dela. Tudo é ordenado pelo nome, sem diferenciar maiúscula. Formato não
    suportado vai para os pulados (não some em silêncio); caminho inexistente é
    ignorado. Sem Tk: o `event.data` já chega aqui como lista.
    """
    def by_name(p) -> str:
        return os.path.basename(str(p)).lower()

    files: List[str] = []
    skipped: List[Tuple[str, str]] = []

    def take(p: Path):
        if p.suffix.lower() in SUPPORTED_EXT:
            files.append(str(p))
        else:
            skipped.append((p.name, "formato não suportado"))

    for raw in sorted((str(x) for x in paths), key=by_name):
        p = Path(raw)
        try:
            if p.is_dir():
                for child in sorted((c for c in p.iterdir() if c.is_file()),
                                    key=by_name):
                    take(child)
            elif p.is_file():
                take(p)
        except OSError:
            continue    # pasta sem permissão ou que sumiu no meio do caminho
    return files, skipped


def move_item(items: list, src: int, dst: int) -> list:
    """Leva o item de `src` para a posição `dst` (no lugar) e devolve a lista.

    Índice fora da faixa, ou origem igual ao destino, não muda nada.
    """
    n = len(items)
    if 0 <= src < n and 0 <= dst < n and src != dst:
        items.insert(dst, items.pop(src))
    return items


def fill_last_sheet(quantities: List[int], nup: int) -> List[int]:
    """Soma as cópias que faltam para fechar a última folha, uma por item a partir do primeiro.

    Dá quantas voltas na lista forem precisas; folha já cheia ou lista vazia
    devolvem as quantidades como vieram.
    """
    out = list(quantities)
    if not out or nup <= 0:
        return out
    missing = (-sum(out)) % nup
    for i in range(missing):
        out[i % len(out)] += 1
    return out


def fill_n_sheets(n_items: int, nup: int, n_sheets: int) -> Optional[List[int]]:
    """Quantidades iguais para encher exatamente `n_sheets` folhas; None se não couber.

    Quando a divisão não é exata, os primeiros itens recebem uma cópia a mais.
    """
    if n_items <= 0 or nup <= 0 or n_sheets <= 0:
        return None
    total = n_sheets * nup
    if n_items > total:
        return None
    base, extra = divmod(total, n_items)
    return [base + 1] * extra + [base] * (n_items - extra)


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
        self.grid_preview.draw(c.cols, c.rows)
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

        cw_mm, ch_mm = engine.cell_mm()
        cw_px, ch_px = engine.cell_px()
        self._cell_var.set(
            f"Célula: {cw_mm:.1f} × {ch_mm:.1f} mm  ({cw_px} × {ch_px} px @ {self.cfg.dpi} DPI)")

        sw, sh, mb_raw = engine.sheet_info()
        self._sheet_var.set(
            f"Folha: {sw} × {sh} px · {mb_raw:.1f} MB bruto".replace(".", ","))

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
