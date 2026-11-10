# Calculadora estilo celular (Windows)

Calculadora para Windows que faz porcentagem igual ao celular.

| Conta        | Resultado | Como é calculado        |
|--------------|-----------|-------------------------|
| 100 + 158%   | 258       | 100 + 100 × 158 / 100   |
| 100 + 110%   | 210       | 100 + 100 × 110 / 100   |
| 200 − 10%    | 180       | 200 − 200 × 10 / 100    |
| 200 × 10%    | 20        | 200 × 10 / 100          |
| 50 ÷ 10%     | 500       | 50 ÷ (10 / 100)         |
| 100 + 10% + 10% | 121    | cada % vale sobre o total até ali |

Visual igual ao da calculadora do Windows 11 (tema claro ou escuro, seguindo o
Windows), com memória (MC, MR, M+, M−, MS), CE, 1/x, x², √x, histórico ao lado
quando a janela fica larga e atalhos de teclado (números, `+ - * /`, `%`,
`Enter` = igual, `Backspace` apaga, `Esc` limpa, `Delete` = CE).

## Instalar no Windows

1. Abra a aba **Actions** do repositório e entre no último run verde de **Calculadora Windows**.
2. Em **Artifacts**, baixe **Calculadora-Windows** e descompacte.
3. Rode `Instalar-Calculadora.exe`. Ele cria o atalho **Calculadora G3** na área de
   trabalho e no menu Iniciar (não pede senha de administrador). Para remover, use
   *Configurações → Aplicativos*.

Se preferir não instalar, o `Calculadora.exe` do mesmo pacote abre direto.
Na primeira vez o Windows SmartScreen pode avisar que o app é desconhecido:
clique em **Mais informações → Executar assim mesmo**.

## Rodar pelo código

Precisa do Python 3.10+ instalado (o Tkinter já vem junto no Windows).

```bat
cd calculadora-celular
python calculadora.py
```

Testes: `python -m unittest -v`

Gerar o .exe localmente:

```bat
pip install pyinstaller pillow
python make_icon.py
pyinstaller --onefile --windowed --name Calculadora --icon icon.ico --add-data "icon.ico;." calculadora.py
iscc instalador.iss
```

Os arquivos ficam em `dist\` (precisa do [Inno Setup 6](https://jrsoftware.org/isinfo.php) para o instalador).
