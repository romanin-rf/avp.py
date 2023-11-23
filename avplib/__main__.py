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
# > Local Imports
from .avf import AVFile
from .units import ASCII_CHARS

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

# > Convert (in memory) and view
@click.command("cav", help="Play video files (*.mp4/*.avi/...)")
@click.argument(
    "video_path",
    type=click.Path(exists=True, file_okay=True)
)
@click.option(
    "-r", "--res",
    type=click.Tuple([int, int]),
    default=(0, 0),
    show_default=True,
    help="Resolution of the terminal of the video to be played."
)
@click.option(
    "--fps",
    type=click.IntRange(1, 120),
    default=30,
    show_default=True,
    help="FPS at which the video will be played back."
)
@click.option(
    "--threading", "-th",
    is_flag=True,
    help="Enable on threading processing."
)
@click.option(
    "--multiprocessing", "-mp",
    is_flag=True,
    help="Enable on multiprocessing."
)
@click.option(
    "--no_audio", "-na",
    is_flag=True,
    help="Disable audio playback."
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    help="Disable playback confirmation."
)
@click.option(
    "--ascii_chars",
    type=list,
    default=ASCII_CHARS,
    show_default=True,
    help="ASCII Chars for to create gradation (256 <= ascii_chars)."
)
def cav(
    video_path: str,
    res: Tuple[int, int],
    fps: int,
    threading: bool,
    multiprocessing: bool,
    no_audio: bool,
    yes: bool,
    ascii_chars: List[str]
):
    multiprocessing = multiprocessing and avplib.avplib.init_multiprocessing

    if sum(res) > 0:
        console.set_size((res[0]+1, res[1]))
    else:
        res = (console.size.width-1, console.size.height)
    
    if len(ascii_chars) > 256: ascii_chars = ascii_chars[:256]

    console.print(f"[#EA00FF]*[/] [#BBFF00]Video Path[/]: '{os.path.abspath(video_path)}'")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Resolution[/]: {res[0]}x{res[1]}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]FPS[/]: {fps}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Enable Threading[/]: {threading}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Enable Multiprocessing[/]: {multiprocessing}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Disable Audio[/]: {no_audio}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]ASCII Chars[/]: {ascii_chars}")

    video = avplib.AVP(video_path, ascii_chars)
    if (fps != 30) and (fps != video.get_fps()):
        video.set_fps(fps)
    if not no_audio:
        audio_path = video.get_audio("file")

    st = time.time()
    with Progress(transient=True) as pr:
        gaf = pr.add_task("Generation ASCII")
        def update_bar(complited: int, total: int):
            pr.update(gaf, total=total, completed=complited)
        if threading:
            frames = video.get_ascii_frames_threading(res, callback=update_bar)
        elif multiprocessing:
            frames = video.get_ascii_frames_multiprocessing(res, callback=update_bar)
        else:
            frames = video.get_ascii_frames(res, callback=update_bar)
    et = time.time()
    
    console.print(f"[#EA00FF]*[/] [#BBFF00]Total Time[/]: {round(et-st,2)} [yellow]sec[/]\n[red](ENTER to continue)[/]")
    if not yes: input()
    if not no_audio: play_audio(audio_path)
    play_video(frames, fps)

