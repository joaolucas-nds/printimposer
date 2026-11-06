#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes headless do núcleo do PrintImposer.

Rodam SEM abrir janela: o `ImpositionEngine` não depende de Tkinter (DEC-004),
então stubamos tkinter/customtkinter e importamos só o que interessa.

    python tests/test_engine.py

Cobre: contagem de folhas, geometria da página e da célula, modos de ajuste,
auto-rotate, guarda de qualidade, gravação em um e dois destinos, restauração
do DPI após o preview e o conteúdo do .bat gerado.

O que estes testes NÃO cobrem: qualquer coisa de interface. Janela, sashes e
DPI awareness só se validam abrindo o app (ver CLAUDE.md, seção Smoke test).
"""

import ast
import os
import sys
import threading
import types
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# ── Stub de GUI: permite importar o módulo sem Tk instalado ──────────────────
if "tkinter" not in sys.modules:
    tk_stub = types.ModuleType("tkinter")
    for name in ("StringVar", "BooleanVar", "DoubleVar", "Canvas",
                 "PanedWindow", "Frame"):
        setattr(tk_stub, name, type(name, (), {}))
    sys.modules["tkinter"] = tk_stub
    for sub in ("filedialog", "messagebox", "colorchooser"):
        sys.modules[f"tkinter.{sub}"] = types.ModuleType(sub)
        setattr(tk_stub, sub, sys.modules[f"tkinter.{sub}"])

if "customtkinter" not in sys.modules:
    ctk_stub = types.ModuleType("customtkinter")
    _base = type("CTkBase", (), {})
    for name in ("CTk", "CTkFrame", "CTkLabel", "CTkButton", "CTkEntry",
                 "CTkCheckBox", "CTkOptionMenu", "CTkScrollableFrame",
                 "CTkProgressBar", "CTkFont", "CTkInputDialog"):
        setattr(ctk_stub, name, _base)
    ctk_stub.set_appearance_mode = lambda *_: None
    ctk_stub.set_default_color_theme = lambda *_: None
    sys.modules["customtkinter"] = ctk_stub

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
import print_imposer as pi  # noqa: E402


def make_image(path: Path, w: int, h: int, color=(120, 90, 200)):
    Image.new("RGB", (w, h), color).save(path)
    return str(path)


class GridTests(unittest.TestCase):
    """Grade livre (DEC-009): qualquer combinação, sem lista cadastrada."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.img = make_image(Path(self.tmp) / "a.png", 1240, 1748)

    def _engine(self, cols, rows, qty=1, n=1):
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = cols, rows, 72
        entries = []
        for i in range(n):
            e = pi.ImageEntry(self.img)
            e.quantity = qty
            entries.append(e)
        return pi.ImpositionEngine(entries, cfg)

    def test_2x6_funciona_sem_cadastro(self):
        """O caso que motivou a DEC-009: 2x6 não existia na lista fixa."""
        eng = self._engine(2, 6)
        self.assertEqual(eng.cfg.nup(), 12)

    def test_grade_arbitraria(self):
        for cols, rows in ((5, 3), (7, 2), (1, 9), (3, 11)):
            with self.subTest(cols=cols, rows=rows):
                self.assertEqual(self._engine(cols, rows).cfg.nup(), cols * rows)

    def test_contagem_de_folhas(self):
        # 10 imagens em grade 2x2 (4 por folha) => 3 folhas
        eng = self._engine(2, 2, qty=10, n=1)
        self.assertEqual(eng.total_expanded(), 10)
        self.assertEqual(eng.total_pages(), 3)

    def test_folha_exata_nao_gera_extra(self):
        eng = self._engine(2, 2, qty=8, n=1)
        self.assertEqual(eng.total_pages(), 2)

    def test_lista_vazia_zero_folhas(self):
        cfg = pi.LayoutConfig()
        self.assertEqual(pi.ImpositionEngine([], cfg).total_pages(), 0)

    def test_atalhos_batem_com_a_grade(self):
        for label, (c, r) in pi.NUP_SHORTCUTS.items():
            with self.subTest(label=label):
                self.assertGreaterEqual(c, 1)
                self.assertGreaterEqual(r, 1)
                self.assertLessEqual(c, pi.MAX_COLS)
                self.assertLessEqual(r, pi.MAX_ROWS)


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.cfg = pi.LayoutConfig()
        self.eng = pi.ImpositionEngine([], self.cfg)

    def test_a4_300dpi(self):
        self.cfg.dpi = 300
        self.assertEqual(self.eng._page_px(), (2480, 3508))

    def test_celula_2x2_sem_margem(self):
        self.cfg.dpi = 300
        self.cfg.cols = self.cfg.rows = 2
        self.cfg.margin_outer_mm = 0.0
        self.cfg.margin_between_x_mm = self.cfg.margin_between_y_mm = 0.0
        cw, ch = self.eng.cell_px()
        self.assertEqual((cw, ch), (1240, 1754))   # metade exata de A4

    def test_margens_encolhem_a_celula(self):
        self.cfg.dpi = 300
        self.cfg.cols = self.cfg.rows = 2
        base_w, base_h = self.eng.cell_px()
        self.cfg.margin_outer_mm = 5.0
        self.cfg.margin_between_x_mm = self.cfg.margin_between_y_mm = 3.0
        new_w, new_h = self.eng.cell_px()
        self.assertLess(new_w, base_w)
        self.assertLess(new_h, base_h)

    def test_celula_mm_coerente(self):
        self.cfg.cols, self.cfg.rows = 2, 2
        self.cfg.margin_outer_mm = 0.0
        self.cfg.margin_between_x_mm = self.cfg.margin_between_y_mm = 0.0
        cw, ch = self.eng.cell_mm()
        self.assertAlmostEqual(cw, 105.0, places=1)   # A6 dentro de A4
        self.assertAlmostEqual(ch, 148.5, places=1)


class ComposeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = pi.LayoutConfig()
        self.cfg.dpi = 72
        self.cfg.cols = self.cfg.rows = 2

    def _engine(self, paths):
        return pi.ImpositionEngine([pi.ImageEntry(p) for p in paths], self.cfg)

    def test_pagina_tem_tamanho_do_papel(self):
        p = make_image(self.tmp / "x.png", 400, 560)
        eng = self._engine([p])
        page = eng.compose_page(0, eng._expand())
        self.assertEqual(page.size, eng._page_px())

    def test_modos_de_ajuste_nao_quebram(self):
        p = make_image(self.tmp / "y.png", 400, 200)
        for mode in ("fit", "fill", "stretch"):
            with self.subTest(mode=mode):
                self.cfg.fit_mode = mode
                eng = self._engine([p])
                self.assertEqual(eng.compose_page(0, eng._expand()).size,
                                 eng._page_px())

    def test_estilos_de_corte_nao_quebram(self):
        p = make_image(self.tmp / "z.png", 300, 400)
        self.cfg.cut_guide = "lines"
        for style in pi.LINE_STYLES:
            with self.subTest(style=style):
                self.cfg.cut_style = style
                eng = self._engine([p])
                self.assertEqual(eng.compose_page(0, eng._expand()).size,
                                 eng._page_px())

    def test_arquivo_corrompido_nao_derruba_a_folha(self):
        bad = self.tmp / "quebrado.png"
        bad.write_bytes(b"isto nao e um png")
        eng = self._engine([str(bad)])
        # A célula vira um aviso vermelho, mas a folha sai.
        self.assertEqual(eng.compose_page(0, [str(bad)]).size, eng._page_px())

    def test_preview_restaura_o_dpi(self):
        """Armadilha do CONTEXT: compose_page troca cfg.dpi temporariamente."""
        p = make_image(self.tmp / "w.png", 300, 400)
        eng = self._engine([p])
        self.cfg.dpi = 300
        eng.preview_page(0)
        self.assertEqual(self.cfg.dpi, 300)

    def test_dpi_restaurado_mesmo_com_erro(self):
        eng = self._engine([])
        self.cfg.dpi = 300
        try:
            eng.compose_page(0, ["/caminho/inexistente.png"], override_dpi=72)
        except Exception:
            pass
        self.assertEqual(self.cfg.dpi, 300)


class QualityGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = pi.LayoutConfig()
        self.cfg.dpi = 300
        self.cfg.cols = self.cfg.rows = 2
        self.cfg.auto_rotate = False

    def _report(self, w, h):
        p = make_image(self.tmp / f"q{w}x{h}.png", w, h)
        return pi.ImpositionEngine([pi.ImageEntry(p)], self.cfg).quality_report()

    def test_fonte_grande_e_ok(self):
        self.assertEqual(self._report(1240, 1754)["level"], "ok")

    def test_fonte_pequena_e_ruim(self):
        r = self._report(300, 420)
        self.assertEqual(r["level"], "bad")
        self.assertLess(r["ratio"], pi.QUALITY_WARN)

    def test_fonte_limitrofe_avisa(self):
        r = self._report(1000, 1420)     # ~80% da célula
        self.assertEqual(r["level"], "warn")

    def test_sem_imagens_sem_veredito(self):
        self.assertEqual(
            pi.ImpositionEngine([], self.cfg).quality_report()["level"], "none")

    def test_auto_rotate_considera_orientacao_girada(self):
        """Imagem deitada em célula em pé: com auto-rotate, não é upscale."""
        p = make_image(self.tmp / "deitada.png", 1754, 1240)
        self.cfg.auto_rotate = True
        eng = pi.ImpositionEngine([pi.ImageEntry(p)], self.cfg)
        self.assertEqual(eng.quality_report()["level"], "ok")


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.out1 = self.tmp / "destino1"; self.out1.mkdir()
        self.out2 = self.tmp / "destino2"; self.out2.mkdir()
        self.cfg = pi.LayoutConfig()
        self.cfg.dpi = 72
        self.cfg.cols = self.cfg.rows = 2
        self.cfg.output_dir = str(self.out1)
        self.img = make_image(self.tmp / "src.png", 400, 560)

    def _engine(self, qty=5):
        e = pi.ImageEntry(self.img); e.quantity = qty
        return pi.ImpositionEngine([e], self.cfg)

    def test_png_e_o_padrao(self):
        self.assertEqual(pi.LayoutConfig().output_format, "PNG")
        self.assertEqual(pi.OUT_FORMATS[0], "PNG")

    def test_png_um_arquivo_por_folha(self):
        eng = self._engine(qty=5)          # 5 imagens, 4 por folha => 2 folhas
        saved = eng.save(eng.generate_all())
        self.assertEqual(len(saved), 2)
        self.assertTrue(all(s.endswith(".png") for s in saved))

    def test_pdf_arquivo_unico(self):
        self.cfg.output_format = "PDF"
        eng = self._engine(qty=9)          # 3 folhas, mas 1 só PDF
        saved = eng.save(eng.generate_all())
        self.assertEqual(len(saved), 1)
        self.assertTrue(saved[0].endswith(".pdf"))

    def test_dois_destinos_gravam_nos_dois(self):
        self.cfg.output_dir2 = str(self.out2)
        self.cfg.output_dir2_on = True
        eng = self._engine(qty=4)          # 1 folha
        saved = eng.save(eng.generate_all())
        self.assertEqual(len(saved), 2)
        self.assertEqual(len(os.listdir(self.out1)), 1)
        self.assertEqual(len(os.listdir(self.out2)), 1)

    def test_destino_duplicado_e_ignorado(self):
        self.cfg.output_dir2 = str(self.out1)   # mesmo caminho do primeiro
        self.cfg.output_dir2_on = True
        self.assertEqual(len(self._engine().output_dirs()), 1)

    def test_nao_sobrescreve(self):
        eng = self._engine(qty=4)
        first  = eng.save(eng.generate_all())
        second = eng.save(eng.generate_all())
        self.assertNotEqual(first[0], second[0])
        self.assertTrue(os.path.exists(first[0]))

    def test_ultima_folha_incompleta_ainda_sai(self):
        eng = self._engine(qty=5)          # deixa 3 slots vazios na 2a folha
        pages = eng.generate_all()
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[1].size, eng._page_px())


