__version__ = "0.1.5"

from . import server


def main():
    server.main()


__all__ = [
    "server",
    "main",
]