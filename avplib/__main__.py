import os
import click
import avplib
import pygame
import fpstimer
import time
from rich.console import Console
from rich.progress import Progress
from rich.live import Live
from typing import Tuple, List

# ! Set Environ
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# ! Reinitialize
class Console(Console):
    def set_size(self, size: Tuple[int, int]) -> None:
        os.system(f'mode {size[0]},{size[1]}')

# ! Initialized
console = Console()
console = Console(width=console.size.width-1, height=console.size.height)

# ! Functions
def play_audio(audio_path: str) -> None:
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()

def play_video(frames: List[str], fps: int) -> None:
    fps_timer = fpstimer.FPSTimer(fps)
    with Live(frames[0], auto_refresh=False, console=console) as live:
        for frame in frames:
            live.update(frame, refresh=True)
            fps_timer.sleep()

# ! CLI
@click.command()
@click.argument(
    "video_path",
    type=click.Path(exists=True)
)
@click.option(
    "-r", "--res",
    type=click.Tuple([int, int]),
    default=(0, 0),
    show_default=True
)
@click.option(
    "--fps",
    type=click.IntRange(1, 120),
    default=30,
    show_default=True
)
@click.option(
    "--threading/--no-threading", " /-th",
    default=False
)
def main(video_path: str, res: Tuple[int, int], fps: int, threading: bool):
    if sum(res) > 0:
        console.set_size((res[0]+1, res[1]))
    else:
        res = (console.size.width-1, console.size.height)

    console.print(f"[#EA00FF]*[/] [#BBFF00]Video Path[/]: '{os.path.abspath(video_path)}'")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Resolution[/]: {res[0]}x{res[1]}")

    video = avplib.AVP(video_path)
    if (fps != 30) and (fps != video.get_fps()):
        video.set_fps(fps)
    
    audio_path = video.get_audio("file")

    st = time.time()
    with Progress(transient=True) as pr:
        gaf = pr.add_task("Generation ASCII")
        def update_bar(complited: int, total: int): pr.update(gaf, total=total, completed=complited)
        if threading:
            frames = video.get_ascii_frames_threading(res, callback=update_bar)
        else:
            frames = video.get_ascii_frames(res, callback=update_bar)
    et = time.time()
    
    console.print(f"[#EA00FF]*[/] [#BBFF00]Total Time[/]: {(et-st):.2} [yellow]sec[/]\n[red](ENTER to continue)[/]")
    input()

    play_audio(audio_path)
    play_video(frames, fps)

if __name__ == '__main__':
    main()