class ConfigTests(unittest.TestCase):
    def test_roundtrip_dict(self):
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = 3, 7, 600
        clone = pi.LayoutConfig()
        clone.from_dict(cfg.to_dict())
        self.assertEqual((clone.cols, clone.rows, clone.dpi), (3, 7, 600))

    def test_preset_nao_carrega_pastas(self):
        """Preset é layout; caminho de pasta é de máquina, não de preset."""
        cfg = pi.LayoutConfig()
        cfg.output_dir = "/algum/lugar"
        d = cfg.preset_dict()
        self.assertNotIn("output_dir", d)
        self.assertNotIn("input_dir", d)
        self.assertIn("cols", d)

    def test_from_dict_ignora_campo_desconhecido(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"campo_que_nao_existe": 1, "cols": 5})
        self.assertEqual(cfg.cols, 5)
        self.assertFalse(hasattr(cfg, "campo_que_nao_existe"))

    def test_cor_invalida_cai_para_branco(self):
        self.assertEqual(pi.ImpositionEngine._hex_rgb("nao-e-cor"), (255, 255, 255))


class PdfWriterTests(unittest.TestCase):
    """Escritor de PDF próprio (DEC-014): sem perda por padrão."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = pi.LayoutConfig()
        self.cfg.dpi = 72
        self.cfg.cols = self.cfg.rows = 2
        self.cfg.output_format = "PDF"
        self.cfg.output_dir = str(self.tmp / "out")
        img = make_image(self.tmp / "src.png", 400, 560)
        e = pi.ImageEntry(img); e.quantity = 9        # 3 folhas
        self.eng = pi.ImpositionEngine([e], self.cfg)

    def _pdf(self):
        saved = self.eng.save(self.eng.generate_all())
        return Path(saved[0]).read_bytes()

    def test_sem_perda_e_o_padrao(self):
        self.assertEqual(pi.LayoutConfig().pdf_compression, "lossless")

    def test_sem_perda_usa_flate_e_nao_dct(self):
        data = self._pdf()
        self.assertEqual(data.count(b"/FlateDecode"), 3)
        self.assertEqual(data.count(b"/DCTDecode"), 0)
        self.assertEqual(data.count(b"/Predictor 15"), 3)

    def test_xref_aponta_para_os_objetos(self):
        data = self._pdf()
        start = int(data.rsplit(b"startxref\n", 1)[1].split(b"\n")[0])
        self.assertTrue(data[start:].startswith(b"xref\n"))
        lines = data[start:].split(b"\n")
        n = int(lines[1].split()[1])
        self.assertEqual(n, 1 + 2 + 3 * 3)            # 0 + catálogo/páginas + 3 folhas
        for num in range(1, n):
            off = int(lines[2 + num][:10])
            self.assertTrue(data[off:].startswith(b"%d 0 obj\n" % num), num)

    def test_idat_embutido_igual_ao_do_png(self):
        import io
        pages = self.eng.generate_all()
        buf = io.BytesIO(); pages[0].save(buf, "PNG")
        _w, _h, idat = pi.png_idat(buf.getvalue())
        out = self.tmp / "x.pdf"
        pi.write_pdf(pages, str(out), 72, "lossless")
        self.assertIn(idat, out.read_bytes())         # byte a byte, sem recomprimir

    def test_columns_e_a_largura_da_folha(self):
        data = self._pdf()
        w = self.eng._page_px()[0]
        self.assertIn(b"/Columns %d" % w, data)

    def test_pdf_jpeg_usa_dct(self):
        self.cfg.pdf_compression = "jpeg"
        data = self._pdf()
        self.assertEqual(data.count(b"/DCTDecode"), 3)
        self.assertEqual(data.count(b"/FlateDecode"), 0)

    def test_pdf_jpeg_usa_a_qualidade_escolhida(self):
        import io
        pages = self.eng.generate_all()
        sizes = {}
        for q in (50, 95):
            out = self.tmp / f"q{q}.pdf"
            pi.write_pdf(pages[:1], str(out), 72, "jpeg", q)
            buf = io.BytesIO(); pages[0].save(buf, "JPEG", quality=q)
            self.assertIn(buf.getvalue(), out.read_bytes())
            sizes[q] = len(buf.getvalue())
        self.assertLess(sizes[50], sizes[95])

    def test_jpeg_usa_a_qualidade_do_campo(self):
        import io
        self.cfg.output_format = "JPEG"
        self.cfg.jpeg_quality = 60
        pages = self.eng.generate_all()
        saved = self.eng.save(pages)
        buf = io.BytesIO(); pages[0].convert("RGB").save(
            buf, "JPEG", quality=60, dpi=(72, 72))
        self.assertEqual(Path(saved[0]).stat().st_size, len(buf.getvalue()))

    def test_qualidade_fora_do_limite_e_ajustada(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"jpeg_quality": 10})
        self.assertEqual(cfg.jpeg_quality, 50)
        cfg.from_dict({"jpeg_quality": 500})
        self.assertEqual(cfg.jpeg_quality, 100)
        self.assertEqual(pi.clamp_jpeg_quality("abc", 95), 95)

    def test_png_entrelacado_e_recusado(self):
        import io
        buf = io.BytesIO()
        Image.new("RGB", (8, 8)).save(buf, "PNG")
        raw = bytearray(buf.getvalue())
        raw[28] = 1                                    # byte de entrelaçamento no IHDR
        with self.assertRaises(ValueError):
            pi.png_idat(bytes(raw))


class SpacingTests(unittest.TestCase):
    """Espaçamento independente em X (colunas) e Y (linhas)."""

    def setUp(self):
        self.cfg = pi.LayoutConfig()
        self.cfg.dpi = 300
        self.cfg.cols = self.cfg.rows = 2
        self.eng = pi.ImpositionEngine([], self.cfg)

    def test_so_x_afasta_so_colunas(self):
        base_w, base_h = self.eng.cell_px()
        self.cfg.margin_between_x_mm = 10.0
        self.cfg.margin_between_y_mm = 0.0
        w, h = self.eng.cell_px()
        self.assertLess(w, base_w)
        self.assertEqual(h, base_h)

    def test_so_y_afasta_so_linhas(self):
        base_w, base_h = self.eng.cell_px()
        self.cfg.margin_between_y_mm = 10.0
        w, h = self.eng.cell_px()
        self.assertEqual(w, base_w)
        self.assertLess(h, base_h)

    def test_cell_mm_acompanha_os_eixos(self):
        self.cfg.margin_between_x_mm = 10.0
        cw, ch = self.eng.cell_mm()
        self.assertAlmostEqual(cw, 100.0, places=1)    # (210 - 10) / 2
        self.assertAlmostEqual(ch, 148.5, places=1)

    def test_linha_de_corte_acompanha_o_espaco(self):
        tmp = Path(tempfile.mkdtemp())
        self.cfg.dpi = 100
        self.cfg.margin_between_x_mm = 10.0
        self.cfg.margin_between_y_mm = 0.0
        self.cfg.cut_guide = "lines"
        self.cfg.cut_color = "#FF0000"
        self.cfg.cut_width_px = 1
        img = make_image(tmp / "a.png", 200, 280, (0, 0, 255))
        eng = pi.ImpositionEngine([], self.cfg)
        page = eng.compose_page(0, [img] * 4)
        cw, ch = eng.cell_px()
        x_cut = cw + eng._mm_px(10.0) // 2             # meio do vão entre colunas
        self.assertEqual(page.getpixel((x_cut, 5)), (255, 0, 0))
        self.assertEqual(page.getpixel((5, ch)), (255, 0, 0))   # Y = 0: rente à célula

    def test_config_antiga_vira_x_igual_y(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"cols": 3, "margin_between_mm": 4.5})
        self.assertEqual((cfg.margin_between_x_mm, cfg.margin_between_y_mm), (4.5, 4.5))
        self.assertFalse(hasattr(cfg, "margin_between_mm"))

    def test_preset_antigo_vira_x_igual_y_sem_mutar_o_dict(self):
        cfg = pi.LayoutConfig()
        preset = {"cols": 2, "margin_between_mm": 2.0}
        cfg.from_dict(preset)
        self.assertEqual((cfg.margin_between_x_mm, cfg.margin_between_y_mm), (2.0, 2.0))
        self.assertIn("margin_between_mm", preset)     # o preset salvo não é alterado

    def test_campos_novos_mandam_sobre_o_antigo(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"margin_between_mm": 4.0, "margin_between_x_mm": 1.0})
        self.assertEqual((cfg.margin_between_x_mm, cfg.margin_between_y_mm), (1.0, 4.0))

    def test_preset_leva_os_campos_novos(self):
        d = pi.LayoutConfig().preset_dict()
        for k in ("margin_between_x_mm", "margin_between_y_mm",
                  "pdf_compression", "jpeg_quality"):
            self.assertIn(k, d)
        self.assertNotIn("margin_between_mm", d)


class SheetInfoTests(unittest.TestCase):
    def test_folha_a4_300dpi(self):
        eng = pi.ImpositionEngine([], pi.LayoutConfig())
        w, h, mb = eng.sheet_info()
        self.assertEqual((w, h), (2480, 3508))
        self.assertAlmostEqual(mb, 2480 * 3508 * 3 / 1048576, places=6)


class ExtraFormatsTests(unittest.TestCase):
    def test_avif_presente_sse_o_pillow_le(self):
        from PIL import features
        self.assertEqual('.avif' in pi.RASTER_EXT, bool(features.check("avif")))

    def test_heic_presente_sse_pillow_heif_registrou(self):
        self.assertEqual('.heic' in pi.RASTER_EXT, pi.HEIF_OK)
        self.assertEqual('.heif' in pi.RASTER_EXT, pi.HEIF_OK)

    def test_sem_pillow_heif_a_sonda_falha_sem_quebrar(self):
        saved = sys.modules.get("pillow_heif")
        sys.modules["pillow_heif"] = None              # import vira ImportError
        try:
            self.assertFalse(pi._probe_heif())
        finally:
            if saved is None:
                sys.modules.pop("pillow_heif", None)
            else:
                sys.modules["pillow_heif"] = saved


class SvgTests(unittest.TestCase):
    """Entrada SVG. Pulados quando não há back-end capaz de renderizar."""

    SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 105 148" '
           'width="105" height="148"><rect width="105" height="148" fill="#2b5c8a"/>'
           '<circle cx="52" cy="60" r="30" fill="#f0c419"/></svg>')

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.svg = self.tmp / "card.svg"
        self.svg.write_text(self.SVG, encoding="utf-8")

    def test_deteccao_e_coerente_com_a_lista(self):
        """REGRESSÃO: importar a lib não basta — tem de renderizar de verdade.

        `svglib` importa sem erro mas depende de rlPyCairo/_rl_renderPM para
        desenhar. A versão anterior aceitava .svg na lista e só quebrava na
        geração. A sondagem agora faz um render real.
        """
        self.assertEqual('.svg' in pi.SUPPORTED_EXT, pi.SVG_BACKEND is not None)

    @unittest.skipIf(pi.SVG_BACKEND is None, "sem back-end de SVG")
    def test_rasteriza_dentro_da_caixa(self):
        for box in ((200, 280), (1240, 1754)):
            with self.subTest(box=box):
                img = pi.rasterize_svg(str(self.svg), *box)
                self.assertLessEqual(img.width,  box[0])
                self.assertLessEqual(img.height, box[1])

    @unittest.skipIf(pi.SVG_BACKEND is None, "sem back-end de SVG")
    def test_escala_com_a_celula_zero_upscale(self):
        """O ganho central do SVG: o desenho é recalculado, não esticado."""
        small = pi.rasterize_svg(str(self.svg), 200, 280)
        big   = pi.rasterize_svg(str(self.svg), 1240, 1754)
        self.assertGreater(big.width, small.width * 4)

    @unittest.skipIf(pi.SVG_BACKEND is None, "sem back-end de SVG")
    def test_modulos_do_backend_ficam_acessiveis(self):
        """REGRESSÃO: o probe importava local e o nome sumia do escopo do módulo."""
        self.assertTrue(pi._SVG_MODS)
        pi.rasterize_svg(str(self.svg), 64, 90)   # levantaria NameError antes

    @unittest.skipIf(pi.SVG_BACKEND is None, "sem back-end de SVG")
    def test_folha_com_svg(self):
        cfg = pi.LayoutConfig()
        cfg.dpi, cfg.cols, cfg.rows = 72, 2, 2
        e = pi.ImageEntry(str(self.svg)); e.quantity = 4
        eng = pi.ImpositionEngine([e], cfg)
        self.assertEqual(eng.compose_page(0, eng._expand()).size, eng._page_px())

    @unittest.skipIf(pi.SVG_BACKEND is None, "sem back-end de SVG")
    def test_svg_fora_da_guarda_de_qualidade(self):
        """Vetor nunca dá upscale, então não entra no veredito."""
        cfg = pi.LayoutConfig(); cfg.dpi = 300
        eng = pi.ImpositionEngine([pi.ImageEntry(str(self.svg))], cfg)
        self.assertEqual(eng.quality_report()["level"], "none")


class PdfInputTests(unittest.TestCase):
    """Entrada PDF (F4 etapa 2). Os testes com stub rodam sem `pypdfium2`;
    os de render real são pulados sem ele, como os de SVG."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pdf = self.tmp / "livro.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 stub")     # só precisa existir (mtime da miniatura)
        self.calls = []

        def fake_raster(path, page, bw, bh, fit_mode="fit"):
            self.calls.append((page, bw, bh))
            shade = 40 + 60 * page
            return Image.new("RGBA", (bw, bh), (shade, shade, shade, 255))

        self.patches = [
            mock.patch.object(pi, "SUPPORTED_EXT", pi.SUPPORTED_EXT | {".pdf"}),
            mock.patch.object(pi, "rasterize_pdf", fake_raster),
            mock.patch.object(pi, "pdf_page_size", lambda path, page: (300.0, 200.0)),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def _engine(self, entries, cell=(2, 2), **cfg_kw):
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = cell[0], cell[1], 72
        for k, v in cfg_kw.items():
            setattr(cfg, k, v)
        return pi.ImpositionEngine(entries, cfg)

    def test_sem_backend_pdf_fora_de_extensoes_e_seletor(self):
        self.assertEqual(".pdf" in pi.PDF_EXT, pi.PDF_OK)
        tipos = pi.ImageListPanel._filetypes(None)
        self.assertEqual(any(t[0] == "PDF" for t in tipos), pi.PDF_OK)
        self.assertNotIn(".pdf", pi.RASTER_EXT)

    def test_n_paginas_viram_n_itens_com_rotulo(self):
        with mock.patch.object(pi, "pdf_page_count", lambda p: 3):
            items, skipped = pi.plan_ingest([str(self.pdf)])
        self.assertEqual(items, [(str(self.pdf), i, 3) for i in range(3)])
        self.assertEqual(skipped, [])
        e = pi.ImageEntry(*items[1])
        self.assertEqual(e.page_label, " · p. 2/3")
        self.assertEqual(pi.ImageEntry(str(self.pdf)).page_label, "")

    def test_confirmacao_acima_de_50_paginas(self):
        perguntas = []

        def nao(nome, n):
            perguntas.append((nome, n))
            return False

        with mock.patch.object(pi, "pdf_page_count", lambda p: 120):
            items, skipped = pi.plan_ingest([str(self.pdf)], confirm_many=nao)
            self.assertEqual(items, [])
            self.assertEqual(perguntas, [("livro.pdf", 120)])
            self.assertEqual(skipped[0][0], "livro.pdf")
            items, _ = pi.plan_ingest([str(self.pdf)], confirm_many=lambda n, c: True)
            self.assertEqual(len(items), 120)
        with mock.patch.object(pi, "pdf_page_count", lambda p: 50):
            items, _ = pi.plan_ingest([str(self.pdf)], confirm_many=nao)
            self.assertEqual(len(items), 50)       # 50 exatos não pede confirmação

    def test_pdf_ilegivel_vai_para_pulados_sem_derrubar_o_lote(self):
        bom = make_image(self.tmp / "ok.png", 100, 100)

        def contador(p):
            raise RuntimeError("Failed to load document (PDFium: Incorrect password error)")

        with mock.patch.object(pi, "pdf_page_count", contador):
            items, skipped = pi.plan_ingest([bom, str(self.pdf)])
        self.assertEqual(items, [(bom, 0, 1)])
        self.assertEqual(skipped, [("livro.pdf", "protegido por senha")])
        with mock.patch.object(pi, "pdf_page_count", lambda p: 0):
            _, skipped = pi.plan_ingest([str(self.pdf)])
        self.assertEqual(skipped, [("livro.pdf", "sem páginas")])
        with mock.patch.object(pi, "pdf_page_count",
                               mock.Mock(side_effect=ValueError("lixo"))):
            _, skipped = pi.plan_ingest([str(self.pdf)])
        self.assertEqual(skipped, [("livro.pdf", "ilegível ou corrompido")])

    def test_caixa_de_render_na_orientacao_final(self):
        """Página deitada (300×200 pt) em célula em pé: com Auto-Rotate a caixa
        pedida ao renderizador é (ch, cw) — nada é ampliado depois do giro."""
        e = pi.ImageEntry(str(self.pdf))
        eng = self._engine([e], cell=(2, 2), paper_w_mm=100.0, paper_h_mm=200.0,
                           auto_rotate=True)
        cw, ch = eng.cell_px(72)
        self.assertLess(cw, ch)                    # célula em pé
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        self.assertEqual(self.calls[-1][1:], (ch, cw))
        # Sem Auto-Rotate: caixa é a própria célula.
        eng.cfg.auto_rotate = False
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        self.assertEqual(self.calls[-1][1:], (cw, ch))
        # Mesma orientação (célula deitada): também (cw, ch).
        eng2 = self._engine([e], cell=(1, 1), paper_w_mm=200.0, paper_h_mm=100.0,
                            auto_rotate=True)
        cw2, ch2 = eng2.cell_px(72)
        self.calls.clear()
        eng2.compose_page(0, eng2._expand(), override_dpi=72)
        self.assertEqual(self.calls[-1][1:], (cw2, ch2))

    def test_pdf_fora_da_guarda_de_qualidade(self):
        eng = self._engine([pi.ImageEntry(str(self.pdf))], cell=(4, 4))
        self.assertEqual(eng.quality_report()["level"], "none")

    def test_miniatura_distingue_paginas(self):
        a = pi.ImageEntry(str(self.pdf), 0, 2)
        b = pi.ImageEntry(str(self.pdf), 1, 2)
        self.assertIsNotNone(a.pil_thumb)
        self.assertNotEqual(a.pil_thumb.getpixel((28, 28)), b.pil_thumb.getpixel((28, 28)))

    def test_referencia_aceita_str_e_sourceref(self):
        img = make_image(self.tmp / "r.png", 300, 400)
        eng = self._engine([pi.ImageEntry(img)], cell=(2, 2))
        self.assertIsInstance(eng._expand()[0], pi.SourceRef)
        a = eng.compose_page(0, [img])
        b = eng.compose_page(0, [pi.SourceRef(img)])
        self.assertEqual(a.tobytes(), b.tobytes())

    def test_pagina_certa_vai_para_o_render(self):
        entradas = [pi.ImageEntry(str(self.pdf), i, 3) for i in range(3)]
        eng = self._engine(entradas, cell=(2, 2))
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        self.assertEqual([c[0] for c in self.calls], [0, 1, 2])


@unittest.skipUnless(pi.PDF_OK, "sem pypdfium2")
class PdfRealTests(unittest.TestCase):
    """Render real com `pypdfium2`. PDFs de teste feitos pelo `write_pdf` (DEC-014)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        # 3 páginas: duas em pé (~100×140 mm) e uma DEITADA (~140×100 mm).
        tamanhos = [(394, 551), (394, 551), (551, 394)]
        cores = [(200, 30, 30), (30, 200, 30), (30, 30, 200)]
        pags = [Image.new("RGB", t, c) for t, c in zip(tamanhos, cores)]
        self.pdf = str(self.tmp / "tres.pdf")
        pi.write_pdf(pags, self.pdf, 100)

    def test_sondagem_guardou_o_modulo(self):
        self.assertTrue(pi._PDF_MODS)
        self.assertIn(".pdf", pi.SUPPORTED_EXT)

    def test_tres_paginas_viram_tres_itens(self):
        items, skipped = pi.plan_ingest([self.pdf])
        self.assertEqual([(i[1], i[2]) for i in items], [(0, 3), (1, 3), (2, 3)])
        self.assertEqual(skipped, [])
        self.assertTrue(all(pi.ImageEntry(*i).pil_thumb is not None for i in items))

    def test_arquivo_corrompido_e_pulado(self):
        ruim = self.tmp / "ruim.pdf"
        ruim.write_text("isto nao e um pdf")
        items, skipped = pi.plan_ingest([str(ruim), self.pdf])
        self.assertEqual(len(items), 3)
        self.assertEqual([s[0] for s in skipped], ["ruim.pdf"])

    def test_folha_2x2_em_png_e_pdf(self):
        items, _ = pi.plan_ingest([self.pdf])
        entries = [pi.ImageEntry(*i) for i in items]
        entries[0].quantity = 2
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = 2, 2, 300
        cfg.output_dir = str(self.tmp / "out")
        for fmt in ("PNG", "PDF"):
            cfg.output_format = fmt
            eng = pi.ImpositionEngine(entries, cfg)
            saved = eng.save(eng.generate_all())
            self.assertTrue(saved and all(os.path.getsize(s) > 0 for s in saved))

    def test_paisagem_em_celula_retrato_sem_ampliacao(self):
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = 2, 2, 300
        cfg.auto_rotate = True
        eng = pi.ImpositionEngine([], cfg)
        cw, ch = eng.cell_px()
        w_pt, h_pt = pi.pdf_page_size(self.pdf, 2)
        self.assertGreater(w_pt, h_pt)
        self.assertEqual(pi.pdf_render_box(w_pt, h_pt, cw, ch, True), (ch, cw))
        img = pi.open_source(self.pdf, cw, ch, page=2, auto_rotate=True)
        # Renderizada já deitada, na caixa girada (ch × cw): um lado encosta nela
        # e nenhum a ultrapassa — depois do giro cabe na célula sem crescer.
        self.assertLessEqual(img.width, ch + 1)
        self.assertLessEqual(img.height, cw + 1)
        self.assertTrue(abs(img.width - ch) <= 1 or abs(img.height - cw) <= 1)

    def test_fundo_branco_opaco(self):
        img = pi.rasterize_pdf(self.pdf, 0, 200, 280)
        self.assertEqual(img.getpixel((img.width // 2, img.height // 2))[3], 255)


class TkAttributeCollisionTests(unittest.TestCase):
    """REGRESSÃO do bloqueador da 1.1.0 (FIX-003).

    `GridPreview.__init__` fazia `self._w, self._h = w, h`. Em `tkinter.Misc`,
    `_w` guarda o pathname Tcl do widget ('.!canvas'); sobrescrever com um int
    faz TODA chamada ao Tk virar `70 delete` → «invalid command name "70"», e o
    app não abre.

    O stub de tkinter da suíte não define `_w`, então nenhum teste de
    comportamento pegaria isso. A checagem aqui é sobre o CÓDIGO-FONTE: nenhuma
    classe que herda de widget Tk pode escrever em nome reservado do Tkinter.
    É a única forma headless de guardar esta lição.
    """

    # Nomes que tkinter.Misc usa internamente e que não podem ser sobrescritos.
    RESERVADOS = {"_w", "_name", "_tclCommands", "master", "tk", "children"}

    def setUp(self):
        self.src = (Path(__file__).resolve().parent.parent / "print_imposer.py"
                    ).read_text(encoding="utf-8")
        self.tree = ast.parse(self.src)

    def _classes_de_widget(self):
        """Classes que herdam de algo do tkinter/customtkinter."""
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                nome = ast.unparse(base)
                if nome.startswith(("tk.", "ctk.")):
                    yield node
                    break

    def test_nenhuma_classe_de_widget_sobrescreve_nome_reservado(self):
        infracoes = []
        for cls in self._classes_de_widget():
            for node in ast.walk(cls):
                alvos = []
                if isinstance(node, ast.Assign):
                    alvos = node.targets
                elif isinstance(node, ast.AnnAssign):
                    alvos = [node.target]
                for alvo in alvos:
                    for elt in (alvo.elts if isinstance(alvo, ast.Tuple) else [alvo]):
                        if (isinstance(elt, ast.Attribute)
                                and isinstance(elt.value, ast.Name)
                                and elt.value.id == "self"
                                and elt.attr in self.RESERVADOS):
                            infracoes.append(f"{cls.name}: self.{elt.attr}")
        self.assertEqual(infracoes, [],
                         f"nome reservado do Tkinter sobrescrito: {infracoes}")

    def test_gridpreview_usa_prefixo_proprio(self):
        self.assertIn("self._box_w", self.src)
        self.assertNotIn("self._w, self._h", self.src)


class DpiRaceTests(unittest.TestCase):
    """REGRESSÃO da corrida de DPI entre preview e geração (FIX-004).

    `compose_page` mutava `cfg.dpi` e restaurava num `finally`. Correto em uso
    sequencial — mas preview e geração rodam em THREADS distintas sobre o mesmo
    `LayoutConfig`. Gerar com o preview em voo produzia a folha em 72 DPI, sem
    aviso nenhum. Agora o DPI é parâmetro, e nada é mutado.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.img = make_image(self.tmp / "src.png", 600, 840)
        self.cfg = pi.LayoutConfig()
        self.cfg.dpi = 150
        self.cfg.cols = self.cfg.rows = 2
        self.cfg.output_dir = str(self.tmp)
        e = pi.ImageEntry(self.img); e.quantity = 4
        self.eng = pi.ImpositionEngine([e], self.cfg)

    def test_compose_nao_muta_o_dpi_do_config(self):
        self.eng.compose_page(0, self.eng._expand(), override_dpi=72)
        self.assertEqual(self.cfg.dpi, 150)

    def test_preview_nao_muta_o_dpi_do_config(self):
        self.eng.preview_page(0)
        self.assertEqual(self.cfg.dpi, 150)

    def test_geracao_mantem_o_dpi_com_preview_concorrente(self):
        """O cenário real: mexo numa opção (dispara preview) e clico em Gerar."""
        parar = threading.Event()
        erros = []

        def martelar_preview():
            while not parar.is_set():
                try:
                    self.eng.preview_page(0)
                except Exception as exc:      # pragma: no cover
                    erros.append(exc)
                    return

        t = threading.Thread(target=martelar_preview, daemon=True)
        t.start()
        try:
            esperado = self.eng._page_px()          # A4 @ 150 DPI
            for _ in range(6):
                pagina = self.eng.compose_page(0, self.eng._expand())
                self.assertEqual(pagina.size, esperado,
                                 "folha saiu no DPI do preview — corrida de volta")
        finally:
            parar.set(); t.join(timeout=5)
        self.assertEqual(erros, [])
        self.assertEqual(self.cfg.dpi, 150)

    def test_dpi_explicito_muda_so_aquela_folha(self):
        p72  = self.eng.compose_page(0, self.eng._expand(), override_dpi=72)
        p150 = self.eng.compose_page(0, self.eng._expand())
        self.assertLess(p72.size[0], p150.size[0])
        self.assertEqual(self.cfg.dpi, 150)


class WorkAreaTests(unittest.TestCase):
    """A janela precisa caber na área ÚTIL, não na tela física (FIX-005).

    Só dá para checar o contrato do código headless; o posicionamento real
    exige abrir a janela (item 1 do smoke test).
    """

    def setUp(self):
        self.src = (Path(__file__).resolve().parent.parent / "print_imposer.py"
                    ).read_text(encoding="utf-8")

    def test_existe_helper_de_area_util(self):
        self.assertIn("def _work_area", self.src)
        self.assertIn("SPI_GETWORKAREA", self.src)

    def test_setup_geometry_usa_area_util_e_nao_a_tela_fisica(self):
        i = self.src.index("def _setup_geometry")
        j = self.src.index("def _place_sashes")
        corpo = self.src[i:j]
        self.assertIn("_work_area()", corpo)
        self.assertNotIn("winfo_screenheight()", corpo)


class SectionsOpenTests(unittest.TestCase):
    """Contrato do `sections_open` no settings.json (SPEC-F3-UI §9)."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._orig = (pi.SettingsStore.DIR, pi.SettingsStore.SETTINGS)
        pi.SettingsStore.DIR = Path(self._dir.name)
        pi.SettingsStore.SETTINGS = Path(self._dir.name) / "settings.json"

    def tearDown(self):
        pi.SettingsStore.DIR, pi.SettingsStore.SETTINGS = self._orig
        self._dir.cleanup()

    def test_roundtrip(self):
        estado = {"papel": True, "ajuste": False, "margens": True,
                  "corte": False, "saida": False}
        self.assertTrue(pi.SettingsStore.save_settings({"sections_open": estado}))
        lido = pi.SettingsStore.load_settings().get("sections_open")
        self.assertEqual(pi.normalize_sections_open(lido), estado)

    def test_arquivo_da_1_1_sem_a_chave_cai_no_padrao(self):
        pi.SettingsStore.save_settings({"config": {}, "geometry": "1180x820+0+0"})
        lido = pi.SettingsStore.load_settings().get("sections_open")
        estado = pi.normalize_sections_open(lido)
        self.assertEqual(estado, pi.SECTION_DEFAULTS)
        self.assertEqual([k for k, v in estado.items() if v], ["saida"])

    def test_chave_desconhecida_e_ignorada(self):
        estado = pi.normalize_sections_open({"papel": True, "inexistente": True})
        self.assertNotIn("inexistente", estado)
        self.assertTrue(estado["papel"])
        self.assertEqual(set(estado), set(pi.SECTION_DEFAULTS))

    def test_valor_que_nao_e_booleano_e_ignorado(self):
        estado = pi.normalize_sections_open({"papel": "sim", "saida": 0})
        self.assertEqual(estado, pi.SECTION_DEFAULTS)

    def test_lixo_no_lugar_do_dicionario_cai_no_padrao(self):
        for lixo in (None, [], "x", 3):
            self.assertEqual(pi.normalize_sections_open(lixo), pi.SECTION_DEFAULTS)


class MenuAndDialogTests(unittest.TestCase):
    """Menubar e diálogo do atalho. Sem Tk real: a checagem é pelo código-fonte,
    como nos testes AST acima. O comportamento de verdade fica no /smoke."""

    ESPERADOS = {
        "Arquivo": ["Adicionar arquivos…", "Adicionar pasta…", "Limpar lista",
                    "Gerar arquivos", "Abrir pasta de saída", "Sair"],
        "Opções":  ["Presets", "Salvar atual…", "Excluir…", "Criar atalho…",
                    "Restaurar configurações padrão"],
        "Ajuda":   ["Guia rápido: da arte à impressão", "Sobre o PrintImposer"],
    }

    def setUp(self):
        self.src = (Path(__file__).resolve().parent.parent / "print_imposer.py"
                    ).read_text(encoding="utf-8")
        self.tree = ast.parse(self.src)

    def _metodo(self, nome):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == nome:
                return node
        self.fail(f"método {nome} não existe")

    def _chaves_de_rotulo_usadas(self, *metodos):
        """Chaves `L["..."]` lidas pelos métodos que montam os menus."""
        usadas = set()
        for nome in metodos:
            for node in ast.walk(self._metodo(nome)):
                if (isinstance(node, ast.Subscript)
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "L"
                        and isinstance(node.slice, ast.Constant)):
                    usadas.add(node.slice.value)
        return usadas

    def test_titulos_do_menubar(self):
        self.assertEqual(pi.MENU_TITLES, tuple(self.ESPERADOS))

    def test_rotulos_da_spec_existem(self):
        todos = set(pi.MENU_LABELS.values())
        for menu, rotulos in self.ESPERADOS.items():
            for r in rotulos:
                self.assertIn(r, todos, f"{menu}: falta «{r}»")

    def test_todo_rotulo_esta_ligado_a_um_menu(self):
        usadas = self._chaves_de_rotulo_usadas("_build_menus", "_rebuild_presets_menu")
        self.assertEqual(usadas, set(pi.MENU_LABELS))

    def test_submenu_de_presets_e_reconstruido_a_cada_abertura(self):
        """Era o bug de 1.1.x: a lista só atualizava ao reabrir o app."""
        popup = ast.unparse(self._metodo("_popup_menu"))
        self.assertIn("_rebuild_presets_menu", popup)

    def test_atalho_abre_na_pasta_pai_da_raiz(self):
        raiz = Path(pi.__file__).resolve().parent
        self.assertEqual(Path(pi.shortcut_initial_dir()), raiz.parent)

    def test_make_bat_usa_a_pasta_pai_e_nao_a_area_de_trabalho(self):
        corpo = ast.unparse(self._metodo("_make_bat"))
        self.assertIn("shortcut_initial_dir()", corpo)
        self.assertNotIn("Desktop", corpo)

    def test_guia_rapido_vem_de_uma_constante_unica(self):
        self.assertIn("Figma", pi.QUICK_GUIDE)
        self.assertIn("QUICK_GUIDE", ast.unparse(self._metodo("_show_guide")))

    def test_secao_recolhivel_fecha_com_grid_remove_e_nao_destroy(self):
        cls = next(n for n in ast.walk(self.tree)
                   if isinstance(n, ast.ClassDef) and n.name == "CollapsibleSection")
        corpo = ast.unparse(cls)
        self.assertIn("grid_remove()", corpo)
        self.assertNotIn(".destroy(", corpo)

    def test_zona_inferior_respeita_o_teto_de_altura(self):
        self.assertLessEqual(pi.ConfigPanel.BOTTOM_H, 84)

    def test_versao(self):
        self.assertEqual(pi.VERSION, "1.6.0")


class StartupErrorTests(unittest.TestCase):
    """1.4.1: erro ao abrir deixa rastro e avisa, mesmo via pythonw (sem console)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.exc = None
        try:
            raise RuntimeError("falha de teste")
        except RuntimeError as e:
            self.exc = e

    def test_grava_log_com_os_campos_e_chama_o_notificador(self):
        avisos = []
        with mock.patch.object(pi.SettingsStore, "DIR", self.tmp / "dot"):
            log = pi.report_startup_error(self.exc, notify=lambda r, p: avisos.append((r, p)))
        self.assertEqual(log, self.tmp / "dot" / "last_error.log")
        texto = log.read_text(encoding="utf-8")
        for campo in ("Data/hora:", f"Versão: {pi.VERSION}", "Python:",
                      "Executável:", "Traceback", "RuntimeError: falha de teste"):
            self.assertIn(campo, texto)
        self.assertEqual(avisos, [("RuntimeError: falha de teste", log)])

    def test_cai_na_pasta_temporaria_quando_a_pasta_nao_pode_ser_criada(self):
        bloqueio = self.tmp / "arquivo"
        bloqueio.write_text("x")          # mkdir dentro de um arquivo falha
        temp = self.tmp / "temp"; temp.mkdir()
        with mock.patch.object(pi.SettingsStore, "DIR", bloqueio / "dot"), \
                mock.patch.object(pi.tempfile, "gettempdir", return_value=str(temp)):
            log = pi.report_startup_error(self.exc, notify=lambda r, p: None)
        self.assertEqual(log, temp / "last_error.log")
        self.assertTrue(log.exists())

    def test_notificador_que_falha_nao_vira_outro_erro(self):
        def quebra(r, p):
            raise OSError("sem janela")
        with mock.patch.object(pi.SettingsStore, "DIR", self.tmp / "dot"):
            log = pi.report_startup_error(self.exc, notify=quebra)
        self.assertTrue(log.exists())

    def test_main_envolve_o_app_num_try_except_exception(self):
        src = (Path(__file__).resolve().parent.parent / "print_imposer.py"
               ).read_text(encoding="utf-8")
        main = next(n for n in ast.walk(ast.parse(src))
                    if isinstance(n, ast.FunctionDef) and n.name == "main")
        tries = [n for n in ast.walk(main) if isinstance(n, ast.Try)]
        self.assertEqual(len(tries), 1)
        self.assertEqual([ast.unparse(h.type) for h in tries[0].handlers], ["Exception"])
        self.assertIn("PrintImposerApp", ast.unparse(tries[0]))
        self.assertIn("mainloop", ast.unparse(tries[0]))


class SecondDestNoticeTests(unittest.TestCase):
    """1.4.1: aviso «Também grava em» (pura; a UI só desenha o resultado)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = pi.LayoutConfig()

    def test_desligado_ou_vazio_nao_mostra(self):
        self.cfg.output_dir2 = str(self.tmp)
        self.assertFalse(pi.second_dest_notice(self.cfg)[0])
        self.cfg.output_dir2_on = True
        self.cfg.output_dir2 = "   "
        self.assertFalse(pi.second_dest_notice(self.cfg)[0])

    def test_ligado_e_existente_fora_do_temp_e_normal(self):
        self.cfg.output_dir2_on = True
        self.cfg.output_dir2 = str(self.tmp)
        elsewhere = self.tmp / "fakeos_temp"; elsewhere.mkdir()
        with mock.patch.object(pi.tempfile, "gettempdir", return_value=str(elsewhere)):
            mostrar, texto, nivel = pi.second_dest_notice(self.cfg)
        self.assertTrue(mostrar)
        self.assertEqual(nivel, "normal")
        self.assertEqual(texto, f"Também grava em: {self.tmp}")

    def test_inexistente_e_ambar(self):
        self.cfg.output_dir2_on = True
        self.cfg.output_dir2 = str(self.tmp / "nao" / "existe")
        self.assertEqual(pi.second_dest_notice(self.cfg)[2], "warn")

    def test_dentro_do_temp_e_ambar(self):
        self.cfg.output_dir2_on = True
        self.cfg.output_dir2 = str(self.tmp)
        with mock.patch.object(pi.tempfile, "gettempdir",
                               return_value=str(self.tmp.parent)):
            self.assertEqual(pi.second_dest_notice(self.cfg)[2], "warn")

    def test_encurta_no_meio_passando_do_limite(self):
        longo = "C:\\" + "a" * 40 + "\\" + "b" * 40 + "\pasta_final"
        curto = pi.shorten_middle(longo)
        self.assertEqual(len(curto), pi.DEST_NOTICE_MAX)
        self.assertIn("…", curto)
        self.assertTrue(curto.endswith("pasta_final"))
        self.assertEqual(pi.shorten_middle("curto"), "curto")


class FrozenGenerationTests(unittest.TestCase):
    """1.4.1: mexer na tela durante a geração não mistura folhas."""

    def test_geracao_ignora_mudancas_feitas_no_meio(self):
        tmp = Path(tempfile.mkdtemp())
        img = make_image(tmp / "src.png", 300, 420)
        cfg = pi.LayoutConfig()
        cfg.dpi = 100; cfg.cols = cfg.rows = 1
        cfg.output_dir = str(tmp)
        e = pi.ImageEntry(img); e.quantity = 12
        entries = [e]
        esperado = pi.ImpositionEngine(entries, cfg)._page_px()   # A4 @ 100 DPI

        snap_entries, snap_cfg = pi.snapshot_for_generation(entries, cfg)
        self.assertIsNot(snap_cfg, cfg)
        self.assertIsNot(snap_entries, entries)
        self.assertIsNot(snap_entries[0], e)

        primeira, mexeu = threading.Event(), threading.Event()

        def mexer():
            primeira.wait(5)
            cfg.paper_key = "A5"; cfg.paper_w_mm, cfg.paper_h_mm = 148.0, 210.0
            cfg.cols = 2
            e.quantity = 1
            entries.clear()
            mexeu.set()

        def progresso(done, total):
            if done == 1:
                primeira.set()
                mexeu.wait(5)

        t = threading.Thread(target=mexer, daemon=True); t.start()
        paginas = pi.ImpositionEngine(snap_entries, snap_cfg).generate_all(progresso)
        t.join(timeout=5)

        self.assertEqual(len(paginas), 12)
        self.assertEqual({p.size for p in paginas}, {esperado})
        # o cfg vivo guarda as mudanças; o preview as enxerga
        self.assertEqual(cfg.paper_key, "A5")
        self.assertEqual(cfg.cols, 2)
        self.assertEqual(entries, [])

    def test_start_generate_congela_antes_da_thread(self):
        src = (Path(__file__).resolve().parent.parent / "print_imposer.py"
               ).read_text(encoding="utf-8")
        fn = next(n for n in ast.walk(ast.parse(src))
                  if isinstance(n, ast.FunctionDef) and n.name == "_start_generate")
        corpo = ast.unparse(fn)
        self.assertLess(corpo.index("snapshot_for_generation"), corpo.index("Thread("))
        self.assertIn("args=(entries, cfg)", corpo)
        worker = next(n for n in ast.walk(ast.parse(src))
                      if isinstance(n, ast.FunctionDef) and n.name == "_generate_worker")
        self.assertNotIn("self.cfg", ast.unparse(worker))
        self.assertNotIn("self.img_panel", ast.unparse(worker))


class SvgFinalOrientationTests(unittest.TestCase):
    """SVG rasterizado na orientação final e respeitando o modo de ajuste (wo0009).

    Um stub registra a caixa/escala pedidas ao back-end: roda sem cairosvg/svglib.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        # Arte DEITADA: 300×200 (proporção 3:2).
        self.svg = self.tmp / "deitado.svg"
        self.svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" '
            'viewBox="0 0 300 200"><rect width="300" height="200"/></svg>',
            encoding="utf-8")
        self.calls = []

        def fake_render(path, out_w, out_h):
            self.calls.append((out_w, out_h))
            return Image.new("RGBA", (out_w, out_h), (10, 10, 10, 255))

        p = mock.patch.object(pi, "_svg_backend_render", fake_render)
        p.start()
        self.addCleanup(p.stop)

    def _engine(self, **cfg_kw):
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = 2, 2, 72
        cfg.paper_w_mm, cfg.paper_h_mm = 100.0, 200.0     # célula em pé
        for k, v in cfg_kw.items():
            setattr(cfg, k, v)
        return pi.ImpositionEngine([pi.ImageEntry(str(self.svg))], cfg)

    def test_proporcao_vem_de_width_height_viewbox_e_unidades(self):
        def size(markup):
            f = self.tmp / "t.svg"
            f.write_text(markup, encoding="utf-8")
            os.utime(f, (f.stat().st_atime, f.stat().st_mtime + len(markup)))  # fura o cache
            return pi.svg_intrinsic_size(str(f))

        ns = 'xmlns="http://www.w3.org/2000/svg"'
        self.assertEqual(size(f'<svg {ns} width="40" height="20"/>'), (40.0, 20.0))
        w, h = size(f'<svg {ns} width="210mm" height="297mm"/>')
        self.assertAlmostEqual(w / h, 210 / 297, places=4)
        w, h = size(f'<svg {ns} width="1in" height="96px"/>')
        self.assertAlmostEqual(w / h, 1.0, places=4)
        self.assertEqual(size(f'<svg {ns} viewBox="0 0 50 80"/>'), (50.0, 80.0))
        # width em % não é medida: cai no viewBox
        self.assertEqual(size(f'<svg {ns} width="100%" height="100%" viewBox="0 0 30 90"/>'),
                         (30.0, 90.0))

    def test_sem_medidas_mede_pelo_backend(self):
        f = self.tmp / "nu.svg"
        f.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        with mock.patch.object(pi, "_svg_backend_size", lambda p: (64.0, 32.0)):
            self.assertEqual(pi.svg_intrinsic_size(str(f)), (64.0, 32.0))

    def test_cache_por_caminho_e_mtime(self):
        pi.svg_intrinsic_size(str(self.svg))
        with mock.patch.object(pi, "_svg_backend_size",
                               side_effect=AssertionError("não devia medir de novo")):
            self.assertEqual(pi.svg_intrinsic_size(str(self.svg)), (300.0, 200.0))

    def test_auto_rotate_pede_caixa_girada(self):
        eng = self._engine(auto_rotate=True)
        cw, ch = eng.cell_px(72)
        self.assertLess(cw, ch)
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        out_w, out_h = self.calls[-1]
        # Arte deitada: renderizada deitada, na caixa (ch, cw); depois do giro cabe sem crescer.
        self.assertLessEqual(out_w, ch + 1)
        self.assertLessEqual(out_h, cw + 1)
        self.assertTrue(abs(out_w - ch) <= 1 or abs(out_h - cw) <= 1)

    def test_sem_auto_rotate_usa_a_propria_celula(self):
        eng = self._engine(auto_rotate=False)
        cw, ch = eng.cell_px(72)
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        out_w, out_h = self.calls[-1]
        self.assertLessEqual(out_w, cw + 1)
        self.assertLessEqual(out_h, ch + 1)

    def test_preencher_cobre_a_caixa_sem_ampliar(self):
        eng = self._engine(auto_rotate=True, fit_mode="fill")
        cw, ch = eng.cell_px(72)
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        out_w, out_h = self.calls[-1]
        # Caixa girada (ch, cw): a escala que COBRE deixa os dois lados >= a caixa...
        self.assertGreaterEqual(out_w, ch - 1)
        self.assertGreaterEqual(out_h, cw - 1)
        # ...e, depois do giro, o `_place_image` cobre a célula com fator ~1 (só recorta).
        factor = max(cw / out_h, ch / out_w)
        self.assertAlmostEqual(factor, 1.0, delta=0.02)

    def test_esticar_entrega_o_tamanho_da_caixa(self):
        img = pi.rasterize_svg(str(self.svg), 120, 400, "stretch")
        self.assertEqual(img.size, (120, 400))
        self.assertGreaterEqual(self.calls[-1][1], 400 - 1)     # renderizou cobrindo

    def test_miniatura_nao_quebra(self):
        e = pi.ImageEntry(str(self.svg))
        self.assertIsNotNone(e.pil_thumb)


