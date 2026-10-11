# Marca — JEAN · Fundação dos Dados

Kit da identidade visual. Tudo nesta pasta é **gerado**: a fonte única é `_fonte/gerar_marca.py`.

Folha da marca: <https://jeanfelipecr-ds.github.io/marca/>

## Por que um gerador

A identidade anterior tinha a paleta copiada à mão em vários lugares (site, capas, skill de carrossel, demos), e cada cópia foi se desviando. Agora existe **uma** geometria do símbolo, **um** dourado e **um** wordmark. Mudou algo? Edita o gerador e roda de novo. Não se edita SVG à mão.

## Arquivos

| Arquivo | Uso |
|---|---|
| `tokens.css` | cores e fonte — importar em qualquer página da marca |
| `logo-principal.svg` / `.png` | logo completo do board (construção + wordmark + lema), fundo escuro |
| `logo-escuro.svg`, `logo-claro.svg`, `logo-mono-preto.svg`, `logo-mono-branco.svg` | assinatura compacta (símbolo + JEAN + Fundação dos Dados + serviço) |
| `simbolo-ouro.svg` | símbolo 3D em ouro, para fundo escuro |
| `simbolo-claro.svg`, `simbolo-mono-*.svg` | símbolo plano |
| `simbolo-construcao.svg` | símbolo com as linhas de construção |
| `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png`, `icone.svg`, `icone-512.png` | ícones |
| `capa-linkedin.png` (1584×396), `capa-whatsapp.png` (1211×681) | capas de perfil |

## Gerar

```bash
python marca/_fonte/gerar_marca.py                                   # SVG + tokens.css
powershell -ExecutionPolicy Bypass -File marca/_fonte/renderizar.ps1  # PNG
```

O gerador precisa de `fontTools` e baixa a Montserrat (licença OFL) para `_fonte/fontes/` quando ela não está lá. Essa pasta fica fora do git.

## Armadilhas

- **O texto é curva, não fonte.** O "JEAN" é Montserrat SemiBold com cada letra encaixada na largura medida no board aprovado, que usa a Montserrat alargada. Por isso os SVGs não dependem de fonte instalada. Em compensação, trocar uma palavra exige rodar o gerador.
- **As linhas de construção não são decoração.** Cada linha sai de uma aresta ou vértice real do símbolo, e por isso ficam retas e presas ao desenho. Não se reposiciona linha "no olho".
- **O dourado é marca, não status.** Verde, laranja e vermelho servem só para meta ou estado. Azul nunca indica atingimento.
- **Favicon pequeno não leva filtro.** Abaixo de ~64 px, sombra e textura viram borrão, e por isso `favicon.svg` e `icone.svg` usam o ouro em faces sem filtros.
