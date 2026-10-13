"""Gerador da marca JEAN · Fundação dos Dados — fonte única de toda a identidade.

Por que existe: antes, a paleta antiga estava copiada à mão em ~6 lugares (site, capas,
skill de carrossel, demos) e cada cópia derivou. Aqui ficam UMA geometria do símbolo,
UM dourado e UM wordmark; todo arquivo em /marca é gerado a partir deles.

A geometria foi MEDIDA no board aprovado (11/10/2026), não redesenhada:
  - caixa do símbolo 536 × 802, isométrico com inclinação k = 0,66 (≈ 33°);
  - "JEAN" é Montserrat SemiBold com cada letra encaixada na caixa medida no board
    (o board usa a Montserrat alargada);
  - as linhas de construção saem de arestas e vértices reais do símbolo.

Armadilha: o texto vira CURVA (fontTools). Os SVG não dependem da fonte instalada —
mas qualquer mudança de texto tem que passar por aqui, não por edição no SVG.

Uso:
  python marca/_fonte/gerar_marca.py          # gera os SVG + tokens.css em /marca
  powershell -File marca/_fonte/renderizar.ps1  # gera os PNG (favicon, ícone, prévias)
"""

import math
import os
from functools import lru_cache

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.dirname(AQUI)
FONTE_VF = os.path.join(AQUI, "fontes", "Montserrat-VF.ttf")
URL_FONTE = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"

# ------------------------------------------------------------------ paleta (board)
PRETO, GRAFITE, OURO, AREIA, BRANCO = "#0A0A0A", "#1E1E1E", "#D4AF37", "#EDE7DA", "#FAFAF8"

# ------------------------------------------------------------------ geometria do símbolo
# Camada de cima: espessura 107, vértice em x = 243, entalhe de 4 no centro.
# Camada de baixo: espessura 95, vão de 75 entre as camadas. Haste x 420 → 536.
PECAS = {
    "v_esq": "M0 546.6 L243 707 L243 802 L0 641.6 Z",
    "v_dir": "M243 707 L536 513.6 L536 608.6 L243 802 Z",
    "v":     "M0 546.6 L243 707 L536 513.6 L536 608.6 L243 802 L0 641.6 Z",
    "braco": "M241 523.7 L81.1 418.1 L0 471.6 L241 630.7 Z",
    "j":     "M245 523.7 L420 408.2 L420 77 L536 0 L536 438.6 L245 630.7 Z",
    "gema":  "M140 327.5 L360 160 L360 351.3 L268 412 Z",
}
CAIXA_3D = "-20 -20 576 842"   # margem p/ sombra e brilho
CAIXA_PLANA = "-4 -4 544 810"

# ------------------------------------------------------------------ dourado em faces (medido no board)
DEFS_OURO = """
<linearGradient id="f-j" x1=".3" y1="0" x2=".1" y2="1"><stop offset="0" stop-color="#F2CC85"/><stop offset=".3" stop-color="#E2B062"/><stop offset=".62" stop-color="#BF8A45"/><stop offset=".82" stop-color="#A9773A"/><stop offset="1" stop-color="#875925"/></linearGradient>
<linearGradient id="f-braco" x1="0" y1=".3" x2="1" y2=".7"><stop offset="0" stop-color="#E6BD7A"/><stop offset=".3" stop-color="#CC9C58"/><stop offset=".72" stop-color="#97693A"/><stop offset=".9" stop-color="#5E3F1C"/><stop offset="1" stop-color="#36240E"/></linearGradient>
<linearGradient id="f-v-esq" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#CF9F5E"/><stop offset=".5" stop-color="#AC7C42"/><stop offset="1" stop-color="#7F562A"/></linearGradient>
<linearGradient id="f-v-dir" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#6A4720"/><stop offset=".45" stop-color="#9C6E38"/><stop offset="1" stop-color="#CD9B57"/></linearGradient>
<linearGradient id="f-gema" x1=".1" y1="0" x2=".7" y2="1"><stop offset="0" stop-color="#FBE2A8"/><stop offset=".45" stop-color="#F0C57E"/><stop offset=".8" stop-color="#D9A55E"/><stop offset="1" stop-color="#B58142"/></linearGradient>
<linearGradient id="f-espessura" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5E4019"/><stop offset="1" stop-color="#2E1F0C"/></linearGradient>
<radialGradient id="brilho" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFE7B0" stop-opacity=".8"/><stop offset=".35" stop-color="#E9B866" stop-opacity=".25"/><stop offset="1" stop-color="#E9B866" stop-opacity="0"/></radialGradient>
<filter id="sombra" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="12" stdDeviation="14" flood-color="#000" flood-opacity=".85"/></filter>
<filter id="escovado" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.9 0.015" numOctaves="2" seed="11" result="r"/><feColorMatrix in="r" type="matrix" values="0 0 0 0 1  0 0 0 0 .92  0 0 0 0 .75  0 0 0 .6 -.25"/><feComposite in2="SourceGraphic" operator="in"/></filter>
"""

