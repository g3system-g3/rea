"""Motor da calculadora com porcentagem no estilo de celular.

Regras de porcentagem (iguais às calculadoras de Android/iPhone):

    A + B%  ->  A + (A * B / 100)      ex.: 100 + 158% = 258
    A - B%  ->  A - (A * B / 100)      ex.: 200 - 10%  = 180
    A x B%  ->  A * (B / 100)          ex.: 200 x 10%  = 20
    A / B%  ->  A / (B / 100)          ex.: 50 / 10%   = 500
    B%      ->  B / 100                ex.: 25%        = 0,25

Em contas encadeadas, o "A" de uma soma/subtração é tudo o que vem antes:
100 + 10% + 10% = 121.  Multiplicação e divisão têm prioridade sobre soma e
subtração, como no celular.  As contas usam Decimal para evitar erros como
0,1 + 0,2 = 0,30000000000000004.
"""

from __future__ import annotations

from decimal import Decimal, DivisionByZero, InvalidOperation, getcontext

getcontext().prec = 34

PLUS = "+"
MINUS = "−"  # sinal de menos tipográfico, usado na tela
TIMES = "×"
DIVIDE = "÷"
PERCENT = "%"
DECIMAL_SEP = ","

BINARY_OPS = (PLUS, MINUS, TIMES, DIVIDE)
# Aceita também os sinais ASCII, para facilitar testes e digitação.
_OP_ALIASES = {"+": PLUS, "-": MINUS, "*": TIMES, "x": TIMES, "/": DIVIDE}


class CalcError(Exception):
    """Conta inválida (ex.: divisão por zero)."""


# --------------------------------------------------------------------------
# Tokenização
# --------------------------------------------------------------------------

def tokenize(expr: str) -> list:
    """Transforma '100+158%' em [Decimal(100), '+', Decimal(158), '%']."""
    tokens: list = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or ch in ",.":
            j = i
            while j < n and (expr[j].isdigit() or expr[j] in ",."):
                j += 1
            raw = expr[i:j].replace(".", "").replace(",", ".") if "," in expr[i:j] else expr[i:j]
            if raw in ("", "."):
                raw = "0"
            if raw.endswith("."):
                raw += "0"
            if raw.startswith("."):
                raw = "0" + raw
            try:
                tokens.append(Decimal(raw))
            except InvalidOperation as exc:
                raise CalcError(f"número inválido: {expr[i:j]}") from exc
            i = j
            continue
        if ch == PERCENT:
            tokens.append(PERCENT)
            i += 1
            continue
        op = _OP_ALIASES.get(ch, ch)
        if op in BINARY_OPS:
            tokens.append(op)
            i += 1
            continue
        raise CalcError(f"caractere inválido: {ch}")
    return tokens


# --------------------------------------------------------------------------
# Avaliação (descida recursiva)
#   expr   := term ((+|−) term)*
#   term   := factor ((×|÷) factor)*
#   factor := (−)* número (%)?
# --------------------------------------------------------------------------

class _Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self) -> Decimal:
        if not self.tokens:
            return Decimal(0)
        value = self.expr()
        if self.peek() is not None:
            raise CalcError("conta incompleta")
        return value

    def expr(self) -> Decimal:
        left, _ = self.term()
        while self.peek() in (PLUS, MINUS):
            op = self.take()
            right, pct = self.term()
            if pct is not None:
                # Estilo celular: A ± B%  =  A ± A*B/100
                right = left * pct / 100
            left = left + right if op == PLUS else left - right
        return left

    def term(self):
        """Retorna (valor, pct) — pct é o B de um termo que é só 'B%'."""
        value, pct = self.factor()
        while self.peek() in (TIMES, DIVIDE):
            op = self.take()
            right, _ = self.factor()
            pct = None
            try:
                value = value * right if op == TIMES else value / right
            except (DivisionByZero, InvalidOperation) as exc:
                raise CalcError("não é possível dividir por zero") from exc
        return value, pct

    def factor(self):
        sign = 1
        while self.peek() == MINUS:
            self.take()
            sign = -sign
        tok = self.take()
        if not isinstance(tok, Decimal):
            raise CalcError("conta incompleta")
        number = tok * sign
        if self.peek() == PERCENT:
            self.take()
            return number / 100, number
        return number, None


def evaluate(expr: str) -> Decimal:
    """Calcula a expressão e devolve um Decimal. Lança CalcError se inválida."""
    return _Parser(tokenize(expr)).parse()


