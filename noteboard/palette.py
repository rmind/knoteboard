from dataclasses import dataclass, fields


@dataclass(frozen=True)
class Palette:
    """
    Solarized colour theme (dark).
    """

    BASE03: tuple[str, str] = ("#002b36", "black")
    BASE02: tuple[str, str] = ("#073642", "dark gray")
    BASE01: tuple[str, str] = ("#586e75", "light gray")
    BASE00: tuple[str, str] = ("#657b83", "white")
    BASE0: tuple[str, str] = ("#839496", "light blue")
    BASE1: tuple[str, str] = ("#93a1a1", "dark green")
    BASE2: tuple[str, str] = ("#eee8d5", "dark gray")
    BASE3: tuple[str, str] = ("#fdf6e3", "black")
    YELLOW: tuple[str, str] = ("#b58900", "yellow")
    ORANGE: tuple[str, str] = ("#cb4b16", "light red")
    RED: tuple[str, str] = ("#dc322f", "dark red")
    MAGENTA: tuple[str, str] = ("#d33682", "light magenta")
    VIOLET: tuple[str, str] = ("#6c71c4", "dark magenta")
    BLUE: tuple[str, str] = ("#268bd2", "dark blue")
    CYAN: tuple[str, str] = ("#2aa198", "light cyan")
    GREEN: tuple[str, str] = ("#859900", "dark green")

    @classmethod
    def format(cls, foreground, background):
        """
        Convert to accommodate urwid.
        """
        fg_color_high, fg_color = foreground
        bg_color_high, bg_color = background
        return (
            fg_color,
            bg_color,
            None,
            fg_color_high,
            bg_color_high,
        )

    @classmethod
    def list(cls) -> dict[str, tuple]:
        """
        Get a list of color names and the corresponding value tuple.
        """
        return {f.name.lower(): getattr(cls, f.name) for f in fields(cls)}