DEFS_PLANO = """
<linearGradient id="f-gema-plana" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E9C27E"/><stop offset="1" stop-color="#B98A45"/></linearGradient>
"""


def simbolo_ouro(sufixo=""):
    """Símbolo 3D em ouro (para fundo escuro): faces, espessura da chapa, bisel e luz."""
    p = PECAS
    return f"""<g filter="url(#sombra)">
  <path d="{p['v_esq']}" fill="url(#f-v-esq)"/><path d="{p['v_dir']}" fill="url(#f-v-dir)"/>
  <path d="{p['braco']}" fill="url(#f-braco)"/><path d="{p['j']}" fill="url(#f-j)"/><path d="{p['gema']}" fill="url(#f-gema)"/>
</g>
<g fill="url(#f-espessura)" opacity=".75">
  <path d="M0 465.6 L241 624.7 L241 630.7 L0 471.6 Z"/><path d="M245 624.7 L536 432.6 L536 438.6 L245 630.7 Z"/>
  <path d="M0 634.6 L243 795 L243 802 L0 641.6 Z"/><path d="M243 795 L536 601.6 L536 608.6 L243 802 Z"/>
  <path d="M140 327.5 L268 412 L360 351.3 L360 345.3 L268 406 L140 321.5 Z"/>
</g>
<g filter="url(#escovado)" opacity=".1">
  <path d="{p['v']}"/><path d="{p['braco']}"/><path d="{p['j']}"/><path d="{p['gema']}"/>
</g>
<g fill="none" stroke="#FFE6B2" stroke-linecap="round">
  <path d="M420 77 L536 0" stroke-width="3.5"/><path d="M536 0 L536 430" stroke-width="2" opacity=".5"/>
  <path d="M420 79 L420 408" stroke-width="2" opacity=".28"/><path d="M81.1 418.1 L241 523.7" stroke-width="3" opacity=".85"/>
  <path d="M0 471.6 L81.1 418.1" stroke-width="2.5" opacity=".7"/><path d="M245 523.7 L420 408.2" stroke-width="2.5" opacity=".5"/>
  <path d="M245 525 L245 624" stroke-width="2" opacity=".55"/><path d="M243 707 L536 513.6" stroke-width="3.5" opacity=".95"/>
  <path d="M0 546.6 L243 707" stroke-width="2.5" opacity=".55"/><path d="M243 709 L243 795" stroke-width="3" opacity=".8"/>
  <path d="M140 327.5 L360 160" stroke-width="3.5"/><path d="M360 162 L360 345" stroke-width="1.5" opacity=".4"/>
</g>
<g style="mix-blend-mode:screen">
  <ellipse cx="520" cy="18" rx="110" ry="80" fill="url(#brilho)"/>
  <ellipse cx="170" cy="318" rx="80" ry="55" fill="url(#brilho)" opacity=".65"/>
  <ellipse cx="243" cy="712" rx="60" ry="40" fill="url(#brilho)" opacity=".45"/>
</g>"""