def trim_incomplete(expr: str) -> str:
    """Remove operadores pendurados no fim ('100+' -> '100') para a prévia."""
    while expr and (expr[-1] in BINARY_OPS or expr[-1] in "+-*/x"):
        expr = expr[:-1]
    return expr


# --------------------------------------------------------------------------
# Formatação no padrão brasileiro: 1.234.567,89
# --------------------------------------------------------------------------

def format_number(value: Decimal, max_decimals: int = 10) -> str:
    if value.is_nan() or value.is_infinite():
        return "Erro"
    q = Decimal(1).scaleb(-max_decimals)
    value = value.quantize(q) if abs(value) < Decimal("1e20") else value
    if abs(value) >= Decimal("1e16"):
        mant, exp = f"{value:.8e}".split("e")
        mant = mant.rstrip("0").rstrip(".").replace(".", DECIMAL_SEP)
        return f"{mant}e{int(exp)}"
    sign = "-" if value < 0 else ""
    text = f"{abs(value):f}"
    if "." in text:
        int_part, frac = text.split(".")
        frac = frac.rstrip("0")
    else:
        int_part, frac = text, ""
    groups = []
    while len(int_part) > 3:
        groups.insert(0, int_part[-3:])
        int_part = int_part[:-3]
    groups.insert(0, int_part)
    result = ".".join(groups)
    if frac:
        result += DECIMAL_SEP + frac
    if result == "0":
        sign = ""
    return sign + result


def to_input(value: Decimal) -> str:
    """Converte um resultado para texto editável (sem separador de milhar)."""
    return format_number(value).replace(".", "")


# --------------------------------------------------------------------------
# Estado da tela (lógica dos botões, sem interface gráfica)
# --------------------------------------------------------------------------

