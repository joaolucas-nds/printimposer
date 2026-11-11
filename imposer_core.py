#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
imposer_core — o motor do PrintImposer, sem interface.

Cálculo, geometria de corte e sangria, escritor de PDF, motor de imposição,
persistência, gerador de .bat e ingestão de arquivos. Nada aqui importa
`tkinter`, `customtkinter` nem `tkinterdnd2`: a GUI (`print_imposer.py`)
importa este módulo, e nunca o contrário (DEC-017).
"""

import os
import sys
import copy
import math
import json
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, NamedTuple

import struct
from PIL import Image, ImageDraw
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

VERSION  = "1.9.1"
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
# Layout da folha (DEC-018): `grid` é a grade colunas × linhas de sempre; as demais
# chaves são molduras do catálogo (células de tamanhos diferentes na mesma folha).
LAYOUT_KEYS   = ["grid", "1+2", "2+1", "1+3", "destaque4", "1+2+1"]
LAYOUT_LABELS = ["Grade", "1 + 2", "2 + 1", "1 + 3", "Destaque + 4", "1 + 2 + 1"]
# O que a «Proporção (%)» mede em cada moldura (a grade não tem proporção).
LAYOUT_HINTS = {
    "1+2": "largura da foto da esquerda",
    "2+1": "altura da faixa de cima",
    "1+3": "altura da foto de cima",
    "destaque4": "altura do destaque",
    "1+2+1": "altura da faixa do meio",
}
LAYOUT_RATIO_RANGE   = (20, 80)    # %
LAYOUT_RATIO_DEFAULT = 50
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
        "cols", "rows", "layout", "layout_ratio_pct", "paper_key", "paper_w_mm", "paper_h_mm", "dpi",
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
        self.layout:            str   = "grid"         # grid | chave de moldura (DEC-018)
        self.layout_ratio_pct:  int   = LAYOUT_RATIO_DEFAULT
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
        if self.layout not in LAYOUT_KEYS:
            self.layout = "grid"
        self.layout_ratio_pct = int(round(clamp_float(
            self.layout_ratio_pct, *LAYOUT_RATIO_RANGE, LAYOUT_RATIO_DEFAULT)))
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
        """Células por folha: os slots da moldura, ou colunas × linhas na grade."""
        if self.layout != "grid":
            return frame_slot_count(self.layout)
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
    # Linhas de corte da moldura (no meio de cada espaçamento, atravessando só o
    # pedaço que a divisão corta). Vazio na grade, que usa `cut_x`/`cut_y`.
    cuts: Tuple[Segment, ...] = ()


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
    if cfg.layout != "grid":
        return frame_geometry(cfg)
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

# ── Molduras (DEC-018) ───────────────────────────────────────────────────────
# Cada moldura é uma árvore de divisões sucessivas: `None` é um slot e
# `("v" | "h", [(peso, filho), ...])` reparte o retângulo em partes lado a lado
# («v», corta na vertical) ou empilhadas («h»). Só guilhotina: dá para cortar.

FrameNode = Any
_EPS = 1e-6


def frame_tree(key: str, ratio_pct: float) -> FrameNode:
    """Árvore de divisões da moldura `key`; `ratio_pct` é a proporção do LAYOUT_HINTS."""
    r = clamp_float(ratio_pct, *LAYOUT_RATIO_RANGE, LAYOUT_RATIO_DEFAULT) / 100.0
    two_side = ("v", [(1, None), (1, None)])
    if key == "1+2":
        return ("v", [(r, None), (1 - r, ("h", [(1, None), (1, None)]))])
    if key == "2+1":
        return ("h", [(r, two_side), (1 - r, None)])
    if key == "1+3":
        return ("h", [(r, None), (1 - r, ("v", [(1, None), (1, None), (1, None)]))])
    if key == "destaque4":
        return ("h", [(r, None), (1 - r, ("h", [(1, two_side), (1, two_side)]))])
    if key == "1+2+1":
        return ("h", [((1 - r) / 2, None), (r, two_side), ((1 - r) / 2, None)])
    raise KeyError(f"moldura desconhecida: {key!r}")


def _tree_slots(node: FrameNode) -> int:
    if node is None:
        return 1
    return sum(_tree_slots(child) for _w, child in node[1])


def frame_slot_count(key: str) -> int:
    """Quantos slots a moldura tem (a proporção não muda a contagem)."""
    return _tree_slots(frame_tree(key, LAYOUT_RATIO_DEFAULT))


def _frame_walk(node: FrameNode, rect: Rect, ext: Rect, gx: float, gy: float,
                cells: List[Rect], edges: List[Segment], centers: List[Segment]):
    """Percorre a árvore: slots em ordem de leitura, bordas de corte e linhas.

    `ext` é o `rect` ampliado até o meio do espaçamento vizinho (ou até a borda do
    papel, nos lados que tocam a área útil): as linhas de corte correm por ele.
    """
    if node is None:
        cells.append(rect)
        return
    axis, parts = node
    x0, y0, x1, y1 = rect
    ex0, ey0, ex1, ey1 = ext
    n = len(parts)
    gap = gx if axis == "v" else gy
    lo, hi = (x0, x1) if axis == "v" else (y0, y1)
    total = max(0.0, (hi - lo) - (n - 1) * gap)
    wsum = sum(w for w, _c in parts)
    spans: List[Tuple[float, float]] = []
    pos = lo
    for i, (w, _c) in enumerate(parts):
        end = hi if i == n - 1 else pos + total * w / wsum
        end = max(end, pos)
        spans.append((pos, end))
        pos = end + gap
    for i, (_w, child) in enumerate(parts):
        a, b = spans[i]
        if axis == "v":
            sub_rect = (a, y0, b, y1)
            sub_ext = (ex0 if i == 0 else a - gap / 2, ey0,
                       ex1 if i == n - 1 else b + gap / 2, ey1)
        else:
            sub_rect = (x0, a, x1, b)
            sub_ext = (ex0, ey0 if i == 0 else a - gap / 2,
                       ex1, ey1 if i == n - 1 else b + gap / 2)
        if i < n - 1:
            e1, e2 = b, spans[i + 1][0]          # as duas bordas do corte
            mid = (e1 + e2) / 2
            if axis == "v":
                edges.append((e1, y0, e1, y1))
                if e2 - e1 > _EPS:
                    edges.append((e2, y0, e2, y1))
                centers.append((mid, ey0, mid, ey1))
            else:
                edges.append((x0, e1, x1, e1))
                if e2 - e1 > _EPS:
                    edges.append((x0, e2, x1, e2))
                centers.append((ex0, mid, ex1, mid))
        _frame_walk(child, sub_rect, sub_ext, gx, gy, cells, edges, centers)


def frame_cells(key: str, ratio_pct: float, rect: Rect,
                gap_x: float, gap_y: float) -> Tuple[List[Rect], List[Segment]]:
    """Slots (ordem de leitura) e bordas de corte internas da moldura em `rect`.

    Em cada divisão o comprimento útil é o lado menos os espaçamentos, repartido
    pelos pesos; partes lado a lado usam `gap_x`, empilhadas `gap_y`. Cada corte
    com espaçamento > 0 devolve as suas duas bordas. Função pura (sem Tk nem Pillow).
    """
    cells: List[Rect] = []
    edges: List[Segment] = []
    _frame_walk(frame_tree(key, ratio_pct), rect, rect,
                max(0.0, gap_x), max(0.0, gap_y), cells, edges, [])
    return cells, edges


def _tree_has(node: FrameNode, axis: str) -> bool:
    if node is None:
        return False
    if node[0] == axis and len(node[1]) > 1:
        return True
    return any(_tree_has(child, axis) for _w, child in node[1])


def frame_geometry(cfg: "LayoutConfig") -> SheetGeometry:
    """`SheetGeometry` de uma moldura: slots, sangria por lado, marcas, linhas e avisos.

    Mesmas regras da grade: a sangria vai até metade do espaçamento da divisão
    vizinha ou até a margem externa, e as marcas ficam fora da área útil, uma por
    ponta de corte que toca a borda dela (ponta que encosta noutro corte não leva).
    """
    mo  = max(0.0, float(cfg.margin_outer_mm))
    mbx = max(0.0, float(cfg.margin_between_x_mm))
    mby = max(0.0, float(cfg.margin_between_y_mm))
    pw, ph = float(cfg.paper_w_mm), float(cfg.paper_h_mm)
    rect: Rect = (mo, mo, max(mo, pw - mo), max(mo, ph - mo))
    gx0, gy0, gx1, gy1 = rect

    tree = frame_tree(cfg.layout, cfg.layout_ratio_pct)
    cells: List[Rect] = []
    edges: List[Segment] = []
    centers: List[Segment] = []
    _frame_walk(tree, rect, (0.0, 0.0, pw, ph), mbx, mby, cells, edges, centers)

    bleed = clamp_float(cfg.bleed_mm, *BLEED_RANGE, 0.0)
    length = clamp_float(cfg.mark_length_mm, *MARK_LEN_RANGE, 4.0)
    offset = max(clamp_float(cfg.mark_offset_mm, *MARK_OFFSET_RANGE, 3.0), bleed)

    bleeds: List[Rect] = []
    sides: List[Tuple[float, float, float, float]] = []
    for x0, y0, x1, y1 in cells:
        l = min(bleed, mo if abs(x0 - gx0) <= _EPS else mbx / 2)
        r = min(bleed, mo if abs(x1 - gx1) <= _EPS else mbx / 2)
        t = min(bleed, mo if abs(y0 - gy0) <= _EPS else mby / 2)
        b = min(bleed, mo if abs(y1 - gy1) <= _EPS else mby / 2)
        sides.append((l, t, r, b))
        bleeds.append((x0 - l, y0 - t, x1 + r, y1 + b))

    cut_x = _unique_sorted([c[0] for c in cells] + [c[2] for c in cells])
    cut_y = _unique_sorted([c[1] for c in cells] + [c[3] for c in cells])

    marks: List[Segment] = []
    if cfg.cut_guide == "marks":
        # Os quatro lados da área útil também são cortes: dão as marcas dos cantos.
        border = [(gx0, gy0, gx0, gy1), (gx1, gy0, gx1, gy1),
                  (gx0, gy0, gx1, gy0), (gx0, gy1, gx1, gy1)]
        seen = set()

        def add(seg: Segment):
            key = tuple(round(v, 6) for v in seg)
            if key not in seen:           # espaçamento 0: dois cortes no mesmo lugar
                seen.add(key)
                marks.append(seg)

        for x1_, y1_, x2_, y2_ in border + edges:
            if abs(x1_ - x2_) <= _EPS:                         # corte vertical
                if abs(y1_ - gy0) <= _EPS:
                    add((x1_, gy0 - offset - length, x1_, gy0 - offset))
                if abs(y2_ - gy1) <= _EPS:
                    add((x1_, gy1 + offset, x1_, gy1 + offset + length))
            else:                                              # corte horizontal
                if abs(x1_ - gx0) <= _EPS:
                    add((gx0 - offset - length, y1_, gx0 - offset, y1_))
                if abs(x2_ - gx1) <= _EPS:
                    add((gx1 + offset, y1_, gx1 + offset + length, y1_))

    warnings: List[Tuple[str, str]] = []
    if cfg.cut_guide == "marks" and mo + 1e-9 < offset + length:
        warnings.append(("warn", "A margem externa precisa de pelo menos "
                                 f"{_fmt_mm(offset + length)} mm para as marcas."))
    if bleed > 0:
        for axis, gap, nome in (("v", mbx, "colunas"), ("h", mby, "linhas")):
            if _tree_has(tree, axis) and gap + 1e-9 < 2 * bleed:
                warnings.append(("warn",
                                 f"Espaçamento entre {nome} menor que 2× a sangria: "
                                 f"entre as {nome} coube {_fmt_mm(gap / 2)} mm."))
        if mo > 1e-9 and mo + 1e-9 < bleed:
            warnings.append(("warn",
                             f"A margem externa ({_fmt_mm(mo)} mm) é menor que a sangria "
                             f"({_fmt_mm(bleed)} mm): na borda da folha, a sangria vai "
                             f"só até {_fmt_mm(mo)} mm."))
        if cfg.cut_guide == "lines":
            warnings.append(("info", "Com sangria, use marcas de canto: "
                                     "as linhas riscam a sangria."))

    return SheetGeometry(cells, bleeds, sides, cut_x, cut_y, marks, offset,
                         rect, warnings, tuple(centers))


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

    def slot_rects_mm(self) -> List[Rect]:
        """Retângulo de cada slot em mm (ordem de leitura): moldura ou grade."""
        return list(sheet_geometry(self.cfg).cells)

    def slot_rects_px(self, dpi: Optional[int] = None) -> List[Tuple[int, int, int, int]]:
        """Slots em px (x0, y0, x1, y1). As BORDAS são arredondadas uma vez a partir
        dos mm — nunca somando larguras já arredondadas (CONTEXT, armadilha 12).
        Na grade o tamanho é o de `cell_px`, que a composição usa."""
        s = (dpi or self.cfg.dpi) * MM_TO_INCH

        def px(v: float) -> int:
            return int(math.floor(v * s + 0.5))

        geo = sheet_geometry(self.cfg)
        if self.cfg.layout == "grid":
            cw, ch = self.cell_px(dpi)
            return [(px(c[0]), px(c[1]), px(c[0]) + cw, px(c[1]) + ch)
                    for c in geo.cells]
        return [(px(c[0]), px(c[1]), px(c[2]), px(c[3])) for c in geo.cells]

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
        if self.cfg.layout != "grid":
            return self._quality_report_frame()
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

    def _entry_ratio(self, e: "ImageEntry", cw: int,
                     ch: int) -> Optional[Tuple[float, str]]:
        """(razão fonte/célula, nome) de uma imagem contra um slot de `cw × ch` px;
        None quando a guarda ignora o item (SVG, PDF sem backend ou ilegível)."""
        if is_pdf(e.path):
            if not PDF_OK:
                return None
            try:
                r = pdf_inner_ratio(e.path, e.page_index, cw, ch,
                                    self.cfg.auto_rotate, self.cfg.fit_mode,
                                    e.rotation)
            except Exception:
                return None                   # PDF ilegível nunca derruba a guarda
            if r is None:
                return None
            return r, f"{e.filename} · p. {e.page_index + 1} (imagem interna)"
        if is_vector(e.path):
            return None
        size = e.real_size()
        if not size:
            return None
        straight = min(size[0] / cw, size[1] / ch)
        turned   = min(size[1] / cw, size[0] / ch)
        if e.rotation:
            r = turned if e.rotation in (90, 270) else straight
        else:
            r = max(straight, turned) if self.cfg.auto_rotate else straight
        return r, e.filename

    def _quality_report_frame(self) -> dict:
        """Guarda de qualidade da moldura: cada imagem é medida contra o SLOT em que
        cai (posição `i` da lista expandida → slot `i % nup`). `cell`/`needed` trazem
        o slot da pior imagem, já com a sangria quando a arte a inclui."""
        rects = self.slot_rects_px()
        nup = len(rects)
        bp = self.bleed_px_included()
        sizes = [(max(1, x1 - x0) + 2 * bp, max(1, y1 - y0) + 2 * bp)
                 for x0, y0, x1, y1 in rects]
        worst_ratio = None
        worst_name = ""
        worst_slot = 0
        pos = 0
        for e in self.entries:
            q = max(1, e.quantity)
            slots = sorted({(pos + k) % nup for k in range(q)})
            pos += q
            for slot in slots:
                got = self._entry_ratio(e, *sizes[slot])
                if got is not None and (worst_ratio is None or got[0] < worst_ratio):
                    worst_ratio, worst_name = got
                    worst_slot = slot
        if worst_ratio is None:
            return {"level": "none", "ratio": 0.0, "worst": "",
                    "cell": sizes[0], "needed": sizes[0]}
        level = ("ok"   if worst_ratio >= QUALITY_OK else
                 "warn" if worst_ratio >= QUALITY_WARN else "bad")
        return {"level": level, "ratio": worst_ratio, "worst": worst_name,
                "cell": sizes[worst_slot], "needed": sizes[worst_slot]}

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
        if cfg.fit_mode == "fill":
            # `int()` trunca: 1500 × 1601/1500 dá 1600,999… → 1600, e o `crop`
            # abaixo passaria 1 px da imagem — o Pillow pinta esse px de preto.
            # No Preencher a imagem nunca pode ficar menor que a célula. FIX-007.
            nw, nh = max(nw, cw), max(nh, ch)
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
                   cw: int, ch: int, mo: int, mbx: int, mby: int,
                   segments: Optional[List[Tuple[int, int, int, int]]] = None):
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

        if segments is not None:         # moldura: cada linha é um segmento em px
            for seg in segments:
                fn(*seg)
            return

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
        if self.cfg.layout != "grid":
            return self._compose_frame(page_idx, image_paths, override_dpi)
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

    def _frame_bleed_px(self, geo: SheetGeometry, rects: List[Tuple[int, int, int, int]],
                        pw: int, ph: int, dpi: int) -> List[Tuple[int, int, int, int]]:
        """Sangria que coube em cada lado de cada slot, em px: a da geometria,
        limitada à metade do vão REAL em px até o vizinho que está do outro lado
        (ou à margem, na borda da folha). Assim nunca pinta pixel do vizinho."""
        s = dpi * MM_TO_INCH
        n = len(rects)
        if self.bleed_px(dpi) <= 0:
            return [(0, 0, 0, 0)] * n

        def px(v: float) -> int:
            return int(math.floor(v * s + 0.5))

        def overlap(a0: float, a1: float, b0: float, b1: float) -> bool:
            return b0 < a1 - _EPS and b1 > a0 + _EPS

        out = []
        for i in range(n):
            cx0, cy0, cx1, cy1 = geo.cells[i]
            rx0, ry0, rx1, ry1 = rects[i]
            gaps = {"l": [], "t": [], "r": [], "b": []}
            for j in range(n):
                if j == i:
                    continue
                jx0, jy0, jx1, jy1 = geo.cells[j]
                qx0, qy0, qx1, qy1 = rects[j]
                if overlap(cy0, cy1, jy0, jy1):
                    if jx1 <= cx0 + _EPS:
                        gaps["l"].append(rx0 - qx1)
                    if jx0 >= cx1 - _EPS:
                        gaps["r"].append(qx0 - rx1)
                if overlap(cx0, cx1, jx0, jx1):
                    if jy1 <= cy0 + _EPS:
                        gaps["t"].append(ry0 - qy1)
                    if jy0 >= cy1 - _EPS:
                        gaps["b"].append(qy0 - ry1)
            edge = {"l": rx0, "t": ry0, "r": pw - rx1, "b": ph - ry1}
            sl, st, sr, sb = (px(v) for v in geo.bleed_sides[i])
            lim = {k: (min(g) // 2 if g else edge[k]) for k, g in gaps.items()}
            out.append(tuple(max(0, min(v, lim[k]))
                             for k, v in zip("ltrb", (sl, st, sr, sb))))
        return out

    def _compose_frame(self, page_idx: int, image_paths: List[Any],
                       override_dpi: Optional[int] = None) -> Image.Image:
        """Compõe uma folha de moldura. Mesmas regras da grade, mas cada slot tem o
        seu retângulo: bordas arredondadas UMA vez a partir dos mm, tamanho derivado
        delas, e cada imagem encaixada no seu slot (DEC-018)."""
        cfg = self.cfg
        dpi = override_dpi or cfg.dpi
        pw, ph = self._page_px(override_dpi)
        bg = self._hex_rgb(cfg.bg_color)
        page = Image.new("RGB", (pw, ph), bg)

        geo = sheet_geometry(cfg)
        rects = self.slot_rects_px(override_dpi)
        nup = len(rects)
        bp_full = self.bleed_px(dpi)
        sides = self._frame_bleed_px(geo, rects, pw, ph, dpi)

        start = page_idx * nup
        for slot in range(nup):
            idx = start + slot
            if idx >= len(image_paths):
                break
            x, y, x1, y1 = rects[slot]
            cw, ch = max(1, x1 - x), max(1, y1 - y)
            l, t, r, b = sides[slot]

            try:
                src = as_ref(image_paths[idx])
                if bp_full > 0 and cfg.bleed_mode == "included":
                    bw, bh = cw + 2 * bp_full, ch + 2 * bp_full
                    img = open_source(src.path, bw, bh, page=src.page,
                                      auto_rotate=cfg.auto_rotate,
                                      fit_mode=cfg.fit_mode,
                                      rotation=src.rotation)
                    big = self._place_image(img, bw, bh, bg, src.rotation)
                    cell = big.crop((bp_full - l, bp_full - t,
                                     bp_full + cw + r, bp_full + ch + b))
                else:
                    img = open_source(src.path, cw, ch, page=src.page,
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
            s = dpi * MM_TO_INCH
            segs = [tuple(int(math.floor(v * s + 0.5)) for v in seg)
                    for seg in geo.cuts]
            self._draw_cuts(page, 0, 0, 0, 0, 0, 0, 0, segments=segs)
        elif cfg.cut_guide == "marks":
            self._draw_marks(page, geo, dpi,
                             (min(r_[0] for r_ in rects), min(r_[1] for r_ in rects),
                              max(r_[2] for r_ in rects), max(r_[3] for r_ in rects)))

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