def simbolo_animado():
    """O símbolo sendo construído: as linhas de construção se desenham e as camadas sobem da base
    para o topo (camada de baixo → braço → haste → gema). É o único movimento do site: mostra a
    "fundação que vira decisão" em vez de decorar. Respeita prefers-reduced-motion (aparece pronto).
    Cada peça leva a própria espessura e o próprio bisel para poder entrar sozinha."""
    p = PECAS
    grad_c, corpo_c = construcao()
    corpo_c = corpo_c.replace("<line ", '<line class="linha" pathLength="1" ').replace("<circle ", '<circle class="linha" pathLength="1" ')
    bisel = 'fill="none" stroke="#FFE6B2" stroke-linecap="round"'
    pecas = [
        ("p1", f'<path d="{p["v_esq"]}" fill="url(#f-v-esq)"/><path d="{p["v_dir"]}" fill="url(#f-v-dir)"/>'
               '<g fill="url(#f-espessura)" opacity=".75"><path d="M0 634.6 L243 795 L243 802 L0 641.6 Z"/><path d="M243 795 L536 601.6 L536 608.6 L243 802 Z"/></g>'
               f'<g {bisel}><path d="M243 707 L536 513.6" stroke-width="3.5" opacity=".95"/><path d="M0 546.6 L243 707" stroke-width="2.5" opacity=".55"/><path d="M243 709 L243 795" stroke-width="3" opacity=".8"/></g>'),
        ("p2", f'<path d="{p["braco"]}" fill="url(#f-braco)"/>'
               '<path d="M0 465.6 L241 624.7 L241 630.7 L0 471.6 Z" fill="url(#f-espessura)" opacity=".75"/>'
               f'<g {bisel}><path d="M81.1 418.1 L241 523.7" stroke-width="3" opacity=".85"/><path d="M0 471.6 L81.1 418.1" stroke-width="2.5" opacity=".7"/></g>'),
        ("p3", f'<path d="{p["j"]}" fill="url(#f-j)"/>'
               '<path d="M245 624.7 L536 432.6 L536 438.6 L245 630.7 Z" fill="url(#f-espessura)" opacity=".75"/>'
               f'<g {bisel}><path d="M420 77 L536 0" stroke-width="3.5"/><path d="M536 0 L536 430" stroke-width="2" opacity=".5"/>'
               '<path d="M420 79 L420 408" stroke-width="2" opacity=".28"/><path d="M245 523.7 L420 408.2" stroke-width="2.5" opacity=".5"/><path d="M245 525 L245 624" stroke-width="2" opacity=".55"/></g>'),
        ("p4", f'<path d="{p["gema"]}" fill="url(#f-gema)"/>'
               '<path d="M140 327.5 L268 412 L360 351.3 L360 345.3 L268 406 L140 321.5 Z" fill="url(#f-espessura)" opacity=".75"/>'
               f'<g {bisel}><path d="M140 327.5 L360 160" stroke-width="3.5"/><path d="M360 162 L360 345" stroke-width="1.5" opacity=".4"/></g>'),
    ]
    # Estado normal = símbolo PRONTO. A animação parte do invisível só enquanto roda ("both"): se o
    # navegador não animar (ou animar SVG dentro de <img> de outro jeito), o símbolo aparece inteiro.
    estilo = """<style>
  .linha { animation: desenhar 1.4s cubic-bezier(.4,0,.2,1) both; stroke-dasharray: 1; }
  .peca { animation: subir .75s cubic-bezier(.2,.7,.2,1) both; }
  .p1 { animation-delay: .9s } .p2 { animation-delay: 1.15s } .p3 { animation-delay: 1.4s } .p4 { animation-delay: 1.75s }
  .luz { animation: acender .9s ease-out 2.2s both; }
  @keyframes desenhar { from { stroke-dashoffset: 1 } to { stroke-dashoffset: 0 } }
  @keyframes subir { from { opacity: 0; transform: translateY(46px) } to { opacity: 1; transform: none } }
  @keyframes acender { from { opacity: 0 } to { opacity: 1 } }
  @media (prefers-reduced-motion: reduce) { .linha, .peca, .luz { animation: none; } }
</style>"""
    luz = ('<g class="luz" style="mix-blend-mode:screen"><ellipse cx="520" cy="18" rx="110" ry="80" fill="url(#brilho)"/>'
           '<ellipse cx="170" cy="318" rx="80" ry="55" fill="url(#brilho)" opacity=".65"/></g>')
    corpo = corpo_c + "".join(f'<g class="peca {c}" filter="url(#sombra)">{g}</g>' for c, g in pecas) + luz
    return grad_c, estilo, corpo


def simbolo_ouro_simples():
    """Ouro em faces SEM filtros (favicon e tamanhos pequenos: sombra e textura viram borrão)."""
    p = PECAS
    return (f'<path d="{p["v_esq"]}" fill="url(#f-v-esq)"/><path d="{p["v_dir"]}" fill="url(#f-v-dir)"/>'
            f'<path d="{p["braco"]}" fill="url(#f-braco)"/><path d="{p["j"]}" fill="url(#f-j)"/>'
            f'<path d="{p["gema"]}" fill="url(#f-gema)"/>')


