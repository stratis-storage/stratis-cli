from cli import gen_parser

def main():
    parser = gen_parser()
    args = parser.parse_args()
    print(args)

if __name__ == "__main__":
    main()
