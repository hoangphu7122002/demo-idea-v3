"""CLI: ``python -m app.seed`` reseeds; ``--if-empty`` seeds only an empty database."""

import argparse

from app.seed.service import reseed, seed_if_empty


def main() -> None:
    """Parse arguments and run the seed; prints what happened."""
    parser = argparse.ArgumentParser(prog="python -m app.seed", description=__doc__)
    parser.add_argument(
        "--if-empty", action="store_true", help="seed only when there are no posts yet"
    )
    args = parser.parse_args()
    if args.if_empty:
        print("seeded" if seed_if_empty() else "skipped: posts already exist")
    else:
        reseed()
        print("reseeded")


if __name__ == "__main__":
    main()
