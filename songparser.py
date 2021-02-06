import re
import typing as ty
from collections import deque
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
        CHORD_SYMBOL,
        COMMAND_NAME,
        END,
        END_QUOTE,
        EQUALS,
        GTAB,
        PUNCTUATION_NO_COMMA,
        REPEAT_CHORD,
        SPACE,
        WORD,
    }
    
    SPACE = r"[ \t\f\v]+"
    PUNCTUATION_NO_COMMA = r"[.:;?!-]"
    CHORD_SYMBOL = r"[0-9/#&*]"
    WORD = r"(\w|')+"
    BEGIN_QUOTE = r"``"
    END_QUOTE = r"('')|\""
    literals = { "{", "}", "[", "]", "\\", ",", "="}
    
    REPEAT_CHORD = r"\^"
    
    BEGIN = r"\\begin"
    END = r"\\end"

    COMMAND_NAME = r"\w+"
    # see: http://songs.sourceforge.net/songsdoc/songs.html#sec6
    COMMAND_NAME[r"gtab"] = GTAB

    ENV_NAME = r"\w+\*?"
    ENV_NAME["song"] = ENV_SONG

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



class SongbookParser(Parser):
    tokens = SongbookLexer.tokens

    @_("BEGIN '{{' ENV_SONG '}}' {{' songtitle '}} [ kv_options ] skip_space body END '{{' ENV_SONG '}}' skip_space")
    def song(self, p):
        return Song(p.songtitle, p.kv_options, p.body)

    @_("body_")
    def body(self, p):
        return list(p.body_)
    
    @_("block skip_space")
    def body_(self, p):
        return deque((p.block,))

    @_("block body_ skip_space"):
    def body_(self, p):
        p.block.appendleft(p.body_)
        return p.block

    @_("BEGIN '{{' ENV_NAME '}}' skip_space body END '{{' ENV_NAME '}}' skip_space")
    def environment(self, p):
        # todo: check matching names
        return Environment(p.ENV_NAME, (), p.body)

    @_("BEGIN '{{' ENV_NAME '}}' '{{' text '}}' skip_space body END '{{' ENV_NAME '}}' skip_space")
    def environment(self, p):
        return Environment(p.ENV_NAME, (p.text,), p.body)

    @_("BEGIN '{{' ENV_NAME '}}' [ environment_options ] skip_space body END '{{' ENV_NAME '}}' skip_space")
    def environment(self, p):
        return Environment(p.ENV_NAME, (p.environment_options,), p.body)

    @_("BEGIN '{{' ENV_NAME '}}' '{{' text '}}' [ environment_options ] skip_space body END '{{' ENV_NAME '}}' skip_space")
    def environment(self, p):
        return Environment(p.ENV_NAME, (p.text, p.environment_options), p.body)

    @_("kv_options skip_space")
    def environment_options(self, p):
        return p

    @_("kv_options_")
    def kv_options(self, p):
        return list(p.kv_options_)

    @_("key_value_pair skip_space")
    def kv_options_(self, p):
        return deque((p.key_value_pair,))

    @_("key_value_pair ',' skip_space kv_options_ skip_space")
    def kv_options_(self, p):
        p.kv_options_.appendleft(p.key_value_pair)
        return p.kv_options_

    @_("COMMAND_NAME skip_space '=' skip_space delimited_text skip_space")
    def key_value_pair(self, p):
        return (p.command_name, p.delimited_text)

    @_("text")
    def environment_options(self, p):
        return p

    @_("text_")
    def text(self, p):
        return list(p.text_)
    
    @_("text_part skip_space")
    def text_(self, p):
        return deque((p[0],))

    @_("text_part text_ skip_space")
    def text_(self, p):
        p.text.appendleft(p[0])
        return p.text_

    @_("WORD", "space", "punctuation", "tex_command")
    def text_part(self, p):
        return p

    @_("'{' text '}' skip_space")
    def delimited_text(self, p):
        return p.text

    @_("'\\' COMMAND_NAME '{' text '}' skip_space")
    def latex_command(self, p):
        return Command(p.COMMAND_NAME, p.text)

    @_("'\\' GTAB chord '{' TAB_SPEC '}' skip_space")
    def gtab_command(self, p):
        return GTab(...) # TODO implement

    @_("REPEAT_CHORD")
    def chord_spec(self, p):
        return p

    @_("'\\' '[' chords ']'")
    def chord_spec(self, p):
        return p

    @_("chords_")
    def chords(p, self):
        return list(p.chords_)
    
    @_("chord")
    def chords_(self, p):
        return deque((p.chord,))

    @_("chord SPACE chords_ skip_space")
    def chords_(self, p):
        p.chords_.appendleft(p.chord)
        return p.chords_

    @_("chord_")
    def chord(self, p):
        return ''.join(p.chord_)
    
    @_("chord_part")
    def chord_(self, p):
        return deque((p.chord_part,))

    @_("chord_part chord")
    def chord_(self, p):
        p.chord_.appendleft(p.chord_part)
        return p.chord_

    @_("WORD", "CHORD_SYMBOL")
    def chord_part(self, p):
        return p

    @_("SPACE")
    def skip_space(self, p):
        pass

    @_("")
    def skip_space(self, p):
        pass

    @_("PUNCTUATION_NO_COMMA", ",")
    def punctuation(self, p):
        return p.value

    
@dataclass
class Song:
    name: str
    options: ty.Mapping[str, str]
    body: ty.List[Block]

@dataclass
class Command:
    name: str
    args: ty.List[Atom]

@dataclass
class Environment:
    name: str
    args: ty.Tuple

@dataclass
class OptionalArg:
    arg: ty.Any

@dataclass
class KVArgs:
    args: ty.Mapping

class ChordWord:
    text: ty.Tuple[ty.Union[str, Chord], ...]

class ChordSpec:
    pass

class RepeatedChord(ChordSpec):
    pass

@dataclass
class Chords(ChordSpec):
    chords: ty.List[Chord]

@dataclass
class Chord:
    content: str # TODO: accidentials, specials...
