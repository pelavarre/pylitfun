#!/usr/bin/env python3

import math


far16 = math.sqrt(3 * 0xFFFF * 0xFFFF)

def rgb16_distance(r: int, g: int, b: int) -> float:
    f = math.sqrt(r * r + g * g + b * b) / far16
    return f

def func(o10: tuple[int, ...], o11: tuple[int, ...], o12: tuple[int, ...], t: str) -> None:

    d10 = rgb16_distance(*o10)
    d11 = rgb16_distance(*o11)
    d12 = rgb16_distance(*o12)

    s = "⬛" if (d11 < 0.25) else "⬜"

    x = sum(o11) < 30_000
    print(s, int(x), t, round(d10, 3), -round(d11, 3), round(d12, 3), o10, o11, o12)


#

# todo: Ghostty


#

t = "Dark iTerm2"
func((0xDCAA, 0xDCAB, 0xDCAA), o11=(0x158E, 0x193A, 0x1E75), o12=(0xFFFD, 0xFFFE, 0xFFFe), t=t)

t = "Light iTerm2"
func((0x1010, 0x1010, 0x1010), o11=(0xFAE0, 0xFAE0, 0xFAE0), o12=(0x0000, 0x0000, 0x0000), t=t)


#

t = "Dark Basic"  # Basic in Darkmode
func((0xFFFF, 0xFFFF, 0xFFFF), o11=(0x2020, 0x2020, 0x2020), o12=(0x9282, 0x9282, 0x9282), t=t)

t = "Light Basic"  # Basic in Lightmode
func((0x0000, 0x0000, 0x0000), o11=(0xFFFF, 0xFFFF, 0xFFFF), o12=(0x9DD1, 0x9DD1, 0x9DD1), t=t)

# todo: t = "Clear Dark"

# todo: t = "Clear Light"

t = "Grass"
func((0xFFFF, 0xF0F0, 0xA5A5), o11=(0x1313, 0x7777, 0x3D3D), o12=(0x8E8E, 0x2828, 0x0000), t=t)

t = "Homebrew"
func((0x2828, 0xFEFE, 0x1414), o11=(0x0000, 0x0000, 0x0000), o12=(0x3838, 0xFEFE, 0x2727), t=t)

t = "Man Page"
func((0x0000, 0x0000, 0x0000), o11=(0xFEFE, 0xF4F4, 0x9C9C), o12=(0x9DD1, 0x9DD1, 0x9DD1), t=t)

t = "Novel"
func((0x4D23, 0x2EFB, 0x2D4B), o11=(0xDFFF, 0xDBA4, 0xC3FF), o12=(0x3A3A, 0x2323, 0x2222), t=t)

t = "Ocean"
func((0xFFFF, 0xFFFF, 0xFFFF), o11=(0x2B5F, 0x66A6, 0xC977), o12=(0x9DD1, 0x9DD1, 0x9DD1), t=t)

t = "Pro"
func((0xF54F, 0xF54F, 0xF54F), o11=(0x0000, 0x0000, 0x0000), o12=(0x600F, 0x600F, 0x600F), t=t)

t = "Red Sands"
func((0xD7D7, 0xC9C9, 0xA7A7), o11=(0x8EAC, 0x34E2, 0x276E), o12=(0xFFFF, 0xFFFF, 0xFFFF), t=t)

t = "Silver Aerogel"
func((0x0000, 0x0000, 0x0000), o11=(0x9282, 0x9282, 0x9282), o12=(0xE101, 0xE101, 0xE101), t=t)

t = "Solid Colors"
func((0x0000, 0x0000, 0x0000), o11=(0xFFFF, 0xFFFF, 0xFFFF), o12=(0xCB95, 0xCB95, 0xCB95), t=t)



_ = """

macOS iTerm2 Terminal Theme

    sampled in Darkmode at Dec/2025 Build 3.6.6

    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:dcaa/dcab/dcaa^[\
    ^[]11;rgb:158e/193a/1e75^[\
    ^[]12;rgb:fffd/fffe/fffe^[\
    %

    sampled in Lightmode at Dec/2025 Build 3.6.6

    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:1010/1010/1010^[\
    ^[]11;rgb:fae0/fae0/fae0^[\
    ^[]12;rgb:0000/0000/0000^[\
    %

Apple macOS Terminal Themes

    sampled in Darkmode at Oct/2024 Sequoia macOS 15, patched up to 15.7.2 build 24G325

    % # Basic
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:ffff/ffff/ffff^G
    ^[]11;rgb:2020/2020/2020^G
    ^[]12;rgb:9282/9282/9282^G
    %

    sampled in Lightmode at Oct/2024 Sequoia macOS 15, patched up to 15.7.2 build 24G325

    % # Basic
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:0000/0000/0000^G
    ^[]11;rgb:ffff/ffff/ffff^G
    ^[]12;rgb:9dd1/9dd1/9dd1^G
    %

    % # Grass
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:ffff/f0f0/a5a5^G
    ^[]11;rgb:1313/7777/3d3d^G
    ^[]12;rgb:8e8e/2828/0000^G
    %

    % # Homebrew
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:2828/fefe/1414^G
    ^[]11;rgb:0000/0000/0000^G
    ^[]12;rgb:3838/fefe/2727^G
    %

    % # Man Page
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:0000/0000/0000^G
    ^[]11;rgb:fefe/f4f4/9c9c^G
    ^[]12;rgb:9dd1/9dd1/9dd1^G
    %

    % # Novel
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:4d23/2efb/2d4b^G
    ^[]11;rgb:dfff/dba4/c3ff^G
    ^[]12;rgb:3a3a/2323/2222^G
    %

    % # Ocean
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:ffff/ffff/ffff^G
    ^[]11;rgb:2b5f/66a6/c977^G
    ^[]12;rgb:9dd1/9dd1/9dd1^G
    %

    % # Pro
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:f54f/f54f/f54f^G^D
    ^[]11;rgb:0000/0000/0000^G
    ^[]12;rgb:600f/600f/600f^G
    %

    % # Red Sands
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:d7d7/c9c9/a7a7^G
    ^[]11;rgb:8eac/34e2/276e^G
    ^[]12;rgb:ffff/ffff/ffff^G
    %

    % # Silver Aerogel
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:0000/0000/0000^G
    ^[]11;rgb:9282/9282/9282^G
    ^[]12;rgb:e101/e101/e101^G
    %

    % # Solid Colors
    % printf '\033]10;?\007' && cat - >/dev/null && printf '\033]11;?\007' && cat - >/dev/null && printf '\033]12;?\007' && cat - >/dev/null
    ^[]10;rgb:0000/0000/0000^G
    ^[]11;rgb:ffff/ffff/ffff^G
    ^[]12;rgb:cb95/cb95/cb95^G
    %

"""