class Calculator:
    def __init__(self):
        self.expr = ""
        self.just_evaluated = False
        self.history: list[tuple[str, str]] = []

    # --- utilidades ---
    def _last_number_start(self) -> int:
        i = len(self.expr)
        while i > 0 and (self.expr[i - 1].isdigit() or self.expr[i - 1] == DECIMAL_SEP):
            i -= 1
        return i

    def _ends_with_number(self) -> bool:
        return bool(self.expr) and (self.expr[-1].isdigit() or self.expr[-1] == DECIMAL_SEP)

    # --- botões ---
    def press_digit(self, d: str):
        if self.just_evaluated:
            self.expr = ""
            self.just_evaluated = False
        if self.expr.endswith(PERCENT):
            self.expr += TIMES
        start = self._last_number_start()
        current = self.expr[start:]
        if current == "0":
            self.expr = self.expr[:start] + d  # evita "007"
        elif len(current.replace(DECIMAL_SEP, "")) < 15:
            self.expr += d

    def press_decimal(self):
        if self.just_evaluated:
            self.expr = ""
            self.just_evaluated = False
        if self.expr.endswith(PERCENT):
            self.expr += TIMES
        start = self._last_number_start()
        current = self.expr[start:]
        if DECIMAL_SEP in current:
            return
        self.expr += "0," if current == "" else DECIMAL_SEP

    def press_operator(self, op: str):
        op = _OP_ALIASES.get(op, op)
        self.just_evaluated = False
        if not self.expr:
            if op == MINUS:
                self.expr = MINUS
            return
        last = self.expr[-1]
        if last in BINARY_OPS:
            if op == MINUS and last in (TIMES, DIVIDE):
                self.expr += MINUS  # permite 5×−2
                return
            # troca o operador anterior (e um eventual "−" unário)
            self.expr = self.expr.rstrip("".join(BINARY_OPS))
            if not self.expr:
                if op == MINUS:
                    self.expr = MINUS
                return
        if self.expr.endswith(DECIMAL_SEP):
            self.expr = self.expr[:-1]
        self.expr += op

    def press_percent(self):
        self.just_evaluated = False
        if self._ends_with_number():
            if self.expr.endswith(DECIMAL_SEP):
                self.expr = self.expr[:-1]
            self.expr += PERCENT

    def press_sign(self):
        """Botão ±: troca o sinal do número atual."""
        self.just_evaluated = False
        end = len(self.expr)
        if self.expr.endswith(PERCENT):
            end -= 1
        i = end
        while i > 0 and (self.expr[i - 1].isdigit() or self.expr[i - 1] == DECIMAL_SEP):
            i -= 1
        has_unary = i > 0 and self.expr[i - 1] == MINUS and (i == 1 or self.expr[i - 2] in BINARY_OPS)
        if has_unary:
            self.expr = self.expr[: i - 1] + self.expr[i:]
        elif i == end and self.expr and self.expr[-1] not in BINARY_OPS:
            return  # nada para inverter
        else:
            self.expr = self.expr[:i] + MINUS + self.expr[i:]

    def backspace(self):
        if self.just_evaluated:
            self.just_evaluated = False
        self.expr = self.expr[:-1]

    def clear(self):
        self.expr = ""
        self.just_evaluated = False

    def clear_entry(self):
        """CE: apaga só o número que está sendo digitado."""
        if self.just_evaluated:
            self.clear()
            return
        end = len(self.expr)
        if self.expr.endswith(PERCENT):
            end -= 1
        i = self._number_start_before(end)
        if i > 0 and self.expr[i - 1] == MINUS and (i == 1 or self.expr[i - 2] in BINARY_OPS):
            i -= 1
        self.expr = self.expr[:i]

    def _number_start_before(self, end: int) -> int:
        i = end
        while i > 0 and (self.expr[i - 1].isdigit() or self.expr[i - 1] == DECIMAL_SEP):
            i -= 1
        return i

    def _current_number_span(self):
        """(início, fim) do último número, incluindo '−' unário e '%'."""
        end = len(self.expr)
        if self.expr.endswith(PERCENT):
            end -= 1
        start = self._number_start_before(end)
        if start == end:
            return None
        if start > 0 and self.expr[start - 1] == MINUS and (start == 1 or self.expr[start - 2] in BINARY_OPS):
            start -= 1
        return start, len(self.expr)

    def apply_function(self, name: str) -> bool:
        """Aplica 1/x, x² ou √x ao número atual. Retorna False se der erro."""
        span = self._current_number_span()
        if span is None:
            return True
        start, end = span
        piece = self.expr[start:end]
        # após "=", ou com um número só na tela, aplica sobre o valor inteiro
        if self.just_evaluated or start == 0:
            piece, start = self.expr, 0
        try:
            value = evaluate(piece)
            if name == "inv":
                if value == 0:
                    return False
                result = 1 / value
            elif name == "sqr":
                result = value * value
            elif name == "sqrt":
                if value < 0:
                    return False
                result = value.sqrt()
            else:
                raise ValueError(name)
        except CalcError:
            return False
        self.expr = self.expr[:start] + to_input(result).replace("-", MINUS)
        return True

    def current_value(self) -> Decimal:
        """Valor que está na tela (para a memória)."""
        try:
            return evaluate(trim_incomplete(self.expr)) if self.expr else Decimal(0)
        except CalcError:
            return Decimal(0)

    def insert_value(self, value: Decimal):
        """Coloca um valor (ex.: da memória) como número atual."""
        text = to_input(value).replace("-", MINUS)
        if self.just_evaluated or not self.expr:
            self.expr = text
            self.just_evaluated = True
            return
        span = self._current_number_span()
        if span is not None:
            self.expr = self.expr[: span[0]]
        if self.expr.endswith(PERCENT):
            self.expr += TIMES
        self.expr += text

    def preview(self) -> str:
        """Resultado ao vivo mostrado abaixo da conta (como no celular)."""
        expr = trim_incomplete(self.expr)
        if not expr or not any(c in expr[1:] for c in (*BINARY_OPS, PERCENT)):
            return ""
        try:
            return format_number(evaluate(expr))
        except CalcError:
            return ""

    def equals(self) -> str:
        expr = trim_incomplete(self.expr)
        if not expr:
            return ""
        try:
            result = evaluate(expr)
        except CalcError:
            return "Erro"
        shown = format_number(result)
        self.history.append((display(expr), shown))
        self.expr = to_input(result).replace("-", MINUS)
        self.just_evaluated = True
        return shown


def display(expr: str) -> str:
    """Formata a conta para a tela, com pontos de milhar e espaços."""
    out = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isdigit() or ch == DECIMAL_SEP:
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == DECIMAL_SEP):
                j += 1
            num = expr[i:j]
            int_part, sep, frac = num.partition(DECIMAL_SEP)
            groups = []
            while len(int_part) > 3:
                groups.insert(0, int_part[-3:])
                int_part = int_part[:-3]
            groups.insert(0, int_part)
            out.append(".".join(groups) + sep + frac)
            i = j
            continue
        unary = ch == MINUS and (i == 0 or expr[i - 1] in BINARY_OPS)
        out.append(ch if unary or ch == PERCENT else f" {ch} ")
        i += 1
    return "".join(out)
