import os
import click
import avplib
import pygame
import fpstimer
import time
import zipfile
import json
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.progress import Progress
from rich.live import Live
from typing import Tuple, List, Dict, Any

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
    "--no_audio", "-na",
    is_flag=True,
    help="Disable audio playback."
)
def cav(video_path: str, res: Tuple[int, int], fps: int, threading: bool, no_audio: bool):
    if sum(res) > 0:
        console.set_size((res[0]+1, res[1]))
    else:
        res = (console.size.width-1, console.size.height)

    console.print(f"[#EA00FF]*[/] [#BBFF00]Video Path[/]: '{os.path.abspath(video_path)}'")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Resolution[/]: {res[0]}x{res[1]}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]FPS[/]: {fps}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Enable Threading[/]: {threading}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Disable Audio[/]: {no_audio}")

    video = avplib.AVP(video_path)
    if (fps != 30) and (fps != video.get_fps()):
        video.set_fps(fps)
    if not no_audio:
        audio_path = video.get_audio("file")

    st = time.time()
    with Progress(transient=True) as pr:
        gaf = pr.add_task("Generation ASCII")
        
        def update_bar(complited: int, total: int): pr.update(gaf, total=total, completed=complited)
        
        if threading: frames = video.get_ascii_frames_threading(res, callback=update_bar)
        else: frames = video.get_ascii_frames(res, callback=update_bar)
    et = time.time()
    
    console.print(f"[#EA00FF]*[/] [#BBFF00]Total Time[/]: {round(et-st,2)} [yellow]sec[/]\n[red](ENTER to continue)[/]")
    input()
    if not no_audio:
        play_audio(audio_path)
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
    default=(118, 30),
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
    "--auto_res", "-ar",
    is_flag=True,
    help="Automatically detection resolution."
)
def convert2avf(from_video_path: str, to_video_path: str, res: Tuple[int, int], fps: int, threading: bool, auto_res: bool):
    if auto_res:
        res = (console.size.width-1, console.size.height)
    console.print(f"[#EA00FF]*[/] [#BBFF00]From Video Path[/]: {os.path.abspath(from_video_path).__repr__()}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]To Video Path[/]: {os.path.abspath(to_video_path).__repr__()}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Resolution[/]: {res[0]}x{res[1]}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]FPS[/]: {fps}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Enable Threading[/]: {threading}")
    
    st = time.time()
    with Progress(transient=True) as pr:
        preparation = pr.add_task("Creating an archive", total=6)
        gaf = pr.add_task("Generation ASCII")
        
        def update_bar(complited: int, total: int): pr.update(gaf, total=total, completed=complited)
        
        # * Подготовка
        with zipfile.ZipFile(to_video_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as av_file:
            pr.update(preparation, advance=1, description="Preparation Video File")
            video = avplib.AVP(from_video_path)
            if fps != video.get_fps():
                video.set_fps(fps)
            
            pr.update(preparation, advance=1, description="Getting audio")
            audio_path = video.get_audio("file")
            
            pr.update(preparation, advance=1, description="Compressing audio")
            av_file.write(audio_path, "audio")
            
            # * Convert
            pr.update(preparation, advance=1, description="Writing Video")
            with NamedTemporaryFile("wb", delete=False) as av_tempfile:
                if threading:
                    frames = video.get_ascii_frames_threading(res, callback=update_bar)
                else:
                    frames = video.get_ascii_frames(res, callback=update_bar)
                pr.remove_task(gaf)
                av_tempfile_path = av_tempfile.name
                for i in frames:
                    if i != None:
                        av_tempfile.write((i+"\r\n\r\n").encode(errors="ignore"))
                avplib.TEMP_DETECTOR.append(av_tempfile.name)
            
            with NamedTemporaryFile("wb", delete=False) as av_info_file:
                av_info_file_path = av_info_file.name
                av_info_file.write(json.dumps({"fps": fps, "res": res}).encode(errors="ignore"))
                avplib.TEMP_DETECTOR.append(av_info_file.name)
            
            av_file.write(av_info_file_path, "info")
            
            pr.update(preparation, advance=1, description="Compressing ASCII Video")
            av_file.write(av_tempfile_path, "video")
            
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
def play_avf(ascii_video_path: str, no_audio: bool) -> None:
    st = time.time()
    with Progress(transient=True) as pr:
        loading = pr.add_task("Getting info", total=3)
        
        with zipfile.ZipFile(ascii_video_path, "r") as av_file:
            info: Dict[str, Any] = json.loads(av_file.read("info"))
            
            pr.update(loading, advance=1, description="Getting Audio")
            if not no_audio:
                with NamedTemporaryFile("wb", delete=False) as av_audio:
                    audio_path = av_audio.name
                    av_audio.write(av_file.read("audio"))
                    avplib.TEMP_DETECTOR.append(av_audio.name)
            
            pr.update(loading, advance=1, description="Getting Video")
            frames = av_file.read("video").decode(errors="ignore").split("\r\n\r\n")
        
        pr.update(loading, advance=1, description="Done!")
    et = time.time()
    
    console.print(f"[#EA00FF]*[/] [#BBFF00]ASCII Video File[/]: {os.path.abspath(ascii_video_path).__repr__()}")
    console.print(f"\n[#EA00FF]*[/] [#BBFF00]Resolution[/]: {info['res'][0]}x{info['res'][1]}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]FPS[/]: {info['fps']}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Disable Audio[/]: {no_audio}")
    console.print(f"[#EA00FF]*[/] [#BBFF00]Total Time[/]: {round(et-st,2)} [yellow]sec[/]\n[red](ENTER to continue)[/]")
    input()
    if not no_audio:
        play_audio(audio_path)
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