def simbolo_claro():
    p = PECAS
    return (f'<g fill="{PRETO}"><path d="{p["v"]}"/><path d="{p["braco"]}"/><path d="{p["j"]}"/></g>'
            f'<path d="{p["gema"]}" fill="url(#f-gema-plana)"/>')


def simbolo_mono(cor):
    p = PECAS
    return f'<g fill="{cor}"><path d="{p["v"]}"/><path d="{p["braco"]}"/><path d="{p["j"]}"/><path d="{p["gema"]}"/></g>'


# ------------------------------------------------------------------ construção (rascunho preso ao símbolo)

def construcao():
    """Cada linha sai de uma aresta/vértice real. Caixa com o círculo grande tangente às guias
    de cima, de baixo e da direita; a diagonal principal (ponta da camada de cima → canto da
    haste) termina no canto da caixa; círculo áureo (× 0,618) tangente à base e à direita."""
    k_diag = (471.6 - 0) / (0 - 536)
    k_haste = (77 - 0) / (420 - 536)
    k_gema = (160 - 327.5) / (360 - 140)
    k_v = (513.6 - 707) / (536 - 243)
    yv = lambda x0, y0, k, x: y0 + k * (x - x0)
    topo, base = -127.0, 802.0
    r = (base - topo) / 2
    dir_x = 536 + (topo - 0) / k_diag
    cx, cy = dir_x - r, topo + r
    r2 = r * 0.618
    ve = 'vector-effect="non-scaling-stroke"'
    L = lambda x1, y1, x2, y2: f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {ve}/>'
    C = lambda x, y, rr: f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" {ve}/>'
    linhas = [
        L(-260, topo, dir_x + 60, topo), L(-260, base, dir_x + 60, base), L(dir_x, topo - 70, dir_x, base + 70),
        L(243, topo - 70, 243, base + 70), L(536, topo - 70, 536, base + 70), L(-280, 327.5, 140, 327.5),
        C(cx, cy, r), C(dir_x - r2, base - r2, r2),
        L(dir_x, topo, -190, yv(0, 471.6, k_diag, -190)),
        L(dir_x, yv(536, 0, k_haste, dir_x), -170, yv(536, 0, k_haste, -170)),
        L(-210, yv(140, 327.5, k_gema, -210), 536, yv(140, 327.5, k_gema, 536)),
        L(243, 707, dir_x, yv(243, 707, k_v, dir_x)),
    ]
    grad = (f'<radialGradient id="g-traco" gradientUnits="userSpaceOnUse" cx="{cx:.0f}" cy="{cy:.0f}" r="720">'
            '<stop offset="0" stop-color="#E0BA62" stop-opacity=".62"/><stop offset=".55" stop-color="#C9A04A" stop-opacity=".36"/>'
            '<stop offset="1" stop-color="#C9A04A" stop-opacity="0"/></radialGradient>')
    corpo = '<g fill="none" stroke="url(#g-traco)" stroke-width="1.1">' + "".join(linhas) + "</g>"
    return grad, corpo


# ------------------------------------------------------------------ texto em curvas

def garantir_fonte():
    if not os.path.exists(FONTE_VF):
        import urllib.request
        os.makedirs(os.path.dirname(FONTE_VF), exist_ok=True)
        urllib.request.urlretrieve(URL_FONTE, FONTE_VF)


@lru_cache(maxsize=None)
def fonte(peso):
    garantir_fonte()
    return instantiateVariableFont(TTFont(FONTE_VF), {"wght": peso}, inplace=False)


def _glifos(peso, texto):
    f = fonte(peso)
    cmap, gs = f.getBestCmap(), f.getGlyphSet()
    return f, gs, [(cmap[ord(c)], gs[cmap[ord(c)]]) for c in texto]


def _limites(gs, glifo):
    bp = BoundsPen(gs)
    glifo.draw(bp)
    return bp.bounds  # (xMin, yMin, xMax, yMax) ou None (espaço)


def _desenho(gs, glifo, xx, yy, sx, sy):
    pen = SVGPathPen(gs)
    glifo.draw(TransformPen(pen, (sx, 0, 0, -sy, xx, yy)))
    return pen.getCommands()


