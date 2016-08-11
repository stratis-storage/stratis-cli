import os
import sys

from cli import run

def main():
    execution = run(sys.argv[1:])
    args = next(execution)
    print(args)
    print(os.linesep)
    (rc, message) = next(execution)
    print(message)
    return rc

if __name__ == "__main__":
    main()
