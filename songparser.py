import re
import typing as ty
from dataclasses import dataclass
from sly import Lexer, Parser


tabspec_re = re.compile(r"(?: ([2-9]): )? ([OX0-9]{6}) (?: :([0-4]{6}) )?", re.VERBOSE)

hextuple = ty.Tuple[str, str, str, str, str, str]

@dataclass
class TabSpec:
    fret: ty.Optional[int]
    strings: hextuple
    fingering: ty.Optional[hextuple]


class SongbookLexer(Lexer):
    tokens = {
        BEGIN,
        BEGIN_QUOTE,
        CHORD_PUNCTUATION,
        CLOSE_BRACE,
        CLOSE_BRACKET,
        END,
        END_QUOTE,
        EQUALS,
        GTAB,
        OPEN_BRACE,
        OPEN_BRACKET,
        OPEN_CHORD,
        PUNCTUATION,
        REPEAT_CHORD,
        SPACE,
        TEX_COMMAND,
        WORD,
    }
    
    SPACE = r"[ \t\f\v]+"
    PUNCTUATION = r"[.,:;?!-]"
    CHORD_PUNCTUATION = r"[0-9/#&*]"
    WORD = r"(\w|')+"
    BEGIN_QUOTE = r"``"
    END_QUOTE = r"('')|\""
    
    OPEN_BRACE = r"{"
    CLOSE_BRACE = r"}"
    OPEN_BRACKET = r"\["
    CLOSE_BRACKET = r"\]"
    
    OPEN_CHORD = r"\\\["
    REPEAT_CHORD = r"\^"
    
    BEGIN = r"\\begin"
    END = r"\\end"
    EQUALS = r"="

    TEX_COMMAND = r"\\\w+"
    # see: http://songs.sourceforge.net/songsdoc/songs.html#sec6
    TEX_COMMAND[r"\\gtab"] = GTAB

    @_(tabspec_re.pattern)
    def TAB_SPEC(self, t):
        m = tabspec_re.match(t.value)
        t.value = TabSpec(*m.groups())
        return t

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    def error(self, t):
        print("Illegal character:", t.value[0])
        self.index += 1
        return t
