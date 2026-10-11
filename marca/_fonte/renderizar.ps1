# Gera os PNG da marca a partir dos SVG (rodar depois de gerar_marca.py).
# Edge headless com Start-Process -Wait: o operador "&" não espera o Edge e o PNG sai vazio.
param([string]$Raiz = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)))

$edge = @("C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
          "C:\Program Files\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1

function Foto([string]$Html, [string]$Png, [string]$Tam, [string]$Escala = "1", [switch]$Transparente) {
  $perfil = Join-Path $env:TEMP ("edge-marca-" + [guid]::NewGuid())
  $a = @("--headless=new","--disable-gpu","--no-sandbox","--hide-scrollbars","--user-data-dir=$perfil",
         "--force-device-scale-factor=$Escala","--window-size=$Tam","--virtual-time-budget=8000","--screenshot=$Png")
  if ($Transparente) { $a += "--default-background-color=00000000" }
  $a += $Html
  Start-Process -FilePath $edge -ArgumentList $a -Wait -NoNewWindow -RedirectStandardError (Join-Path $env:TEMP "edge-marca-err.txt")
  Remove-Item -Recurse -Force $perfil -ErrorAction SilentlyContinue
  "{0,-28} {1}" -f (Split-Path -Leaf $Png), $(if (Test-Path $Png) { "ok" } else { "FALHOU" })
}

# página mínima que mostra um SVG ocupando a janela inteira
function Pagina([string]$Svg, [string]$Fundo = "transparent") {
  $tmp = Join-Path $env:TEMP ("marca-" + [IO.Path]::GetFileNameWithoutExtension($Svg) + ".html")
  "<!doctype html><html><body style='margin:0;background:$Fundo'><img src='file:///$($Svg.Replace('\','/'))' style='width:100vw;height:100vh;object-fit:contain;display:block'></body></html>" |
    Set-Content -Path $tmp -Encoding UTF8
  $tmp
}

$m = $Raiz
# Ícones: o Edge headless não abre janela com menos de ~500 px (a imagem sai cortada).
# Renderiza em 512 e reduz com o Pillow no fim (a redução LANCZOS também fica mais nítida).
Foto (Pagina "$m\favicon.svg") "$m\favicon-512.png" "512,512" -Transparente
Foto (Pagina "$m\icone.svg") "$m\icone-512.png" "512,512" -Transparente
Foto (Pagina "$m\simbolo-ouro.svg") "$m\simbolo-ouro.png" "576,842" "2" -Transparente
Foto (Pagina "$m\logo-principal.svg") "$m\logo-principal.png" "1907,760" "2"
Foto (Pagina "$m\logo-escuro.svg" "#0A0A0A") "$m\logo-escuro.png" "1188,510" "2"
Foto (Pagina "$m\logo-claro.svg" "#F7F5F0") "$m\logo-claro.png" "1188,510" "2"
Foto (Pagina "$m\capa-linkedin.svg") "$m\capa-linkedin.png" "1584,396"
Foto (Pagina "$m\capa-whatsapp.svg") "$m\capa-whatsapp.png" "1211,681"
Foto (Pagina "$m\og-imagem.svg") "$m\og-imagem.png" "1200,630"
Foto "$m\index.html" "$m\folha-marca.png" "1920,1440"

py -I -c "from PIL import Image; Image.open(r'$m\favicon-512.png').resize((32,32), Image.LANCZOS).save(r'$m\favicon-32.png'); Image.open(r'$m\icone-512.png').resize((180,180), Image.LANCZOS).save(r'$m\apple-touch-icon.png')"
Remove-Item "$m\favicon-512.png"
"favicon-32.png e apple-touch-icon.png reduzidos a partir de 512 px"