def letras_encaixadas(peso, letras_caixas, cap_topo, base):
    """Cada letra ocupa exatamente (x0 → x1) e a caixa alta vai de cap_topo a base."""
    f, gs, _ = _glifos(peso, "E")
    cap = _limites(gs, gs[f.getBestCmap()[ord("E")]])[3]
    sy = (base - cap_topo) / cap
    partes = []
    for letra, x0, x1 in letras_caixas:
        _, gs, [(_, g)] = _glifos(peso, letra)
        xmin, _, xmax, _ = _limites(gs, g)
        sx = (x1 - x0) / (xmax - xmin)
        partes.append(_desenho(gs, g, x0 - xmin * sx, base, sx, sy))
    return " ".join(partes)


def linha_justificada(peso, texto, tamanho, x_ini, x_fim, base):
    """Tinta do 1º glifo começa em x_ini e a do último termina em x_fim (espaço extra igual entre glifos)."""
    f, gs, gl = _glifos(peso, texto)
    s = tamanho / f["head"].unitsPerEm
    hmtx = f["hmtx"]
    avancos = [hmtx[nome][0] * s for nome, _ in gl]
    lim = [_limites(gs, g) for _, g in gl]
    esq = lim[0][0] * s
    dir_ult = lim[-1][2] * s
    natural = sum(avancos[:-1]) + dir_ult - esq
    extra = ((x_fim - x_ini) - natural) / (len(gl) - 1)
    x = x_ini - esq
    partes = []
    for (nome, g), a, b in zip(gl, avancos, lim):
        if b is not None:
            partes.append(_desenho(gs, g, x, base, s, s))
        x += a + extra
    return " ".join(partes)


def texto(peso, conteudo, tamanho, x, base, espaco_em=0.0, alinhar="esquerda"):
    """Linha de texto em curvas com espaçamento entre letras (em 'em'), sem justificar."""
    f, gs, gl = _glifos(peso, conteudo)
    s = tamanho / f["head"].unitsPerEm
    avancos = [f["hmtx"][nome][0] * s + espaco_em * tamanho for nome, _ in gl]
    largura = sum(avancos) - espaco_em * tamanho
    xx = x - largura if alinhar == "direita" else x - largura / 2 if alinhar == "centro" else x
    partes = []
    for (nome, g), a in zip(gl, avancos):
        if _limites(gs, g) is not None:
            partes.append(_desenho(gs, g, xx, base, s, s))
        xx += a
    return " ".join(partes)


def wordmark(cor_nome, cor_sub, cor_serv, cor_traco):
    """Origem = topo esquerdo do J; caixa alta do JEAN = 107. Igual à folha aprovada."""
    jean = letras_encaixadas(600, [("J", 0, 115), ("E", 205, 320), ("A", 405, 555), ("N", 635, 765)], 0, 107)
    sub = linha_justificada(400, "FUNDAÇÃO DOS DADOS", 40, 0, 765, 176)
    serv = linha_justificada(400, "Consultoria de Dados", 33, 140, 597, 260)
    return (f'<path d="{jean}" fill="{cor_nome}"/><path d="{sub}" fill="{cor_sub}"/>'
            f'<rect x="-1" y="246" width="95" height="4" fill="{cor_traco}"/><path d="{serv}" fill="{cor_serv}"/>')


def lema(cor, cor_traco):
    """Lema do board, em caixa alta espaçada, depois da divisória."""
    linhas = [("DADOS", 290, 110), ("ORGANIZAM.", 329, 215), ("CLAREZA", 368, 153),
              ("CONECTA.", 407, 172), ("DECISÕES", 447, 167), ("TRANSFORMAM.", 486, 277)]
    d = " ".join(linha_justificada(500, t, 26, 1585, 1585 + w, y) for t, y, w in linhas)
    return f'<path d="{d}" fill="{cor}"/><rect x="1585" y="535" width="68" height="4" fill="{cor_traco}"/>'


# ------------------------------------------------------------------ montagem dos arquivos

def svg(viewbox, corpo, defs="", w=None, h=None, titulo="JEAN · Fundação dos Dados"):
    dims = f' width="{w}" height="{h}"' if w else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}"{dims} role="img">'
            f'<title>{titulo}</title><defs>{defs}</defs>{corpo}</svg>\n')


def em(x, y, escala, corpo):
    return f'<g transform="translate({x} {y}) scale({escala})">{corpo}</g>'


