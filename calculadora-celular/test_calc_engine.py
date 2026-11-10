import unittest
from decimal import Decimal

from calc_engine import Calculator, CalcError, display, evaluate, format_number


def calc(expr):
    return format_number(evaluate(expr))


def press(keys):
    c = Calculator()
    for k in keys:
        if k.isdigit():
            c.press_digit(k)
        elif k == ",":
            c.press_decimal()
        elif k == "%":
            c.press_percent()
        elif k == "=":
            c.equals()
        elif k == "±":
            c.press_sign()
        elif k == "<":
            c.backspace()
        else:
            c.press_operator(k)
    return c


class PercentPhoneStyle(unittest.TestCase):
    def test_exemplos_do_usuario(self):
        self.assertEqual(calc("100+158%"), "258")
        self.assertEqual(calc("100+110%"), "210")

    def test_subtracao(self):
        self.assertEqual(calc("200-10%"), "180")
        self.assertEqual(calc("100-150%"), "-50")

    def test_multiplicacao_e_divisao(self):
        self.assertEqual(calc("200*10%"), "20")
        self.assertEqual(calc("50/10%"), "500")

    def test_porcentagem_sozinha(self):
        self.assertEqual(calc("25%"), "0,25")

    def test_encadeado(self):
        self.assertEqual(calc("100+10%+10%"), "121")
        self.assertEqual(calc("100+10%-10%"), "99")

    def test_prioridade(self):
        self.assertEqual(calc("2+3*4"), "14")
        self.assertEqual(calc("100+50*10%"), "105")
        self.assertEqual(calc("10+20/4"), "15")

    def test_decimais_sem_erro_de_float(self):
        self.assertEqual(calc("0,1+0,2"), "0,3")
        self.assertEqual(calc("1/3"), "0,3333333333")
        self.assertEqual(calc("19,90+15%"), "22,885")

    def test_negativos(self):
        self.assertEqual(calc("5*-2"), "-10")
        self.assertEqual(calc("-5+10"), "5")

    def test_divisao_por_zero(self):
        with self.assertRaises(CalcError):
            evaluate("5/0")


class Formatting(unittest.TestCase):
    def test_milhar(self):
        self.assertEqual(format_number(Decimal("1234567.5")), "1.234.567,5")
        self.assertEqual(format_number(Decimal("-0")), "0")

    def test_display(self):
        self.assertEqual(display("1000+158%"), "1.000 + 158%")
        self.assertEqual(display("5×−2"), "5 × −2")


class Buttons(unittest.TestCase):
    def test_fluxo_do_usuario(self):
        c = press("100+158%")
        self.assertEqual(c.preview(), "258")
        self.assertEqual(c.equals(), "258")

    def test_continuar_apos_igual(self):
        c = press("100+10%=+10%=")
        self.assertEqual(c.expr, "121")

    def test_digito_apos_igual_comeca_novo(self):
        c = press("2+2=7")
        self.assertEqual(c.expr, "7")

    def test_troca_operador(self):
        self.assertEqual(press("5+×3").expr, "5×3")
        self.assertEqual(press("5×-3").expr, "5×−3")

    def test_zero_a_esquerda_e_virgula(self):
        self.assertEqual(press("007").expr, "7")
        self.assertEqual(press(",5,5").expr, "0,55")

    def test_sinal(self):
        self.assertEqual(press("100+5±").expr, "100+−5")
        self.assertEqual(press("100+5±±").expr, "100+5")
        self.assertEqual(press("8±").expr, "−8")

    def test_backspace(self):
        self.assertEqual(press("123<").expr, "12")

    def test_erro(self):
        c = press("5/0")
        self.assertEqual(c.equals(), "Erro")


class ExtraKeys(unittest.TestCase):
    def test_ce(self):
        c = press("100+58")
        c.clear_entry()
        self.assertEqual(c.expr, "100+")

    def test_funcoes(self):
        c = press("9")
        c.apply_function("sqrt")
        self.assertEqual(c.expr, "3")
        c = press("100+4")
        c.apply_function("sqr")
        self.assertEqual(c.expr, "100+16")
        c = press("4")
        c.apply_function("inv")
        self.assertEqual(c.expr, "0,25")
        c = press("0")
        self.assertFalse(c.apply_function("inv"))

    def test_memoria(self):
        c = press("100+158%")
        self.assertEqual(c.current_value(), Decimal(258))
        c = press("5+")
        c.insert_value(Decimal(258))
        self.assertEqual(c.expr, "5+258")


if __name__ == "__main__":
    unittest.main()
