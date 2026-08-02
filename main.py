import sys

try:
    from src.runner import main
except RuntimeError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