def make_pdf_with_images(path: str, size_pt, images):
    """PDF de 1 página com imagens em posições dadas pelo teste.

    `images`: [(px_w, px_h, x, y, w_pt, h_pt)] — pypdfium2 monta o objeto de imagem.
    """
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument.new()
    page = doc.new_page(*size_pt)
    for px_w, px_h, x, y, w_pt, h_pt in images:
        obj = pdfium.PdfImage.new(doc)
        obj.set_bitmap(pdfium.PdfBitmap.from_pil(
            Image.new("RGB", (px_w, px_h), (200, 30, 30)).convert("RGBA")))
        obj.set_matrix(pdfium.PdfMatrix().scale(w_pt, h_pt).translate(x, y))
        page.insert_obj(obj)
    page.gen_content()
    doc.save(path)


@unittest.skipUnless(pi.PDF_OK, "sem pypdfium2")
class PdfInnerImageGuardTests(unittest.TestCase):
    """A guarda de qualidade olha as imagens DENTRO do PDF (wo0009)."""

    A4 = (595.0, 842.0)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _report(self, pdf, cols=1, rows=1, dpi=150, **cfg_kw):
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = cols, rows, dpi
        for k, v in cfg_kw.items():
            setattr(cfg, k, v)
        return pi.ImpositionEngine([pi.ImageEntry(pdf)], cfg).quality_report()

    def _pdf(self, name, size, images):
        path = str(self.tmp / name)
        make_pdf_with_images(path, size, images)
        return path

    def test_imagem_pequena_dentro_do_pdf_da_selo_vermelho(self):
        pdf = self._pdf("pequena.pdf", self.A4, [(300, 420, 0, 0, 595, 842)])
        q = self._report(pdf)       # célula A4 a 150 dpi = 1240×1754
        escala = 1754 / 842
        # como no raster: vale o pior dos dois eixos (a imagem 300×420 não é 595:842)
        esperado = min(300 / (595 * escala), 420 / (842 * escala))
        self.assertAlmostEqual(q["ratio"], esperado, places=4)
        self.assertEqual(q["level"], "bad")
        self.assertEqual(q["worst"], "pequena.pdf · p. 1 (imagem interna)")

    def test_imagem_grande_da_selo_verde(self):
        pdf = self._pdf("grande.pdf", self.A4, [(3000, 4200, 0, 0, 595, 842)])
        self.assertEqual(self._report(pdf)["level"], "ok")

    def test_logo_abaixo_de_10_por_cento_e_ignorado(self):
        pdf = self._pdf("logo.pdf", self.A4, [(40, 40, 20, 20, 60, 60)])
        self.assertEqual(self._report(pdf)["level"], "none")

    def test_pior_imagem_da_pagina_manda(self):
        pdf = self._pdf("duas.pdf", self.A4, [(3000, 2100, 0, 421, 595, 421),
                                               (100, 70, 0, 0, 595, 421)])
        q = self._report(pdf)
        self.assertEqual(q["level"], "bad")
        escala = 1754 / 842
        self.assertAlmostEqual(q["ratio"], min(100 / (595 * escala),
                                               70 / (421 * escala)), places=4)

    def test_escala_da_celula_inclui_auto_rotate(self):
        """Página deitada em célula em pé: a escala é a da caixa GIRADA. Errar isso
        dá selo verde para imagem pequena."""
        pdf = self._pdf("deitada.pdf", (842.0, 595.0), [(1000, 700, 0, 0, 842, 595)])
        # Folha A4 a 300 dpi, grade 2×2: célula 1240×1754 (em pé).
        com = self._report(pdf, cols=2, rows=2, dpi=300, auto_rotate=True)
        esc_com = min(1754 / 842, 1240 / 595)
        self.assertAlmostEqual(com["ratio"], min(1000 / (842 * esc_com),
                                                 700 / (595 * esc_com)), places=4)
        sem = self._report(pdf, cols=2, rows=2, dpi=300, auto_rotate=False)
        esc_sem = min(1240 / 842, 1754 / 595)
        self.assertAlmostEqual(sem["ratio"], min(1000 / (842 * esc_sem),
                                                 700 / (595 * esc_sem)), places=4)

    def test_modo_preencher_usa_a_escala_que_cobre(self):
        pdf = self._pdf("fill.pdf", self.A4, [(1000, 1400, 0, 0, 595, 842)])
        fit = self._report(pdf, cols=2, rows=2, dpi=300, fit_mode="fit")
        fill = self._report(pdf, cols=2, rows=2, dpi=300, fit_mode="fill")
        self.assertLessEqual(fill["ratio"], fit["ratio"])

    def test_pdf_ilegivel_nao_derruba_a_guarda(self):
        ruim = self.tmp / "ruim.pdf"
        ruim.write_text("isto nao e um pdf")
        raster = make_image(self.tmp / "p.png", 300, 420)
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = 1, 1, 300
        q = pi.ImpositionEngine([pi.ImageEntry(str(ruim)), pi.ImageEntry(raster)],
                                cfg).quality_report()
        self.assertEqual(q["worst"], "p.png")      # o raster segue valendo
        self.assertEqual(q["level"], "bad")

    def test_vetor_puro_continua_fora(self):
        pdf = self._pdf("vazio.pdf", self.A4, [])
        self.assertEqual(self._report(pdf)["level"], "none")


