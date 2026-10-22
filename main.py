from datetime import datetime
import math
import queue
import sys
import threading
import time


GRID_HEIGHT = 21
GRID_WIDTH = 43
CENTER_ROW = GRID_HEIGHT // 2
CENTER_COLUMN = GRID_WIDTH // 2


class Stopwatch:
    def __init__(self):
        self._elapsed_before_start = 0.0
        self._started_at = None

    def start(self):
        if self._started_at is None:
            self._started_at = time.monotonic()

    def pause(self):
        if self._started_at is not None:
            self._elapsed_before_start += time.monotonic() - self._started_at
            self._started_at = None

    def reset(self):
        self._elapsed_before_start = 0.0
        self._started_at = None

    def elapsed(self):
        if self._started_at is None:
            return self._elapsed_before_start
        return self._elapsed_before_start + time.monotonic() - self._started_at


def draw_hand(grid, angle, length, symbol):
    end_column = round(CENTER_COLUMN + math.sin(angle) * length * 2)
    end_row = round(CENTER_ROW - math.cos(angle) * length)
    steps = max(abs(end_column - CENTER_COLUMN), abs(end_row - CENTER_ROW))

    for step in range(steps + 1):
        ratio = step / steps if steps else 0
        column = round(CENTER_COLUMN + (end_column - CENTER_COLUMN) * ratio)
        row = round(CENTER_ROW + (end_row - CENTER_ROW) * ratio)
        grid[row][column] = symbol


def draw_clock(now):
    grid = [[" " for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

    for row in range(GRID_HEIGHT):
        for column in range(GRID_WIDTH):
            horizontal = (column - CENTER_COLUMN) / 2
            vertical = row - CENTER_ROW
            distance = math.sqrt(horizontal**2 + vertical**2)
            if 9.6 <= distance <= 10.6:
                grid[row][column] = "o"

    for hour in range(1, 13):
        angle = hour * math.pi / 6
        row = round(CENTER_ROW - math.cos(angle) * 8)
        column = round(CENTER_COLUMN + math.sin(angle) * 16)
        label = str(hour).rjust(2)
        grid[row][column - 1 : column + 1] = label

    hour_value = now.hour % 12 + now.minute / 60 + now.second / 3600
    minute_value = now.minute + now.second / 60
    second_value = now.second + now.microsecond / 1_000_000

    draw_hand(grid, hour_value * math.pi / 6, 5, "H")
    draw_hand(grid, minute_value * math.pi / 30, 8, "M")
    draw_hand(grid, second_value * math.pi / 30, 9, ".")
    grid[CENTER_ROW][CENTER_COLUMN] = "+"

    return ["".join(row).rstrip() for row in grid]


def format_stopwatch(seconds):
    centiseconds = int(seconds * 100)
    minutes, remainder = divmod(centiseconds, 6000)
    whole_seconds, fraction = divmod(remainder, 100)
    return f"{minutes:02d}:{whole_seconds:02d}.{fraction:02d}"


def build_display(now, stopwatch, status):
    lines = [
        "RELOJ ANALOGICO - Python puro",
        "",
        f"Hora:  {now:%H:%M:%S}",
        f"Fecha: {now:%d/%m/%Y}",
        "",
        *draw_clock(now),
        "",
        f"Cronometro: {format_stopwatch(stopwatch.elapsed())}",
        f"Estado: {status}",
        "",
        "Comandos: start | pause | reset | help | exit",
        "",
    ]
    return "\n".join(lines)


def read_commands(commands):
    while True:
        try:
            command = input("Comando: ").strip().lower()
        except EOFError:
            commands.put("exit")
            return

        commands.put(command)
        if command in {"exit", "quit", "q"}:
            return


def main():
    stopwatch = Stopwatch()
    commands = queue.Queue()
    status = "Pausado"
    running = True

    sys_stdout = sys.stdout
    sys_stdout.write("\033[2J\033[H")
    sys_stdout.flush()

    frame = build_display(datetime.now(), stopwatch, status)
    sys_stdout.write(frame)
    sys_stdout.write("\033[33;1H")
    sys_stdout.flush()

    input_thread = threading.Thread(
        target=read_commands, args=(commands,), daemon=True
    )
    input_thread.start()

    while running:
        while True:
            try:
                command = commands.get_nowait()
            except queue.Empty:
                break

            if command in {"start", "s"}:
                stopwatch.start()
                status = "En marcha"
            elif command in {"pause", "p"}:
                stopwatch.pause()
                status = "Pausado"
            elif command in {"reset", "r"}:
                stopwatch.reset()
                status = "Reiniciado"
            elif command == "help":
                status = "Use start, pause, reset o exit"
            elif command in {"exit", "quit", "q"}:
                running = False
                break
            elif command:
                status = f"Comando no reconocido: {command}"

        if not running:
            break

        frame = build_display(datetime.now(), stopwatch, status)
        sys_stdout.write("\033[s\033[H")
        sys_stdout.write(frame)
        sys_stdout.write("\033[u")
        sys_stdout.flush()
        time.sleep(0.1)

    sys_stdout.write("\033[33;1H\033[2KPrograma finalizado.\n")
    sys_stdout.flush()


if __name__ == "__main__":
    main()
