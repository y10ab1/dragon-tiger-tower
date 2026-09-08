"""Procedurally generate game sound effects as WAV files (16-bit mono)."""
import math
import os
import random
import struct
import wave

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "game", "assets", "audio")
os.makedirs(OUT, exist_ok=True)
random.seed(7)


def write_wav(name, samples):
    path = os.path.join(OUT, name)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = b"".join(
            struct.pack("<h", max(-32767, min(32767, int(s * 32767))))
            for s in samples)
        w.writeframes(frames)
    print("wrote", path, len(samples) / SR, "s")


def lowpass(samples, alpha):
    out, y = [], 0.0
    for s in samples:
        y += alpha * (s - y)
        out.append(y)
    return out


def wind_loop(dur=10.0):
    n = int(SR * dur)
    noise = [random.uniform(-1, 1) for _ in range(n)]
    base = lowpass(lowpass(noise, 0.03), 0.05)
    out = []
    for i in range(n):
        t = i / SR
        gust = 0.55 + 0.45 * math.sin(2 * math.pi * t / dur) \
            * math.sin(2 * math.pi * 2 * t / dur + 1.3)
        out.append(base[i] * gust * 6.0)
    m = max(abs(s) for s in out)
    return [s / m * 0.5 for s in out]


def heartbeat(dur=1.1):
    n = int(SR * dur)
    out = [0.0] * n

    def thump(t0, amp):
        for i in range(int(0.12 * SR)):
            t = i / SR
            idx = int(t0 * SR) + i
            if idx < n:
                env = math.exp(-t * 30)
                out[idx] += amp * env * math.sin(2 * math.pi * 55 * t)
    thump(0.0, 0.9)
    thump(0.28, 0.6)
    return out


def moan(dur=4.0):
    n = int(SR * dur)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / SR
        f = 150 + 40 * math.sin(2 * math.pi * 0.4 * t) - 15 * t
        phase += 2 * math.pi * f / SR
        env = math.sin(math.pi * t / dur) ** 1.5
        s = (math.sin(phase) * 0.5 + math.sin(phase * 2.02) * 0.25
             + math.sin(phase * 0.5) * 0.3)
        s += random.uniform(-0.25, 0.25)
        out.append(s * env * 0.5)
    return lowpass(out, 0.25)


def pickup(dur=0.9):
    n = int(SR * dur)
    out = []
    for i in range(n):
        t = i / SR
        env = math.exp(-t * 5)
        s = (math.sin(2 * math.pi * 880 * t) * 0.5
             + math.sin(2 * math.pi * 1320 * t) * 0.3
             + math.sin(2 * math.pi * 1760 * t) * 0.2)
        out.append(s * env * 0.5)
    return out


def death(dur=1.6):
    n = int(SR * dur)
    noise = [random.uniform(-1, 1) for _ in range(n)]
    noise = lowpass(noise, 0.4)
    out = []
    for i in range(n):
        t = i / SR
        env = math.exp(-t * 3)
        drone = math.sin(2 * math.pi * (90 - 40 * t) * t)
        shriek = math.sin(2 * math.pi * (1200 + 500 * math.sin(30 * t)) * t)
        out.append((noise[i] * 2.2 + drone * 0.6 + shriek * 0.3 * env)
                   * env * 0.7)
    return out


def gong(dur=3.5):
    n = int(SR * dur)
    out = []
    for i in range(n):
        t = i / SR
        env = math.exp(-t * 1.4)
        s = (math.sin(2 * math.pi * 220 * t) * 0.4
             + math.sin(2 * math.pi * 331 * t) * 0.3
             + math.sin(2 * math.pi * 442 * t + 0.5) * 0.2
             + math.sin(2 * math.pi * 553 * t) * 0.1 * math.sin(6 * t))
        out.append(s * env * 0.6)
    return out


def whisper(dur=3.0):
    """Creepy whisper-like filtered noise bursts."""
    n = int(SR * dur)
    noise = [random.uniform(-1, 1) for _ in range(n)]
    noise = lowpass(noise, 0.5)
    out = []
    for i in range(n):
        t = i / SR
        syl = max(0.0, math.sin(2 * math.pi * 3.1 * t)) \
            * max(0.0, math.sin(2 * math.pi * 0.7 * t + 0.4))
        out.append(noise[i] * syl * 0.55)
    return out


def footstep(dur=0.18):
    n = int(SR * dur)
    noise = lowpass([random.uniform(-1, 1) for _ in range(n)], 0.15)
    out = []
    for i in range(n):
        t = i / SR
        env = math.exp(-t * 40)
        out.append(noise[i] * env * 2.4)
    m = max(abs(s) for s in out)
    return [s / m * 0.35 for s in out]


write_wav("wind_loop.wav", wind_loop())
write_wav("heartbeat.wav", heartbeat())
write_wav("moan.wav", moan())
write_wav("pickup.wav", pickup())
write_wav("death.wav", death())
write_wav("gong.wav", gong())
write_wav("whisper.wav", whisper())
write_wav("footstep.wav", footstep())
