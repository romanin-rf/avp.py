import os
import cv2
import time
import moviepy.editor as mp
import soundfile as sf
from PIL import Image
from io import BufferedReader, BytesIO
from tempfile import NamedTemporaryFile
from threading import Thread
# > Typing
from typing import Literal, Any, Optional, Tuple
# > Local Imports
from .units import ASCII_CHARS_GRADIENTION

# > Functions
def _callback(complited: int, total: int): ...

# > Classes
class ProgressiveList:
    def __init__(
        self,
        max_size: int=256,
        pass_data: Optional[Any]=None
    ) -> None:
        assert isinstance(max_size, int)
        self.max_size: int = max_size
        self.pass_data = pass_data
        self.data = [self.pass_data for i in range(0, self.max_size)]
    
    def __repr__(self) -> str: return self.data.__repr__()
    def __str__(self) -> str: return self.__repr__()
    def __getitem__(self, key: int) -> Any: return self.data[key]
    def __setitem__(self, key: int, value: Any) -> Any: self.data[key] = value
    def __delitem__(self, key: int) -> Any: self.data[key] = None

    def count_pass(self) -> int:
        c = 0
        for i in self.data: c += (1 if i == self.pass_data else 0)
        return c
    
    def count_busy(self) -> int:
        c = 0
        for i in self.data: c += (1 if i != self.pass_data else 0)
        return c
    
    def clear(self) -> None: self.data = [self.pass_data for i in range(0, self.max_size)]

class ThreadingFrameHandler:
    def __init__(self, frames_count: int, frame_size: Tuple[int, int], callback=_callback) -> None:
        self.frames_count = frames_count
        self.frame_size = frame_size
        self.pl = ProgressiveList(frames_count)
        self.done = 1
        self.callback = callback
    
    def _gaf(self, idx: int, data: Tuple[bool, Any]) -> None:
        ret, image_frame = data
        if ret:
            ac = "".join([ASCII_CHARS_GRADIENTION[pixel] for pixel in Image.fromarray(image_frame).convert("L").resize(self.frame_size).getdata()])
            self.pl[idx] = "\n".join([ac[index:(index+self.frame_size[0])] for index in range(0, len(ac), self.frame_size[0])])
        self.done += 1
        self.callback(self.done, self.frames_count)
    
    def get_acsii_frame(self, idx: int, data: Tuple[bool, Any]) -> None:
        Thread(target=self._gaf, args=(idx, data)).start()

# > Main Class
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
    
    def get_ascii_frames_threading(self, frame_size, callback=_callback):
        capture = cv2.VideoCapture(self.path)
        capture.set(1, 1)
        frames_count = self.get_frames_count()
        
        thfn = ThreadingFrameHandler(frames_count, frame_size, callback)
        
        for i in range(1, frames_count):
            ret, image_frame = capture.read()
            thfn.get_acsii_frame(i, (ret, image_frame))
        
        while thfn.frames_count > thfn.done: time.sleep(0.01)
        
        return thfn.pl.data