# > Convert and save
@click.command("convert", help="Convert Video Files to ASCII Video File.")
@click.argument(
    "from_video_path",
    type=click.Path(exists=True, file_okay=True),
)
@click.argument(
    "to_video_path",
    type=click.Path(),
)
@click.option(
    "-r", "--res",
    type=click.Tuple([int, int]),
    default=(120, 30),
    show_default=True,
    help="Resolution for conversion (does not change after conversion)."
)
@click.option(
    "--fps",
    type=click.IntRange(1, 120),
    default=30,
    show_default=True,
    help="FPS for conversion (does not change after conversion)."
)
@click.option(
    "--threading", "-th",
    is_flag=True,
    help="Enable on threading processing."
)
@click.option(
    "--multiprocessing", "-mp",
    is_flag=True,
    help="Enable on multiprocessing."
)
@click.option(
    "--auto_res", "-ar",
    is_flag=True,
    help="Automatically detection resolution."
)
@click.option(
    "--title", "-t",
    help="Set title.",
    type=str,
    default=""
)
@click.option(
    "--author", "-a",
    help="Set author.",
    type=str,
    default=""
)
@click.option(
    "--no_audio", "-na",
    is_flag=True,
    help="Disable audio playback."
)
@click.option(
    "--ascii_chars",
    type=list,
    default=ASCII_CHARS,
    show_default=True,
    help="ASCII Chars for to create gradation (256 <= ascii_chars)."
)
def convert2avf(
    from_video_path: str,
    to_video_path: str,
    res: Tuple[int, int],
    fps: int,
    threading: bool,
    multiprocessing: bool,
    auto_res: bool,
    title: str,
    author: str,
    no_audio: bool,
    ascii_chars: List[str]
):
    multiprocessing = multiprocessing and avplib.avplib.init_multiprocessing

    if auto_res:
        res = (console.size.width-1, console.size.height)
    
    if len(ascii_chars) > 256: ascii_chars = ascii_chars[:256]
    
    console.print(f"[#EA00FF]*[/] [#BBFF00]From Video Path[/]: {os.path.abspath(from_video_path).__repr__()}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]To Video Path[/]: {os.path.abspath(to_video_path).__repr__()}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Resolution[/]: {res[0]}x{res[1]}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]FPS[/]: {fps}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Enable Threading[/]: {threading}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Enable Multiprocessing[/]: {multiprocessing}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Disable Audio[/]: {no_audio}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]ASCII Chars[/]: {ascii_chars}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Title[/]: {title.__repr__()}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Author[/]: {author.__repr__()}")
    
    st = time.time()
    with Progress(transient=True) as pr:
        preparation = pr.add_task("Creating an archive", total=5)
        gaf = pr.add_task("Generation ASCII")
        
        def update_bar(complited: int, total: int): pr.update(gaf, total=total, completed=complited)
        
        # * Подготовка
        avfile = AVFile(to_video_path, "w")
        
        pr.update(preparation, advance=1, description="Preparation Video File")
        video = avplib.AVP(from_video_path, ascii_chars)
        if fps != video.get_fps():
            video.set_fps(fps)
        
        pr.update(preparation, advance=1, description="Writing info")
        avfile.set_info(
            title,
            author,
            fps,
            res,
            not(no_audio),
            ascii_chars
        )
        
        pr.update(preparation, advance=1, description="Compressing audio")
        if not no_audio: avfile.set_audio_from_path(video.get_audio("file"))
        
        # * Convert
        pr.update(preparation, advance=1, description="Compressing Video")
        if threading:
            frames = video.get_ascii_frames_threading(res, callback=update_bar)
        elif multiprocessing:
            frames = video.get_ascii_frames_multiprocessing(res, callback=update_bar)
        else:
            frames = video.get_ascii_frames(res, callback=update_bar)
        pr.remove_task(gaf)
        avfile.set_video(frames)
        
        avfile.close()
        pr.update(preparation, advance=1, description="Done!")
    et = time.time()
    
    console.print(f"[#EA00FF]*[/] [#BBFF00]Total Time[/]: {round(et-st,2)} [yellow]sec[/]")

@click.command("play", help="Play ASCII Video.")
@click.argument(
    "ascii_video_path",
    type=click.Path(exists=True, file_okay=True),
)
@click.option(
    "--no_audio", "-na",
    is_flag=True,
    help="Disable audio playback."
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    help="Disable playback confirmation."
)
def play_avf(ascii_video_path: str, no_audio: bool, yes: bool) -> None:
    st = time.time()
    with Progress(transient=True) as pr:
        loading = pr.add_task("Open an archive", total=4)
        
        avfile = AVFile(ascii_video_path, "r")
        
        pr.update(loading, advance=1, description="Getting Info")
        info = avfile.get_info()
        
        pr.update(loading, advance=1, description="Getting Video")
        frames = avfile.get_video()
        
        pr.update(loading, advance=1, description="Getting Audio")
        if (not no_audio) and (info["exists_audio"]): audio_path = avfile.get_audio_path()
        
        pr.update(loading, advance=1, description="Done!")
    et = time.time()
    
    console.print(f"\n[#EA00FF]*[/] [#BBFF00]ASCII Video File[/]: {os.path.abspath(ascii_video_path).__repr__()}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Resolution[/]: {info['res'][0]}x{info['res'][1]}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]FPS[/]: {info['fps']}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Title[/]: {info['title'].__repr__()}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Author[/]: {info['author'].__repr__()}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Exists Audio[/]: {info['exists_audio']}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Disable Audio[/]: {no_audio}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]ASCII Chars[/]: {info['ascii_chars']}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Total Time[/]: {round(et-st,2)} [yellow]sec[/]\n[red](ENTER to continue)[/]")
    
    if not yes: input()
    if (not no_audio) and (info["exists_audio"]): play_audio(audio_path)
    
    play_video(frames, info['fps'])

# > Main
@click.group()
def main(): pass

# > Start
if __name__ == '__main__':
    main.add_command(cav)
    main.add_command(convert2avf)
    main.add_command(play_avf)
    main()
    avplib.TEMP_DETECTOR.clear()