def gerar():
    arquivos = {}
    grad_c, corpo_c = construcao()

    # símbolos
    arquivos["simbolo-ouro.svg"] = svg(CAIXA_3D, simbolo_ouro(), DEFS_OURO)
    arquivos["simbolo-claro.svg"] = svg(CAIXA_PLANA, simbolo_claro(), DEFS_PLANO)
    arquivos["simbolo-mono-preto.svg"] = svg(CAIXA_PLANA, simbolo_mono(PRETO))
    arquivos["simbolo-mono-branco.svg"] = svg(CAIXA_PLANA, simbolo_mono(BRANCO))
    arquivos["simbolo-construcao.svg"] = svg("-300 -210 1060 1100", corpo_c + simbolo_ouro(), DEFS_OURO + grad_c)
    grad_a, estilo_a, corpo_a = simbolo_animado()
    arquivos["simbolo-animado.svg"] = svg("-300 -210 1060 1100", estilo_a + corpo_a, DEFS_OURO + grad_a)

    # logo principal (o do board): fundo escuro, construção, wordmark, divisória e lema
    s = 0.4795  # escala do símbolo no logo principal (origem do símbolo em 248, 208)
    fundo = ('<radialGradient id="fundo" cx="22%" cy="48%" r="80%"><stop offset="0" stop-color="#15130F"/>'
             '<stop offset=".5" stop-color="#0B0A09"/><stop offset="1" stop-color="#050505"/></radialGradient>')
    principal = ('<rect width="1907" height="760" fill="url(#fundo)"/>'
                 + em(248, 208, s, corpo_c) + em(248, 208, s, simbolo_ouro())
                 + em(625, 283, 1, wordmark("#F7F4EE", "#ECE6DA", "#DAD5CB", OURO))
                 + '<rect x="1505" y="252" width="2.5" height="320" fill="#A98535"/>' + lema("#E8E2D6", OURO))
    arquivos["logo-principal.svg"] = svg("0 0 1907 760", principal, DEFS_OURO + grad_c + fundo)

    # lockups compactos (proporção do board: símbolo ≈ 4,3 × a caixa alta do JEAN)
    def compacto(simb, wm):
        return em(133.6, 64, 0.1823, simb) + em(260, 104, 0.3195, wm)
    vb = "122 52 396 170"
    arquivos["logo-escuro.svg"] = svg(vb, compacto(simbolo_ouro(), wordmark("#F7F4EE", "#ECE6DA", "#DAD5CB", OURO)), DEFS_OURO)
    arquivos["logo-claro.svg"] = svg(vb, compacto(simbolo_claro(), wordmark(PRETO, "#2A2723", "#4B463E", "#C9A03A")), DEFS_PLANO)
    arquivos["logo-mono-preto.svg"] = svg(vb, compacto(simbolo_mono(PRETO), wordmark(PRETO, PRETO, PRETO, PRETO)))
    arquivos["logo-mono-branco.svg"] = svg(vb, compacto(simbolo_mono(BRANCO), wordmark(BRANCO, BRANCO, BRANCO, BRANCO)))

    # ícone de app / favicon: quadrado grafite arredondado, ouro em faces sem filtro
    borda = ('<linearGradient id="borda-app" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a342a"/>'
             '<stop offset="1" stop-color="#141414"/></linearGradient>')
    esc = 360 / 802
    icone = ('<rect x="4" y="4" width="504" height="504" rx="112" fill="#111" stroke="url(#borda-app)" stroke-width="6"/>'
             + em(round((512 - 536 * esc) / 2, 1), 76, round(esc, 4), simbolo_ouro_simples()))
    arquivos["icone.svg"] = svg("0 0 512 512", icone, DEFS_OURO + borda)
    # favicon: sem moldura clara (em 16 px a borda some), símbolo maior
    esc_f = 440 / 802
    fav = ('<rect width="512" height="512" rx="104" fill="#111"/>'
           + em(round((512 - 536 * esc_f) / 2, 1), 36, round(esc_f, 4), simbolo_ouro_simples()))
    arquivos["favicon.svg"] = svg("0 0 512 512", fav, DEFS_OURO)

    # capas: a composição do logo principal reaproveitada (mesmos elementos, outra escala)
    def logo_sem_fundo():
        return (em(248, 208, s, corpo_c) + em(248, 208, s, simbolo_ouro())
                + em(625, 283, 1, wordmark("#F7F4EE", "#ECE6DA", "#DAD5CB", OURO))
                + '<rect x="1505" y="252" width="2.5" height="320" fill="#A98535"/>' + lema("#E8E2D6", OURO))
    fundo_capa = ('<radialGradient id="fundo" cx="42%" cy="50%" r="75%"><stop offset="0" stop-color="#15130F"/>'
                  '<stop offset=".55" stop-color="#0B0A09"/><stop offset="1" stop-color="#050505"/></radialGradient>')
    # LinkedIn 1584 × 396: os 34% da esquerda ficam livres para a foto de perfil
    url = texto(500, "jeanfelipecr-ds.github.io", 15, 1528, 372, 0.06, "direita")
    linkedin = ('<rect width="1584" height="396" fill="url(#fundo)"/>'
                + '<g transform="translate(411 -41) scale(.6)">' + logo_sem_fundo() + "</g>"
                + f'<path d="{url}" fill="{OURO}" opacity=".85"/>')
    arquivos["capa-linkedin.svg"] = svg("0 0 1584 396", linkedin, DEFS_OURO + grad_c + fundo_capa)
    # WhatsApp 1211 × 681: conteúdo em cima e centralizado; a base fica livre para a foto redonda
    whatsapp = ('<rect width="1211" height="681" fill="url(#fundo)"/>'
                + em(533, 70, 0.27, corpo_c) + em(533, 70, 0.27, simbolo_ouro())
                + em(367, 330, 0.62, wordmark("#F7F4EE", "#ECE6DA", "#DAD5CB", OURO)))
    arquivos["capa-whatsapp.svg"] = svg("0 0 1211 681", whatsapp, DEFS_OURO + grad_c + fundo_capa)
    # prévia de link (og:image) 1200 × 630: o logo principal centralizado na proporção que o LinkedIn não corta
    og = ('<rect width="1200" height="630" fill="url(#fundo)"/>'
          + '<g transform="translate(7.3 93) scale(.6)">' + logo_sem_fundo() + "</g>")
    arquivos["og-imagem.svg"] = svg("0 0 1200 630", og, DEFS_OURO + grad_c + fundo_capa)

    for nome, conteudo in arquivos.items():
        with open(os.path.join(SAIDA, nome), "w", encoding="utf-8") as f:
            f.write(conteudo)
    with open(os.path.join(SAIDA, "tokens.css"), "w", encoding="utf-8") as f:
        f.write(TOKENS)
    print(f"{len(arquivos)} SVG + tokens.css em {SAIDA}")


