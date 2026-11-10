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

Também tem: prévia do resultado enquanto você digita, vírgula como decimal,
pontos de milhar, histórico, botão ± e atalhos de teclado
(números, `+ - * /`, `%`, `Enter` = igual, `Backspace` apaga, `Esc` limpa).

## Baixar o .exe

1. Abra a aba **Actions** do repositório e entre no último run de **Calculadora Windows**.
2. Em **Artifacts**, baixe **Calculadora-Windows** e descompacte.
3. Dê dois cliques em `Calculadora.exe` (não precisa instalar Python).

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
pip install pyinstaller
pyinstaller --onefile --windowed --name Calculadora calculadora.py
```

O arquivo fica em `dist\Calculadora.exe`.
