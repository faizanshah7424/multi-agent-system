import argparse


def run_cli(args_list=None):
    parser = argparse.ArgumentParser(description="Mock Python CLI tool")
    parser.add_argument(
        "--message", type=str, default="Welcome to the CodeOrbit Python CLI!"
    )
    args = parser.parse_args(args_list)
    print(args.message)
    return args.message


if __name__ == "__main__":
    run_cli()
