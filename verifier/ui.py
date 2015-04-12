import argparse
import os

from .parser import Parser
from .lexer import Lexer
from . import utils
from . import scope
from . import typeinferencer

def dpyast_from_file(infile):
    node = None
    parser = Parser()
    with open(infile, "r") as f:
        source = f.read()
        node = parser.parse(source, infile)

    return node

def dpyfile_to_tla(infile, outfile=None):
    dpyast = dpyast_from_file(infile)
    filename = os.path.basename(infile)

    purename, _, suffix = filename.rpartition(".")
    if len(purename) == 0:
        purename = suffix
        suffix = ""
    if suffix != "da":
        purename = filename

    scopes = scope.ScopeBuilder.run(dpyast)
    typeinferencer.TypeInferencer.run(dpyast)

    print(scopes)

def main():
    """Main entry point when invoking compiler module from command line."""
    ap = argparse.ArgumentParser(description="DistAlgo to tla.")
    ap.add_argument('-o', help="Output file name.", dest="outfile")
    ap.add_argument('infile', help="DistPy input source file.")
    args = ap.parse_args()
    dpyfile_to_tla(args.infile, args.outfile)