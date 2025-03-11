__version__ = "0.1.6"

from . import server


def main():
    server.main()


__all__ = [
    "server",
    "main",
]