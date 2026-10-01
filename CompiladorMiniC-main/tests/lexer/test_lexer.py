"""Pruebas del analizador léxico de Mini C.

Verifica categorías de token, literales, posiciones, reglas de máxima coincidencia,
palabras reservadas, operadores simples y dobles, recuperación con LEX001 y token EOF.
"""

from minic.diagnostics.diagnostic_code import LEX001
from minic.lexer import Lexer, Token, TokenType
from minic.output import format_diagnostic, format_token


def test_empty_source() -> None:
    tokens, diagnostics = Lexer("").scan()
    assert len(diagnostics) == 0
    assert len(tokens) == 1
    assert tokens[0] == Token(TokenType.EOF, "", None, 1, 1)


def test_skill_section_7_case_1() -> None:
    source = "int2 = 12abc;\nwhilex == -5"
    tokens, diagnostics = Lexer(source).scan()
    assert len(diagnostics) == 0

    expected_formatted = [
        "IDENTIFIER 'int2' 1 1",
        "ASSIGN '=' 1 6",
        "INTEGER_LITERAL '12' 1 8",
        "IDENTIFIER 'abc' 1 10",
        "SEMICOLON ';' 1 13",
        "IDENTIFIER 'whilex' 2 1",
        "EQUAL_EQUAL '==' 2 8",
        "MINUS '-' 2 11",
        "INTEGER_LITERAL '5' 2 12",
        "EOF '' 2 13",
    ]
    actual_formatted = [format_token(t) for t in tokens]
    assert actual_formatted == expected_formatted

    # Verificar literales enteros específicos
    assert tokens[2].literal == 12
    assert tokens[8].literal == 5


def test_skill_section_7_case_2_with_errors() -> None:
    source = "int x = @;\nx ! = 0; // fin"
    tokens, diagnostics = Lexer(source).scan()

    expected_tokens = [
        "KW_INT 'int' 1 1",
        "IDENTIFIER 'x' 1 5",
        "ASSIGN '=' 1 7",
        "SEMICOLON ';' 1 10",
        "IDENTIFIER 'x' 2 1",
        "ASSIGN '=' 2 5",
        "INTEGER_LITERAL '0' 2 7",
        "SEMICOLON ';' 2 8",
        "IDENTIFIER 'fin' 2 13",
        "EOF '' 2 16",
    ]
    expected_diagnostics = [
        "LEX001 error 1:9 Carácter no reconocido: '@'",
        "LEX001 error 2:3 Carácter no reconocido: '!'",
        "LEX001 error 2:10 Carácter no reconocido: '/'",
        "LEX001 error 2:11 Carácter no reconocido: '/'",
    ]

    assert [format_token(t) for t in tokens] == expected_tokens
    assert [format_diagnostic(d) for d in diagnostics] == expected_diagnostics


def test_keywords_and_identifiers() -> None:
    source = "int while int_var while1 _ident IDENTIFIER"
    tokens, diagnostics = Lexer(source).scan()
    assert len(diagnostics) == 0

    types = [t.type for t in tokens]
    assert types == [
        TokenType.KW_INT,
        TokenType.KW_WHILE,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.EOF,
    ]


def test_all_operators_and_symbols() -> None:
    source = "== != = + - ( ) { } ;"
    tokens, diagnostics = Lexer(source).scan()
    assert len(diagnostics) == 0

    types = [t.type for t in tokens]
    assert types == [
        TokenType.EQUAL_EQUAL,
        TokenType.NOT_EQUAL,
        TokenType.ASSIGN,
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]


def test_integer_literals_and_leading_zeros() -> None:
    source = "0 007 12345678901234567890"
    tokens, diagnostics = Lexer(source).scan()
    assert len(diagnostics) == 0

    assert tokens[0].literal == 0
    assert tokens[0].lexeme == "0"
    assert tokens[1].literal == 7
    assert tokens[1].lexeme == "007"
    assert tokens[2].literal == 12345678901234567890


def test_position_tracking_tabs_and_cr() -> None:
    # \t cuenta como 1 columna, \r suelto es 1 columna, \n reinicia columna
    source = "a\tb\r\nc\rd"
    tokens, diagnostics = Lexer(source).scan()
    assert len(diagnostics) == 0

    # 'a' en 1:1, '\t' col 2, 'b' col 3, '\r' col 4, '\n' -> línea 2 col 1
    # 'c' en 2:1, '\r' col 2, 'd' col 3
    # EOF en 2:4
    positions = [(t.lexeme, t.line, t.column) for t in tokens]
    assert positions == [
        ("a", 1, 1),
        ("b", 1, 3),
        ("c", 2, 1),
        ("d", 2, 3),
        ("", 2, 4),
    ]


def test_unrecognized_characters_recovery() -> None:
    source = "$#&"
    tokens, diagnostics = Lexer(source).scan()
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF
    assert len(diagnostics) == 3
    for d in diagnostics:
        assert d.code == LEX001
        assert d.severity == "error"
