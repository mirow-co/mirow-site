# Fontes dos logos de clientes (onda 5 — 2026-07-30)

Arquivos baixados por `tools_onda5/00_baixar_logos.py` para
`public/wp-content/uploads/2026/07/clientes/`.

Preferência: SVG do Wikimedia Commons; quando não havia, site oficial / RI da empresa.
Todos os arquivos SVG passam por uma normalização idempotente que garante
`width`/`height` numéricos no elemento `<svg>` raiz — sem isso o `<img>` renderiza
0×0 dentro do container flex da barra (caso real: Volkswagen, Energisa, Yara, Wilson Sons).

| Cliente | Arquivo | Fonte (URL do original) | Tipo |
|---|---|---|---|
| Mercedes-Benz | `mercedes-benz.svg` | https://upload.wikimedia.org/wikipedia/commons/9/9e/Mercedes-Benz_Logo_2010.svg (Commons, `File:Mercedes-Benz Logo 2010.svg`) | SVG |
| Volkswagen | `volkswagen.svg` | https://upload.wikimedia.org/wikipedia/commons/6/6d/Volkswagen_logo_2019.svg (Commons, `File:Volkswagen logo 2019.svg`) | SVG |
| Ipiranga | `ipiranga.svg` | https://upload.wikimedia.org/wikipedia/commons/3/38/Ipiranga_logo_%282023%29.svg (Commons, `File:Ipiranga logo (2023).svg`) | SVG |
| Suzano | `suzano.svg` | https://upload.wikimedia.org/wikipedia/commons/4/42/Logotipo_da_Suzano_%282019%29.svg (Commons, `File:Logotipo da Suzano (2019).svg`) | SVG |
| Klabin | `klabin.svg` | https://upload.wikimedia.org/wikipedia/commons/1/10/Klabin.svg (Commons, `File:Klabin.svg`) | SVG |
| Dexco | `dexco.svg` | https://upload.wikimedia.org/wikipedia/commons/c/c4/Logotipo_da_Dexco.svg (Commons, `File:Logotipo da Dexco.svg`) | SVG |
| EDP | `edp.svg` | https://upload.wikimedia.org/wikipedia/commons/d/d2/EDP_2022.svg (Commons, `File:EDP 2022.svg`) | SVG |
| Energisa | `energisa.svg` | https://upload.wikimedia.org/wikipedia/commons/8/89/Energisa.svg (Commons, `File:Energisa.svg`) | SVG |
| Eneva | `eneva.svg` | https://upload.wikimedia.org/wikipedia/commons/7/73/Logotipo_da_Eneva.svg (Commons, `File:Logotipo da Eneva.svg`) | SVG |
| Taesa | `taesa.png` | https://ri.taesa.com.br/wp-content/themes/ri-taesa/imgs/logo-taesa.png (site de RI da própria Taesa — não há SVG no Commons) | PNG 400×147 |
| Yara | `yara.svg` | https://upload.wikimedia.org/wikipedia/commons/4/42/Yara_logo.svg (Commons, `File:Yara logo.svg`) | SVG |
| Wilson Sons | `wilson-sons.svg` | https://wilsonsons.com.br/wp-content/themes/wilsonsons_2021/assets/images/logo.svg (site oficial — não há arquivo no Commons) | SVG |
| Santos Brasil | `santos-brasil.jpg` | https://upload.wikimedia.org/wikipedia/commons/c/c3/Logo_da_Santos_Brasil.jpg (Commons, `File:Logo da Santos Brasil.jpg`) | JPG 666×504, fundo branco |
| XP Inc. | `xp.svg` | https://upload.wikimedia.org/wikipedia/commons/b/b2/XP_Inc._Logo.svg (Commons, `File:XP Inc. Logo.svg`) | SVG |
| SulAmérica | `sulamerica.svg` | https://upload.wikimedia.org/wikipedia/commons/0/01/Logotipo_da_SulAm%C3%A9rica.svg (Commons, `File:Logotipo da SulAmérica.svg`) | SVG |

## Observações

- **Santos Brasil** é o único arquivo raster com fundo branco. Na barra isso é
  invisível porque a faixa tem fundo branco (`#ffffff`) — se algum dia a faixa mudar
  de cor, trocar por um SVG/PNG transparente.
- **Taesa** só existe como PNG (o Commons não tem o logo da transmissora — os
  resultados de busca são da extinta companhia aérea mexicana homônima).
- Todos os logos são marcas registradas dos respectivos titulares; entram aqui como
  referência a clientes atendidos. A lista de 15 é a definida pelo Mario em 30/07/2026.
