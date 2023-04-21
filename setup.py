import os
from pathlib import Path
from typing import List, Union
import setuptools

def globalizer(path: Union[str, Path]) -> List[Path]:
    assert isinstance(path, str) or isinstance(path, Path)
    path, files = Path(path), []
    if path.is_dir():
        for i in path.iterdir():
            if i.is_dir(): files += globalizer(i)
            elif i.is_file(): files.append(i)
    elif path.is_file(): files.append(path)
    return files

# * This setup
setuptools.setup(
    name="avplib",
    version="1.4.6",
    description='AVP - ASCII Video Player. Allows you to play any video as ASCII-art.',
    keywords=["avplib"],
    packages=setuptools.find_packages(),
    author_email='semina054@gmail.com',
    url="https://github.com/romanin-rf/avplib",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    package_data={
        "avplib": [
            str(i.absolute()) for i in globalizer(os.path.join(os.path.dirname(__file__), "avplib"))
        ]
    },
    author='ProgrammerFromParlament',
    license='MIT',
    install_requires=["click", "rich", "soundfile", "opencv-python", "pillow", "pygame", "fpstimer", "ffmpeg", "moviepy", "numpy"],
    setup_requires=["click", "rich", "soundfile", "opencv-python", "pillow", "pygame", "fpstimer", "ffmpeg", "moviepy", "numpy"]
)