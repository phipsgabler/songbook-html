#! /usr/bin/env python3

import errno
import sys
from songparser import SongbookLexer

if __name__ == "__main__":
    lexer = SongbookLexer()
    song = sys.stdin.read()
    # print(song)
    try: 
        for token in lexer.tokenize(song):
            sys.stdout.write(str(token))
            sys.stdout.write("\n")
    except IOError as e:
        # fix output pipe signal error, see: https://stackoverflow.com/a/14208261/1346276
        if e.errno == errno.EPIPE:
            sys.exit(0)
