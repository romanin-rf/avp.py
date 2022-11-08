import os
import cv2
import moviepy.editor as mp
import soundfile as sf
from PIL import Image
from typing import Literal
from io import BufferedReader, BytesIO
from tempfile import NamedTemporaryFile
from .units import ASCII_CHARS_GRADIENTION

class AVP:
    def __init__(self, fp) -> None:
        self.tempfiles = []
        if isinstance(fp, str):
            self.path = os.path.abspath(fp)
        elif isinstance(fp, bytes):
            with NamedTemporaryFile("wb", delete=False) as tempfile:
                tempfile.write(fp)
                self.path = os.path.abspath(tempfile.name)
                self.tempfiles.append(self.path)
        elif isinstance(fp, BufferedReader):
            self.path = os.path.abspath(fp.name)
        else:
            raise TypeError(f"The variable type 'fp' does not accept the type {type(fp)}")
        self.video = mp.VideoFileClip(self.path)
    
    def __del__(self) -> None:
        self.video.close()
        for i in self.tempfiles:
            os.remove(i)
    
    def get_frames_count(self):
        cap = cv2.VideoCapture(self.path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))-1
        cap.release()
        return total_frames
    
    def get_fps(self):
        return int(self.video.fps)
    
    def set_fps(self, fps):
        with NamedTemporaryFile("wb", suffix=".mp4", delete=False) as tempfile:
            filepath = os.path.abspath(tempfile.name)
        self.tempfiles.append(filepath)
        self.video.write_videofile(filename=filepath, fps=fps, codec="mpeg4")
    
    def get_audio(self, tp: Literal["file", "bytes", "array"], filepath=None):
        if tp == "file":
            if filepath is None:
                with NamedTemporaryFile("wb", suffix=".mp3", delete=False) as tempfile:
                    filepath = os.path.abspath(tempfile.name)
                self.tempfiles.append(filepath)
            else:
                filepath = os.path.abspath(filepath)
            self.video.audio.write_audiofile(filepath)
            return filepath
        elif (tp == "bytes") or (tp == "array"):
            array = self.video.audio.to_soundarray(fps=44100, nbytes=4)
            if tp == "array":
                return array
            else:
                bio = BytesIO()
                sf.write(bio, array, 44100, subtype="PCM_32", format="WAV")
                return bio.read()
    
    @staticmethod
    def _callback(complited, total): ...

    def get_ascii_frames(self, frame_size, callback=_callback):
        capture, al = cv2.VideoCapture(self.path), []
        capture.set(1, 1)
        frames_count = self.get_frames_count()
        for i in range(1, frames_count):
            callback(i, frames_count)
            ret, image_frame = capture.read()
            if ret:
                ac = "".join([ASCII_CHARS_GRADIENTION[pixel] for pixel in Image.fromarray(image_frame).convert("L").resize(frame_size).getdata()])
                al.append("\n".join([ac[index:(index+frame_size[0])] for index in range(0, len(ac), frame_size[0])]))
            else:
                break
        capture.release()
        return al
