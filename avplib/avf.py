import json
import pathlib
from zipfile import ZipFile, ZIP_DEFLATED
from tempfile import NamedTemporaryFile
from typing import Tuple, List, Dict, Any, Literal, Union, TypeVar
from .units import ASCII_CHARS

T = TypeVar("T")
D = TypeVar("D")

def removes(l: List[Union[T, D]], rl: List[D]) -> List[T]:
    for i in rl:
        for i in range(l.count(i)):
            try: l.remove(i)
            except: pass
    return l

class AVFile:
    def __init__(self, path: str, mode: Literal["r", "w"]="r") -> None:
        self.name = pathlib.Path(path)
        self.mode = mode
        if mode == "r":     avf_args = dict(mode=self.mode)
        elif mode == "w":   avf_args = dict(compression=ZIP_DEFLATED, compresslevel=9, mode=self.mode)
        self.fp = ZipFile(path, **avf_args)
    
    def set_info(
        self,
        title: str="",
        author: str="",
        fps: int=1,
        res: Tuple[int, int]=(1,1),
        exists_audio: bool=False,
        ascii_chars: List[str]=ASCII_CHARS
    ) -> None:
        self.fp.writestr(
            "info",
            json.dumps(
                {
                    "title": title,
                    "author": author,
                    "fps": fps,
                    "res": res,
                    "exists_audio": exists_audio,
                    "ascii_chars": ascii_chars
                }
            )
        )
    
    def get_info(self) -> Dict[str, Any]:
        return json.loads(self.fp.read("info"))
    
    def set_video(self, frames: List[str]=[]) -> None:
        self.fp.writestr(
            "video",
            "\r\n\r\n".join(frames)
        )
    
    def get_video(self) -> List[str]:
        return self.fp.read("video").decode(errors="ignore").split("\r\n\r\n")
    
    def set_audio_from_path(self, audio_path: str) -> None:
        self.fp.write(audio_path, "audio")
    
    def get_audio_path(self) -> str:
        with NamedTemporaryFile(delete=False) as audio_file:
            audio_file.write(self.fp.read("audio"))
        return audio_file.name
    
    def set_audio_from_bytes(self, audio: bytes) -> None:
        self.fp.writestr("audio", audio)
    
    def get_audio_bytes(self) -> bytes:
        return self.fp.read("audio")
    
    def close(self) -> None:
        self.fp.close()