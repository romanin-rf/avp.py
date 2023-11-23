import os
import cv2
import time
import queue
import moviepy.editor as mp
import soundfile as sf
from PIL import Image
from io import BufferedReader, BytesIO
from tempfile import NamedTemporaryFile
from threading import Thread
try: 
    from multiprocessing import Process, Pipe
    from multiprocessing.connection import PipeConnection
    init_multiprocessing = True
except:
    init_multiprocessing = False
# > Typing
from typing import Literal, Any, Optional, Union, TypeVar, Generic, Tuple, List
# > Local Imports
from .units import ASCII_CHARS_GRADIENTION, ASCII_CHARS

# ! Types
DT = TypeVar('DT')
PDT = TypeVar('PDT')

# ! Temp Detected
class TempDetected:
    def __init__(self) -> None:
        self.files = []
    def append(self, path: str) -> None: self.files.append(path)
    def clear(self) -> None:
        for i in self.files:
            try: os.remove(i)
            except: pass

# > Initilation
TEMP_DETECTOR = TempDetected()

# > Functions
def _callback(complited: int, total: int): ...

def generate_ascii_chars_gradient(ascii_chars: List[str]=ASCII_CHARS) -> List[str]:
    ascii_chars_gradient_k = int(256 / len(ascii_chars)) + 1
    return [ascii_chars[i // ascii_chars_gradient_k] for i in range(0, 257)]

def generate_ascii_frame(image_frame, frame_size: Tuple[int, int], ascii_chars_gradient: List[str]=ASCII_CHARS_GRADIENTION) -> str:
    ac = "".join([ascii_chars_gradient[pixel] for pixel in Image.fromarray(image_frame).convert("L").resize(frame_size).getdata()])
    return "\n".join([ac[index:(index+frame_size[0])] for index in range(0, len(ac), frame_size[0])])

# > Classes
class ProgressiveList(Generic[DT, PDT]):
    def __init__(
        self,
        max_size: int=256,
        pass_data: Optional[PDT]=None
    ) -> None:
        assert isinstance(max_size, int)
        self.max_size: int = max_size
        self.pass_data: PDT = pass_data
        self.data: List[Union[DT, PDT]] = [self.pass_data for i in range(0, self.max_size)]
    
    def __repr__(self) -> str: return self.data.__repr__()
    def __str__(self) -> str: return self.__repr__()
    def __getitem__(self, key: int) -> Union[DT, PDT]: return self.data[key]
    def __setitem__(self, key: int, value: DT) -> None: self.data[key] = value
    def __delitem__(self, key: int) -> None: self.data[key] = None

    def count_pass(self) -> int:
        c = 0
        for i in self.data:
            c += (1 if i == self.pass_data else 0)
        return c
    
    def count_busy(self) -> int:
        c = 0
        for i in self.data:
            c += (1 if i != self.pass_data else 0)
        return c
    
    def clear(self) -> None:
        self.data = [self.pass_data for i in range(0, self.max_size)]
    
    def to_list(self) -> List[DT]:
        datas = []
        for i in self.data:
            if i != self.pass_data:
                datas.append(i)
        return datas

# ! Handlers
class ThreadingFrameHandler:
    def __init__(
        self,
        frames_count: int,
        frame_size: Tuple[int, int],
        callback=_callback,
        ascii_chars_gradient: List[str]=ASCII_CHARS_GRADIENTION
    ) -> None:
        self.frames_count = frames_count
        self.frame_size = frame_size
        self.pl: ProgressiveList[str, None] = ProgressiveList(frames_count)
        self.done = 1
        self.callback = callback
        self.ascii_chars_gradient = ascii_chars_gradient
    
    def _gaf(self, idx: int, data: Tuple[bool, Any]) -> None:
        ret, image_frame = data
        if ret:
            self.pl[idx] = generate_ascii_frame(image_frame, self.frame_size, self.ascii_chars_gradient)
        self.done += 1
        self.callback(self.done, self.frames_count)
    
    def get_acsii_frame(self, idx: int, data: Tuple[bool, Any]) -> None:
        Thread(target=self._gaf, args=(idx, data)).start()

if init_multiprocessing:
    class MultiprocessingFrameHandler:
        def __init__(
            self,
            frames_count: int,
            frame_size: Tuple[int, int],
            callback=_callback
        ) -> None:
            self.frames_count = frames_count
            self.frame_size = frame_size
            self.queue: queue.Queue[Tuple[int, bool, Any]] = queue.Queue()
            self.pl: ProgressiveList[str, None] = ProgressiveList(frames_count)
            self.done = 1
            self.callback = callback
            self.cores = os.cpu_count() or 1
            self.processes_started = 0
        
        @staticmethod
        def _gaf(connection: PipeConnection) -> None:
            frame_size: Tuple[int, int] = connection.recv()
            while True:
                data: Union[Tuple[int, bool, Any], Literal[0]] = connection.recv()
                if data == 0:
                    break
                idx, ret, image_frame = data
                if ret:
                    ac = "".join([ASCII_CHARS_GRADIENTION[pixel] for pixel in Image.fromarray(image_frame).convert("L").resize(frame_size).getdata()])
                    text_frame = "\n".join([ac[index:(index+frame_size[0])] for index in range(0, len(ac), frame_size[0])])
                else:
                    text_frame = None
                connection.send((idx, text_frame))
        
        def _gaf_control_thread(self, pipe: PipeConnection) -> None:
            self.processes_started += 1
            pipe.send(self.frame_size)
            while not self.queue.empty():
                pipe.send(self.queue.get())
                data: Tuple[int, Optional[str]] = pipe.recv()
                if data[1] is not None:
                    self.pl[data[0]] = data[1]
                self.done += 1
                self.callback(self.done, self.frames_count)
            pipe.send(0)
            self.processes_started -= 1
        
        def add_task_data(self, idx: int, ret: bool, image_frame: Any) -> None:
            self.queue.put((idx, ret, image_frame))
        
        def proccessing(self) -> None:
            for i in range(self.cores):
                send_conn, recv_conn = Pipe()
                Process(target=self._gaf, args=(recv_conn,)).start()
                Thread(target=self._gaf_control_thread, args=(send_conn,), daemon=True).start()
            while self.processes_started > 0:
                time.sleep(0.01)

# ! Main Class
class AVP:
    def __init__(self, fp, ascii_chars: List[str]=ASCII_CHARS) -> None:
        self.ascii_chars_gradient = generate_ascii_chars_gradient(ascii_chars)
        if isinstance(fp, str):
            self.path = os.path.abspath(fp)
        elif isinstance(fp, bytes):
            with NamedTemporaryFile("wb", delete=False) as tempfile:
                tempfile.write(fp)
                self.path = os.path.abspath(tempfile.name)
                TEMP_DETECTOR.append(self.path)
        elif isinstance(fp, BufferedReader):
            self.path = os.path.abspath(fp.name)
        else:
            raise TypeError(f"The variable type 'fp' does not accept the type {type(fp)}")
        self.video = mp.VideoFileClip(self.path)
    
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
            TEMP_DETECTOR.append(filepath)
        self.video.write_videofile(filename=filepath, fps=fps, codec="mpeg4")
    
    def get_audio(self, tp: Literal["file", "bytes", "array"], filepath=None):
        if tp == "file":
            if filepath is None:
                with NamedTemporaryFile("wb", suffix=".mp3", delete=False) as tempfile:
                    filepath = os.path.abspath(tempfile.name)
                    TEMP_DETECTOR.append(filepath)
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
                al.append(generate_ascii_frame(image_frame, frame_size, self.ascii_chars_gradient))
            else:
                break
        capture.release()
        return al
    
    def get_ascii_frames_threading(self, frame_size, callback=_callback):
        capture = cv2.VideoCapture(self.path)
        capture.set(1, 1)
        frames_count = self.get_frames_count()
        thfn = ThreadingFrameHandler(frames_count, frame_size, callback, self.ascii_chars_gradient)
        for i in range(1, frames_count):
            ret, image_frame = capture.read()
            thfn.get_acsii_frame(i, (ret, image_frame))
        while thfn.frames_count > thfn.done:
            time.sleep(0.01)
        capture.release()
        return thfn.pl.to_list()
    
    def get_ascii_frames_multiprocessing(self, frame_size, callback=_callback):
        capture = cv2.VideoCapture(self.path)
        capture.set(1, 1)
        frames_count: int = self.get_frames_count()
        mpfn = MultiprocessingFrameHandler(frames_count, frame_size, callback)
        for i in range(1, frames_count):
            ret, image_frame = capture.read()
            mpfn.add_task_data(i, ret, image_frame)
        mpfn.proccessing()
        return mpfn.pl.to_list()
