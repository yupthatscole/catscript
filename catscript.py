"""
catscript runner.

    python catscript.py program.meow
"""

import sys

from lexer import tokenize, CatError
from parser import parse
from interpreter import Interpreter

HAPPY_CAT = r"""
   /\_/\
  ( ^.^ )  purr. it worked.
   > ^ <
"""

ANGRY_CAT = r"""
   /\_/\
  ( >.< )  HISS.
   > ^ <
"""

SLEEPY_CAT = r"""
   /\_/\
  ( -.- )  zzz... you woke me up.
   > ^ <
"""


def main():
    if len(sys.argv) < 2:
        print("usage: python catscript.py program.meow")
        sys.exit(1)

    path = sys.argv[1]
    if not path.endswith(".meow"):
        print("\n  HISS-415: catscript only eats .meow files\n")
        sys.exit(1)

    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"\n  HISS-404: couldn't find '{path}'. did the cat knock it off the desk?\n")
        sys.exit(1)

    sys.setrecursionlimit(4000)

    try:
        tree = parse(tokenize(source))
        Interpreter().run(tree)
    except CatError as e:
        print(e)
        print(ANGRY_CAT)
        sys.exit(1)
    except RecursionError:
        print("\n  HISS-508: your cat is chasing its tail (a hunt called itself forever)\n")
        print(ANGRY_CAT)
        sys.exit(1)
    except KeyboardInterrupt:
        print(SLEEPY_CAT)
        sys.exit(130)
    except Exception as e:
        # a bug in catscript itself, not in the .meow file
        print(f"\n  HISS-999: catscript tripped over its own tail. this one's not your fault.")
        print(f"  ({type(e).__name__}: {e})\n")
        print(ANGRY_CAT)
        sys.exit(1)

    print(HAPPY_CAT)


if __name__ == "__main__":
    main()
