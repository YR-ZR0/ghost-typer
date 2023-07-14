# ghost-typer

This is a python script using [guillaumekln/faster-whisper](https://github.com/guillaumekln/faster-whisper) to type with your voice.
After you start the script select your sound device by typing its name or a unique string that identifies it e.g. if you device is listed as Yeti Blue USB Pulse, you can type Yeti USB and that will select it then you just press **F12** to start/stop recording. After the record is finished, it will type what you said starting at the current cursor position in any editor,input field etc.

# Setup Instructions

**Step 1 (Linux - Ubuntu,Debian):**

    sudo apt-get install python3 python3-pip git ffmpeg

**Step 1 (Windows):**

- Download ffmpeg from https://ffmpeg.org/ , unpack it and paste "ffmpeg.exe" in this folder
- Download and Install git from https://git-scm.com/download/win
- Download and Install python3 from https://www.python.org/downloads/windows/

**Step 1 (MAC OS - not tested):**

Download and Install ffmpeg, git and python3

**Step 2:**

    pip install -r requirements.txt

**Step 3:**

    python3 whisper-typer-tool.py
## TODO
- [ ] Make the transcription realtime by chunking audio
