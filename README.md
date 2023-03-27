# avplib
## Description
**AVP** - ASCII Video Player. Allows you to play any video as ASCII-art.

## Install
```
python -m pip install --upgrade avplib
```

## Usage
```
python -m avplib [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  cav      Play video files (*.mp4/*.avi/...)
  convert  Convert Video Files to ASCII Video File.
  play     Play ASCII Video.
```

```
python -m avplib cav [OPTIONS] VIDEO_PATH

  Play video files (*.mp4/*.avi/...)

Options:
  -r, --res <INTEGER INTEGER>...  Resolution of the terminal of the video to
                                  be played.  [default: 0, 0]
  --fps INTEGER RANGE             FPS at which the video will be played back.
                                  [default: 30; 1<=x<=120]
  -th, --threading                Enable on threading processing.
  -na, --no_audio                 Disable audio playback.
  -y, --yes                       Disable playback confirmation.
  --help                          Show this message and exit.
```

```
python -m avplib convert [OPTIONS] FROM_VIDEO_PATH TO_VIDEO_PATH

  Convert Video Files to ASCII Video File.

Options:
  -r, --res <INTEGER INTEGER>...  Resolution for conversion (does not change
                                  after conversion).  [default: 118, 30]
  --fps INTEGER RANGE             FPS for conversion (does not change after
                                  conversion).  [default: 30; 1<=x<=120]
  -th, --threading                Enable on threading processing.
  -ar, --auto_res                 Automatically detection resolution.
  --help                          Show this message and exit.
```

```
python -m avplib play [OPTIONS] ASCII_VIDEO_PATH

  Play ASCII Video.

Options:
  -na, --no_audio  Disable audio playback.
  -y, --yes        Disable playback confirmation.
  --help           Show this message and exit.
```