TOKENS = """/*
  JEAN · Fundação dos Dados — tokens da marca (fonte única)
  Gerado por marca/_fonte/gerar_marca.py — edite lá, não aqui.

  Uso:  <link rel="stylesheet" href="https://jeanfelipecr-ds.github.io/marca/tokens.css">
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">

  Regra: verde/laranja/vermelho só para estado ou meta (período encerrado); o dourado é MARCA,
  nunca status; azul nunca representa atingimento.
*/
:root {
  /* paleta do board */
  --jfc-preto: #0A0A0A;
  --jfc-grafite: #1E1E1E;
  --jfc-ouro: #D4AF37;
  --jfc-areia: #EDE7DA;
  --jfc-branco: #FAFAF8;

  /* ouro em faces (o metal do símbolo) */
  --jfc-ouro-reflexo: #F8D99D;
  --jfc-ouro-claro: #F2CC85;
  --jfc-ouro-medio: #BF8A45;
  --jfc-ouro-sombra: #875925;
  --jfc-ouro-vinco: #4A3116;
  --jfc-ouro-metal: linear-gradient(135deg, #F8D99D 0%, #E2B062 35%, #BF8A45 70%, #875925 100%);

  /* superfícies e texto em fundo escuro */
  --jfc-fundo: #0A0A0A;
  --jfc-superficie: #121110;
  --jfc-linha: #2A2620;
  --jfc-texto: #EDE7DA;
  --jfc-texto-forte: #FAFAF8;
  --jfc-texto-suave: #A9A397;

  /* tipografia: uma família só */
  --jfc-fonte: "Montserrat", system-ui, -apple-system, "Segoe UI", sans-serif;
  --jfc-espaco-titulo: .26em;   /* caixa alta espaçada, como o "FUNDAÇÃO DOS DADOS" */
  --jfc-espaco-rotulo: .2em;

  /* status — só para estado/meta */
  --jfc-ok: #16A34A;
  --jfc-atencao: #F97316;
  --jfc-alerta: #EF4444;
}
"""

if __name__ == "__main__":
    gerar()