class SemPdfiumGuardTests(unittest.TestCase):
    def test_sem_backend_pdf_nada_muda(self):
        tmp = Path(tempfile.mkdtemp())
        pdf = tmp / "x.pdf"
        pdf.write_bytes(b"%PDF-1.4 stub")
        cfg = pi.LayoutConfig()
        with mock.patch.object(pi, "PDF_OK", False):
            q = pi.ImpositionEngine([pi.ImageEntry(str(pdf))], cfg).quality_report()
        self.assertEqual(q["level"], "none")


class WebpAvifOutputTests(unittest.TestCase):
    """Saída WebP e AVIF, para compartilhar (wo0009)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = make_image(self.tmp / "a.png", 600, 800)
        # Folha com ruído (reprodutível): o gradiente liso comprime a nada sem perda.
        import random
        rng = random.Random(7)
        self.page = Image.frombytes("RGB", (400, 560), rng.randbytes(400 * 560 * 3))

    def _save(self, fmt, **cfg_kw):
        self._n = getattr(self, "_n", 0) + 1       # pasta nova a cada gravação (sem sufixo _2)
        cfg = pi.LayoutConfig()
        cfg.output_format = fmt
        cfg.output_dir = str(self.tmp / f"{fmt.lower()}{self._n}")
        for k, v in cfg_kw.items():
            setattr(cfg, k, v)
        eng = pi.ImpositionEngine([pi.ImageEntry(self.src)], cfg)
        return eng.save([self.page, self.page])

    def test_lista_de_formatos_e_sondagem(self):
        self.assertEqual(pi.OUT_FORMATS[:4], ["PNG", "PDF", "JPEG", "TIFF"])
        self.assertEqual(pi.build_out_formats(lambda f: True)[-2:], ["WEBP", "AVIF"])
        # AVIF sem gravação (só leitura): fica fora da lista; WEBP continua.
        self.assertEqual(pi.build_out_formats(lambda f: f != "AVIF")[4:], ["WEBP"])
        self.assertEqual(pi.build_out_formats(lambda f: False), ["PNG", "PDF", "JPEG", "TIFF"])

    def test_sondagem_grava_de_verdade(self):
        """`features.check` verdadeiro não basta: a sonda faz um save real (FIX-002)."""
        with mock.patch.object(Image.Image, "save", side_effect=OSError("só leitura")):
            self.assertFalse(pi._probe_can_save("AVIF"))

    def test_cada_formato_grava_reabre_e_tem_o_tamanho_da_folha(self):
        casos = [("WEBP", {"webp_compression": "lossless"}),
                 ("WEBP", {"webp_compression": "lossy", "jpeg_quality": 80}),
                 ("AVIF", {"jpeg_quality": 80})]
        for fmt, kw in casos:
            if fmt not in pi.OUT_FORMATS:
                continue
            with self.subTest(fmt=fmt, kw=kw):
                saved = self._save(fmt, **kw)
                self.assertEqual(len(saved), 2)
                self.assertTrue(saved[0].endswith(f"folha_001.{fmt.lower()}"))
                with Image.open(saved[0]) as im:
                    self.assertEqual(im.size, self.page.size)

    def test_webp_sem_perda_reabre_identico(self):
        saved = self._save("WEBP", webp_compression="lossless")
        with Image.open(saved[0]) as im:
            self.assertEqual(im.convert("RGB").tobytes(), self.page.tobytes())

    def test_webp_com_perda_pesa_menos_que_sem_perda(self):
        sem = os.path.getsize(self._save("WEBP", webp_compression="lossless")[0])
        com = os.path.getsize(self._save("WEBP", webp_compression="lossy",
                                         jpeg_quality=60)[0])
        self.assertLess(com, sem)

    def test_preset_ida_e_volta_com_webp_compression(self):
        cfg = pi.LayoutConfig()
        cfg.output_format, cfg.webp_compression = "WEBP", "lossy"
        self.assertIn("webp_compression", pi.LayoutConfig.PRESET_FIELDS)
        novo = pi.LayoutConfig()
        novo.from_dict(cfg.preset_dict())
        self.assertEqual((novo.output_format, novo.webp_compression), ("WEBP", "lossy"))

    def test_valores_invalidos_voltam_ao_padrao(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"webp_compression": "xyz", "output_format": "BMP"})
        self.assertEqual((cfg.webp_compression, cfg.output_format), ("lossless", "PNG"))

    def test_avif_de_preset_some_se_a_maquina_nao_grava(self):
        with mock.patch.object(pi, "OUT_FORMATS", ["PNG", "PDF", "JPEG", "TIFF", "WEBP"]):
            cfg = pi.LayoutConfig()
            cfg.from_dict({"output_format": "AVIF"})
            self.assertEqual(cfg.output_format, "PNG")


def cut_cfg(**kw):
    """Config de teste: A4, 2×2, margem 10 mm, espaçamento 0 — o caso de referência do corte."""
    cfg = pi.LayoutConfig()
    cfg.cols = cfg.rows = 2
    cfg.margin_outer_mm = 10.0
    cfg.auto_rotate = False
    for k, v in kw.items():
        setattr(cfg, k, v)
    return cfg


def _overlap(a, b):
    """Interseção de área positiva entre dois retângulos (x0, y0, x1, y1)."""
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


class SheetGeometryTests(unittest.TestCase):
    """F4 etapa 4: geometria de corte, sangria e marcas, em mm, sem Tk nem Pillow."""

    def test_marcas_com_celulas_coladas(self):
        geo = pi.sheet_geometry(cut_cfg(cut_guide="marks"))
        self.assertEqual(len(geo.cut_x), 3)
        self.assertEqual(len(geo.cut_y), 3)
        self.assertEqual(len(geo.marks), 2 * (3 + 3))
        self.assertEqual([round(v, 3) for v in geo.cut_x], [10.0, 105.0, 200.0])

    def test_marcas_com_espacamento(self):
        geo = pi.sheet_geometry(cut_cfg(cut_guide="marks", margin_between_x_mm=6.0,
                                        margin_between_y_mm=6.0))
        self.assertEqual((len(geo.cut_x), len(geo.cut_y)), (4, 4))
        self.assertEqual(len(geo.marks), 16)

    def test_sem_marcas_fora_da_guia_marcas(self):
        for guide in ("none", "lines"):
            self.assertEqual(pi.sheet_geometry(cut_cfg(cut_guide=guide)).marks, [])

    def test_marca_comeca_na_distancia_e_tem_o_comprimento(self):
        geo = pi.sheet_geometry(cut_cfg(cut_guide="marks"))
        gx0, gy0, gx1, gy1 = geo.grid
        top = [m for m in geo.marks if m[0] == m[2] and m[3] <= gy0]
        self.assertEqual(len(top), 3)
        for x1, y1, x2, y2 in top:
            self.assertAlmostEqual(gy0 - y2, 3.0)         # distância padrão
            self.assertAlmostEqual(y2 - y1, 4.0)          # comprimento padrão

    def test_distancia_efetiva_nunca_menor_que_a_sangria(self):
        geo = pi.sheet_geometry(cut_cfg(cut_guide="marks", bleed_mm=5.0,
                                        mark_offset_mm=3.0, margin_outer_mm=15.0))
        self.assertEqual(geo.mark_offset, 5.0)
        gy0 = geo.grid[1]
        top = [m for m in geo.marks if m[0] == m[2] and m[3] <= gy0]
        self.assertAlmostEqual(gy0 - top[0][3], 5.0)

    def test_margem_curta_avisa_com_o_minimo(self):
        geo = pi.sheet_geometry(cut_cfg(cut_guide="marks", margin_outer_mm=5.0))
        self.assertIn(("warn", "A margem externa precisa de pelo menos 7 mm "
                               "para as marcas."), geo.warnings)

    def test_margem_suficiente_nao_avisa(self):
        self.assertEqual(pi.sheet_geometry(cut_cfg(cut_guide="marks")).warnings, [])

    def test_margem_curta_so_avisa_com_marcas(self):
        self.assertEqual(
            pi.sheet_geometry(cut_cfg(cut_guide="none", margin_outer_mm=0.0)).warnings, [])

    def test_sangria_maior_que_o_vao_avisa_o_que_coube(self):
        geo = pi.sheet_geometry(cut_cfg(bleed_mm=3.0, margin_between_x_mm=4.0,
                                        margin_between_y_mm=4.0))
        self.assertIn(("warn", "Espaçamento entre colunas menor que 2× a sangria: "
                               "entre as colunas coube 2 mm."), geo.warnings)
        self.assertIn(("warn", "Espaçamento entre linhas menor que 2× a sangria: "
                               "entre as linhas coube 2 mm."), geo.warnings)

    def test_sangria_com_celulas_coladas_so_cabe_na_borda_externa(self):
        geo = pi.sheet_geometry(cut_cfg(bleed_mm=3.0))
        self.assertEqual(geo.bleed_sides[0], (3.0, 3.0, 0.0, 0.0))     # canto sup. esq.
        self.assertEqual(geo.bleed_sides[3], (0.0, 0.0, 3.0, 3.0))     # canto inf. dir.
        self.assertTrue(any(lvl == "warn" for lvl, _ in geo.warnings))

    def test_sangria_com_espaco_de_sobra_vai_inteira(self):
        geo = pi.sheet_geometry(cut_cfg(bleed_mm=3.0, margin_between_x_mm=6.0,
                                        margin_between_y_mm=6.0))
        for sides in geo.bleed_sides:
            self.assertEqual(sides, (3.0, 3.0, 3.0, 3.0))
        self.assertEqual(geo.warnings, [])

    def test_sangria_limitada_pela_margem_externa(self):
        geo = pi.sheet_geometry(cut_cfg(bleed_mm=3.0, margin_outer_mm=1.0,
                                        margin_between_x_mm=6.0, margin_between_y_mm=6.0))
        self.assertEqual(geo.bleed_sides[0][:2], (1.0, 1.0))

    def test_sem_sangria_o_retangulo_de_sangria_e_o_de_corte(self):
        geo = pi.sheet_geometry(cut_cfg())
        self.assertEqual(geo.bleeds, geo.cells)

    def test_linhas_com_sangria_avisa_em_cinza(self):
        geo = pi.sheet_geometry(cut_cfg(cut_guide="lines", bleed_mm=3.0,
                                        margin_between_x_mm=6.0, margin_between_y_mm=6.0))
        self.assertEqual(geo.warnings, [("info", "Com sangria, use marcas de canto: "
                                                 "as linhas riscam a sangria.")])

    def test_marca_nunca_intersecta_corte_nem_sangria(self):
        casos = [dict(), dict(margin_between_x_mm=6.0, margin_between_y_mm=6.0),
                 dict(bleed_mm=3.0), dict(bleed_mm=5.0, margin_between_x_mm=12.0,
                                          margin_between_y_mm=12.0),
                 dict(bleed_mm=3.0, mark_offset_mm=0.0, margin_outer_mm=12.0),
                 dict(cols=3, rows=4, bleed_mm=2.0, margin_between_x_mm=5.0)]
        eps = 1e-9
        for kw in casos:
            with self.subTest(**kw):
                geo = pi.sheet_geometry(cut_cfg(cut_guide="marks", **kw))
                self.assertTrue(geo.marks)
                for x1, y1, x2, y2 in geo.marks:
                    # Espessura mínima só no eixo curto: tocar a borda (distância ==
                    # sangria) não é invadir.
                    ex, ey = (eps, 0) if x1 == x2 else (0, eps)
                    caixa = (min(x1, x2) - ex, min(y1, y2) - ey,
                             max(x1, x2) + ex, max(y1, y2) + ey)
                    for rect in geo.cells + geo.bleeds:
                        self.assertFalse(_overlap(caixa, rect), (caixa, rect))

    def test_nenhuma_celula_com_valor_negativo(self):
        geo = pi.sheet_geometry(cut_cfg(margin_outer_mm=200.0))
        for x0, y0, x1, y1 in geo.cells:
            self.assertGreaterEqual(x1, x0)
            self.assertGreaterEqual(y1, y0)

    def test_funcao_pura_nao_muta_a_config(self):
        cfg = cut_cfg(cut_guide="marks", bleed_mm=3.0)
        antes = dict(cfg.to_dict())
        pi.sheet_geometry(cfg)
        self.assertEqual(cfg.to_dict(), antes)


class CutCompatTests(unittest.TestCase):
    """cut_lines (1.5) → cut_guide (1.6), faixas dos campos novos e presets."""

    def test_cut_lines_true_vira_linhas(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"cut_lines": True})
        self.assertEqual(cfg.cut_guide, "lines")

    def test_cut_lines_false_vira_nenhuma(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"cut_lines": False})
        self.assertEqual(cfg.cut_guide, "none")

    def test_campo_novo_manda_sobre_o_antigo(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"cut_lines": True, "cut_guide": "marks"})
        self.assertEqual(cfg.cut_guide, "marks")

    def test_nao_muta_o_dict_do_chamador(self):
        preset = {"cut_lines": True, "cols": 3}
        pi.LayoutConfig().from_dict(preset)
        self.assertIn("cut_lines", preset)

    def test_cut_lines_nao_existe_mais_no_modelo(self):
        cfg = pi.LayoutConfig()
        self.assertFalse(hasattr(cfg, "cut_lines"))
        self.assertNotIn("cut_lines", cfg.to_dict())
        self.assertNotIn("cut_lines", pi.LayoutConfig.PRESET_FIELDS)

    def test_preset_antigo_de_arquivo_abre_com_linhas(self):
        """Um presets.json da 1.5 (com cut_lines) não perde o corte ligado em silêncio."""
        import json
        antigo = json.loads('{"Cards": {"cols": 2, "rows": 2, "cut_lines": true, '
                            '"cut_color": "#112233", "cut_style": "Tracejada"}}')
        cfg = pi.LayoutConfig()
        cfg.from_dict(antigo["Cards"])
        self.assertEqual((cfg.cut_guide, cfg.cut_color, cfg.cut_style),
                         ("lines", "#112233", "Tracejada"))

    def test_padroes_do_mercado(self):
        cfg = pi.LayoutConfig()
        self.assertEqual((cfg.cut_guide, cfg.mark_length_mm, cfg.mark_offset_mm,
                          cfg.mark_width_pt, cfg.bleed_mm, cfg.bleed_mode),
                         ("none", 4.0, 3.0, 0.25, 0.0, "mirror"))

    def test_preset_ida_e_volta_com_os_campos_novos(self):
        a = pi.LayoutConfig()
        a.from_dict({"cut_guide": "marks", "mark_length_mm": 5.0, "mark_offset_mm": 2.5,
                     "mark_width_pt": 0.5, "bleed_mm": 3.0, "bleed_mode": "included"})
        d = a.preset_dict()
        for k in ("cut_guide", "mark_length_mm", "mark_offset_mm", "mark_width_pt",
                  "bleed_mm", "bleed_mode"):
            self.assertIn(k, d)
        b = pi.LayoutConfig()
        b.from_dict(d)
        self.assertEqual(b.preset_dict(), d)

    def test_valores_fora_de_faixa_sao_ajustados(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"mark_length_mm": 99, "mark_offset_mm": 40, "mark_width_pt": 0,
                       "bleed_mm": -3})
        self.assertEqual((cfg.mark_length_mm, cfg.mark_offset_mm,
                          cfg.mark_width_pt, cfg.bleed_mm), (15.0, 15.0, 0.1, 0.0))
        cfg.from_dict({"mark_length_mm": 0.2, "bleed_mm": 50})
        self.assertEqual((cfg.mark_length_mm, cfg.bleed_mm), (1.0, 10.0))

    def test_valor_ilegivel_cai_no_padrao_e_enum_invalido_tambem(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"mark_length_mm": "abc", "bleed_mm": None,
                       "cut_guide": "zig", "bleed_mode": "zag"})
        self.assertEqual((cfg.mark_length_mm, cfg.bleed_mm, cfg.cut_guide, cfg.bleed_mode),
                         (4.0, 0.0, "none", "mirror"))

    def test_geracao_congelada_leva_os_campos_novos(self):
        cfg = pi.LayoutConfig()
        cfg.from_dict({"cut_guide": "marks", "bleed_mm": 2.0, "bleed_mode": "included"})
        _, frozen = pi.snapshot_for_generation([], cfg)
        self.assertEqual((frozen.cut_guide, frozen.bleed_mm, frozen.bleed_mode),
                         ("marks", 2.0, "included"))

    def test_confirmacao_so_com_aviso_ambar(self):
        self.assertIsNone(pi.cut_confirm_text(cut_cfg(cut_guide="marks")))
        self.assertIsNone(pi.cut_confirm_text(cut_cfg(cut_guide="lines", bleed_mm=3.0,
                                                      margin_between_x_mm=6.0,
                                                      margin_between_y_mm=6.0)))
        txt = pi.cut_confirm_text(cut_cfg(cut_guide="marks", margin_outer_mm=0.0))
        self.assertIn("A margem externa precisa de pelo menos 7 mm", txt)
        self.assertTrue(txt.endswith("Gerar mesmo assim?"))

    def test_rotulos_e_secao_no_codigo(self):
        src = (Path(__file__).resolve().parent.parent / "print_imposer.py"
               ).read_text(encoding="utf-8")
        self.assertIn('_acc_section("corte", "Corte e sangria")', src)
        self.assertEqual(pi.CUT_GUIDE_LABELS,
                         ["Nenhuma", "Linhas atravessando", "Marcas de canto"])
        self.assertEqual(pi.BLEED_MODE_LABELS,
                         ["Estender a borda (espelhar)", "A arte já tem sangria"])
        for rotulo in ("Guia de corte:", "Comprimento (mm):", "Distância do corte (mm):",
                       "Espessura (pt):", "Sangria (mm):"):
            self.assertIn(rotulo, src)
        self.assertIn("corte", pi.SECTION_DEFAULTS)


class CutRasterTests(unittest.TestCase):
    """Desenho raster das marcas e da sangria (mesmo compose_page do preview)."""

    DPI = 150

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _engine(self, n=4, color=(0, 0, 255), **kw):
        cfg = cut_cfg(dpi=self.DPI, **kw)
        eng = pi.ImpositionEngine([], cfg)
        cw, ch = eng.cell_px()
        img = make_image(self.tmp / "fonte.png", cw, ch, color)
        return eng, [img] * n

    def _px(self, mm):
        return int(mm * self.DPI / 25.4 + 0.5)

    @staticmethod
    def _componentes_pretos(page):
        """Conta componentes conexos (4-vizinhança) de pixels pretos puros."""
        w, h = page.size
        pix = page.load()
        pretos = {(x, y) for y in range(h) for x in range(w) if pix[x, y] == (0, 0, 0)}
        n = 0
        while pretos:
            n += 1
            pilha = [pretos.pop()]
            while pilha:
                x, y = pilha.pop()
                for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if p in pretos:
                        pretos.discard(p)
                        pilha.append(p)
        return n

    def test_marcas_celulas_coladas_sao_12_componentes(self):
        eng, imgs = self._engine(cut_guide="marks")
        self.assertEqual(self._componentes_pretos(eng.compose_page(0, imgs)), 12)

    def test_marcas_com_espacamento_sao_16_componentes(self):
        eng, imgs = self._engine(cut_guide="marks", margin_between_x_mm=6.0,
                                 margin_between_y_mm=6.0)
        self.assertEqual(self._componentes_pretos(eng.compose_page(0, imgs)), 16)

    def test_marca_na_margem_e_nenhuma_dentro_do_corte_e_da_sangria(self):
        eng, imgs = self._engine(cut_guide="marks", margin_between_x_mm=6.0,
                                 margin_between_y_mm=6.0, bleed_mm=3.0)
        page = eng.compose_page(0, imgs)
        geo = pi.sheet_geometry(eng.cfg)
        # Uma marca vertical acima da grade: pixel preto no meio dela.
        x1, y1, x2, y2 = next(m for m in geo.marks if m[0] == m[2] and m[3] <= geo.grid[1])
        self.assertEqual(page.getpixel((self._px(x1), self._px((y1 + y2) / 2))), (0, 0, 0))
        # Nada de preto dentro de nenhum retângulo de sangria (que contém o de corte).
        for x0, y0, xe, ye in geo.bleeds:
            reg = page.crop((self._px(x0), self._px(y0), self._px(xe), self._px(ye)))
            self.assertNotIn((0, 0, 0), set(reg.getdata()))
        self.assertEqual(self._componentes_pretos(page), 16)

    def test_espessura_em_pt_vira_px_com_minimo_de_1(self):
        eng, imgs = self._engine(cut_guide="marks", mark_width_pt=0.25)
        page = eng.compose_page(0, imgs)
        m = pi.sheet_geometry(eng.cfg).marks[0]
        x, y = self._px(m[0]), self._px((m[1] + m[3]) / 2)
        self.assertEqual(page.getpixel((x, y)), (0, 0, 0))
        self.assertNotEqual(page.getpixel((x + 3, y)), (0, 0, 0))   # 0,25 pt a 150 dpi = 1 px
        eng.cfg.mark_width_pt = 2.0                                  # 2 pt a 150 dpi ≈ 4 px
        page = eng.compose_page(0, imgs)
        self.assertEqual(page.getpixel((x + 1, y)), (0, 0, 0))

    def test_sem_marcas_nao_ha_preto(self):
        eng, imgs = self._engine(cut_guide="none")
        self.assertEqual(self._componentes_pretos(eng.compose_page(0, imgs)), 0)

    def test_preview_a_72_dpi_tambem_desenha_as_marcas(self):
        eng, imgs = self._engine(cut_guide="marks")
        page = eng.compose_page(0, imgs, override_dpi=72)
        self.assertEqual(self._componentes_pretos(page), 12)

    def test_linhas_atravessando_continuam_desenhando(self):
        eng, imgs = self._engine(cut_guide="lines", margin_between_x_mm=10.0)
        eng.cfg.cut_color = "#FF0000"
        page = eng.compose_page(0, imgs)
        achou = any(page.getpixel((x, 5)) == (255, 0, 0) for x in range(page.width))
        self.assertTrue(achou)

    # ── sangria espelhada ───────────────────────────────────────────────────

    def _fonte_marcada(self, eng, name="marcada.png"):
        """Fonte do tamanho exato da célula: coluna 0 amarela, linha 0 vermelha."""
        cw, ch = eng.cell_px()
        img = Image.new("RGB", (cw, ch), (0, 0, 255))
        img.paste((255, 255, 0), (0, 0, 1, ch))
        img.paste((255, 0, 0), (0, 0, cw, 1))
        path = self.tmp / name
        img.save(path)
        return str(path)

    def test_sangria_espelhada_reflete_a_borda_da_celula(self):
        eng = pi.ImpositionEngine([], cut_cfg(dpi=self.DPI, fit_mode="stretch",
                                              bleed_mm=3.0, margin_between_x_mm=6.0,
                                              margin_between_y_mm=6.0))
        fonte = self._fonte_marcada(eng)
        page = eng.compose_page(0, [fonte] * 4)
        x, y = self._px(10.0), self._px(10.0)
        b = eng.bleed_px()
        self.assertGreater(b, 3)
        # Esquerda: a 1ª coluna da faixa é a 1ª coluna da célula (amarela); a 2ª, a 2ª (azul).
        self.assertEqual(page.getpixel((x - 1, y + 40)), (255, 255, 0))
        self.assertEqual(page.getpixel((x - 2, y + 40)), (0, 0, 255))
        # Topo: espelha a linha 0 (vermelha).
        self.assertEqual(page.getpixel((x + 40, y - 1)), (255, 0, 0))
        # Canto: espelhado nos dois eixos = o pixel (0,0) da célula (vermelho, desenhado por último).
        self.assertEqual(page.getpixel((x - 1, y - 1)), (255, 0, 0))
        # A faixa tem a largura da sangria: um pixel além dela é fundo.
        self.assertEqual(page.getpixel((x - b - 1, y + 40)), (255, 255, 255))

    def test_sangria_espelhada_nao_invade_a_celula_vizinha(self):
        eng = pi.ImpositionEngine([], cut_cfg(dpi=self.DPI, fit_mode="stretch",
                                              bleed_mm=3.0, margin_between_x_mm=2.0,
                                              margin_between_y_mm=2.0))
        fonte = self._fonte_marcada(eng)
        page = eng.compose_page(0, [fonte] * 4)
        cw, ch = eng.cell_px()
        x0, y0 = self._px(10.0), self._px(10.0)
        # Última coluna e última linha da célula 0 seguem azuis: a sangria da vizinha
        # (limitada a metade do vão) não passou por cima.
        self.assertEqual(page.getpixel((x0 + cw - 1, y0 + 40)), (0, 0, 255))
        self.assertEqual(page.getpixel((x0 + 40, y0 + ch - 1)), (0, 0, 255))

    def test_sem_sangria_o_modo_e_irrelevante(self):
        eng, imgs = self._engine(cut_guide="none")
        a = eng.compose_page(0, imgs)
        eng.cfg.bleed_mm = 0.0
        eng.cfg.bleed_mode = "included"
        self.assertEqual(list(a.getdata()), list(eng.compose_page(0, imgs).getdata()))

    # ── sangria «a arte já tem» ─────────────────────────────────────────────

    def test_arte_com_sangria_cai_no_corte(self):
        eng = pi.ImpositionEngine([], cut_cfg(dpi=self.DPI, fit_mode="stretch",
                                              bleed_mm=3.0, bleed_mode="included",
                                              margin_between_x_mm=6.0,
                                              margin_between_y_mm=6.0))
        cw, ch = eng.cell_px()
        b = eng.bleed_px()
        # Fonte do tamanho da célula aumentada: borda extra amarela, 1º pixel de dentro verde.
        img = Image.new("RGB", (cw + 2 * b, ch + 2 * b), (0, 0, 255))
        img.paste((255, 255, 0), (0, 0, b, ch + 2 * b))
        img.paste((0, 200, 0), (b, 0, b + 1, ch + 2 * b))
        path = self.tmp / "com_sangria.png"
        img.save(path)
        page = eng.compose_page(0, [str(path)] * 4)
        x, y = self._px(10.0), self._px(10.0)
        self.assertEqual(page.getpixel((x, y + 40)), (0, 200, 0))        # corte = borda de dentro
        self.assertEqual(page.getpixel((x - 1, y + 40)), (255, 255, 0))  # sangria da própria arte

    def test_guarda_de_qualidade_mede_contra_a_celula_aumentada(self):
        a6 = dict(paper_w_mm=105.0, paper_h_mm=148.0, cols=1, rows=1,
                  margin_outer_mm=0.0, dpi=300)
        fonte = make_image(self.tmp / "a6.png", 1240, 1748)

        def rel(**kw):
            cfg = cut_cfg(**{**a6, **kw})
            return pi.ImpositionEngine([pi.ImageEntry(fonte)], cfg).quality_report()

        sem = rel()
        com = rel(bleed_mm=3.0, bleed_mode="included")
        espelho = rel(bleed_mm=3.0, bleed_mode="mirror")
        b = pi.ImpositionEngine([], cut_cfg(**a6, bleed_mm=3.0)).bleed_px()
        self.assertEqual(com["cell"], (sem["cell"][0] + 2 * b, sem["cell"][1] + 2 * b))
        self.assertLess(com["ratio"], sem["ratio"])
        self.assertEqual(espelho["cell"], sem["cell"])         # espelhar não muda a célula


class IncludedBleedBoxTests(unittest.TestCase):
    """Fonte vetorial no modo «A arte já tem sangria»: a caixa de render vira (cw+2b, ch+2b)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.svg = self.tmp / "deitado.svg"
        self.svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" '
            'viewBox="0 0 300 200"><rect width="300" height="200"/></svg>',
            encoding="utf-8")
        self.calls = []

        def fake_render(path, out_w, out_h):
            self.calls.append((out_w, out_h))
            return Image.new("RGBA", (out_w, out_h), (10, 10, 10, 255))

        p = mock.patch.object(pi, "_svg_backend_render", fake_render)
        p.start()
        self.addCleanup(p.stop)

    def _engine(self, **kw):
        cfg = pi.LayoutConfig()
        cfg.cols, cfg.rows, cfg.dpi = 2, 2, 72
        cfg.paper_w_mm, cfg.paper_h_mm = 100.0, 200.0     # célula em pé
        cfg.margin_outer_mm = 10.0
        cfg.margin_between_x_mm = cfg.margin_between_y_mm = 6.0
        for k, v in kw.items():
            setattr(cfg, k, v)
        return pi.ImpositionEngine([pi.ImageEntry(str(self.svg))], cfg)

    def test_sem_auto_rotate_a_caixa_e_a_celula_aumentada(self):
        eng = self._engine(auto_rotate=False, bleed_mm=3.0, bleed_mode="included",
                           fit_mode="stretch")
        cw, ch = eng.cell_px(72)
        b = eng.bleed_px(72)
        self.assertGreater(b, 0)
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        # stretch renderiza cobrindo a caixa (cw+2b, ch+2b): os dois lados >= a caixa.
        self.assertGreaterEqual(self.calls[-1][0], cw + 2 * b - 1)
        self.assertGreaterEqual(self.calls[-1][1], ch + 2 * b - 1)

    def test_com_auto_rotate_a_caixa_nasce_girada_e_aumentada(self):
        eng = self._engine(auto_rotate=True, bleed_mm=3.0, bleed_mode="included")
        cw, ch = eng.cell_px(72)
        b = eng.bleed_px(72)
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        out_w, out_h = self.calls[-1]
        bw, bh = cw + 2 * b, ch + 2 * b
        # Arte deitada numa célula em pé: renderiza deitada na caixa (bh, bw).
        self.assertLessEqual(out_w, bh + 1)
        self.assertLessEqual(out_h, bw + 1)
        self.assertTrue(abs(out_w - bh) <= 1 or abs(out_h - bw) <= 1)

    def test_sem_sangria_a_caixa_continua_a_celula(self):
        eng = self._engine(auto_rotate=False, bleed_mm=0.0, bleed_mode="included")
        cw, ch = eng.cell_px(72)
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        self.assertLessEqual(self.calls[-1][0], cw + 1)
        self.assertLessEqual(self.calls[-1][1], ch + 1)

    def test_modo_espelhar_nao_aumenta_a_caixa(self):
        eng = self._engine(auto_rotate=False, bleed_mm=3.0, bleed_mode="mirror")
        cw, ch = eng.cell_px(72)
        self.calls.clear()
        eng.compose_page(0, eng._expand(), override_dpi=72)
        self.assertLessEqual(self.calls[-1][0], cw + 1)
        self.assertLessEqual(self.calls[-1][1], ch + 1)


class LauncherTests(unittest.TestCase):
    def test_bat_e_ascii_puro(self):
        """CMD usa codepage legado: acento vindo de UTF-8 sai corrompido."""
        content = pi.build_launcher_bat("C:\\Tools\\print_imposer.py")
        content.encode("ascii")          # levanta se escapou algum acento

    def test_bat_tem_start_e_caminho(self):
        content = pi.build_launcher_bat("C:\\Tools\\print_imposer.py")
        self.assertIn("@echo off", content)
        self.assertIn("start \"\"", content)
        self.assertIn("print_imposer.py", content)
        self.assertIn("\r\n", content)   # CRLF, como .bat espera


if __name__ == "__main__":
    unittest.main(verbosity=2)
