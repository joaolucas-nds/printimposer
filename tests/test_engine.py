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
        self.cfg.margin_outer_mm = self.cfg.margin_between_mm = 0.0
        cw, ch = self.eng.cell_px()
        self.assertEqual((cw, ch), (1240, 1754))   # metade exata de A4

    def test_margens_encolhem_a_celula(self):
        self.cfg.dpi = 300
        self.cfg.cols = self.cfg.rows = 2
        base_w, base_h = self.eng.cell_px()
        self.cfg.margin_outer_mm = 5.0
        self.cfg.margin_between_mm = 3.0
        new_w, new_h = self.eng.cell_px()
        self.assertLess(new_w, base_w)
        self.assertLess(new_h, base_h)

    def test_celula_mm_coerente(self):
        self.cfg.cols, self.cfg.rows = 2, 2
        self.cfg.margin_outer_mm = self.cfg.margin_between_mm = 0.0
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
        self.cfg.cut_lines = True
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
        "Ajuda":   ["Guia rápido: Figma → impressão", "Sobre o PrintImposer"],
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
        self.assertEqual(pi.VERSION, "1.2.0")


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
