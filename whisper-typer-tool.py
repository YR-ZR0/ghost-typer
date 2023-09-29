"""
Uses OpenAi Whisper to transcribe text and types it using pynput
"""

import configparser
import os
import queue
import threading
import time

import numpy  # Make sure NumPy is loaded before it is used in the callback
import pystray
import soundfile as sf
import sounddevice as sd
from faster_whisper import WhisperModel
from pynput import keyboard
from PIL import Image, ImageDraw

assert numpy  # avoid "imported but unused" message (W0611)


# create a ConfigParser object
config = configparser.ConfigParser()

# read the preferences from the file
config.read("prefs.ini", encoding="utf-8")
device_index = config.get("audio", "device_index", fallback=None)
model_size = config.get("model", "model_size", fallback=None)


def create_image(width, height, color1):
    # Generate an image and draw a pattern
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    # calculate center of the image
    center_x = width // 2
    center_y = height // 2

    # calculate radius of the ellipse
    radius = min(center_x, center_y) - 10

    # calculate bounding box of the ellipse
    left = center_x - radius
    top = center_y - radius
    right = center_x + radius
    bottom = center_y + radius

    dc.ellipse((left, top, right, bottom), fill=color1)

    return image


if not device_index:
    print(sd.query_devices())
    device_index = input("Enter the device index: ")
    config["audio"] = {"device_index": device_index}
if not model_size:
    model_size = input("Enter the model size (tiny, base, small, medium, large): ")
    config["model"] = {"model_size": model_size}

with open("prefs.ini", "w", encoding="utf-8") as configfile:
    config.write(configfile)

print(f"loading model {model_size}...")
# load model
MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
selected = sd.query_devices(device_index)
sd.default.samplerate = int(selected["default_samplerate"])
sd.default.device = selected["index"]

# sd.play(loaded, fs)
print(f"{model_size} model loaded")
FILE_READY_COUNTER = 0
STOP_RECORDING = False
IS_RECORDING = False
pykeyboard = keyboard.Controller()
icon = pystray.Icon("GhostTyper", icon=create_image(64, 64, "red"))
icon.run_detached()


def transcribe_speech():
    """
    Handles the main speech transcription
    """
    i = 1
    print("ready - start transcribing with F12 ...\n")
    while True:
        while FILE_READY_COUNTER < i:
            time.sleep(0.01)
        result, _ = MODEL.transcribe(
            "test" + str(i) + ".wav", beam_size=5, word_timestamps=False
        )
        result = list(result)
        for element in result:
            try:
                pykeyboard.type(element.text)
                time.sleep(0.0025)
            except pykeyboard.InvalidCharacterException:
                print("empty or unknown symbol")
        os.remove("test" + str(i) + ".wav")
        i = i + 1


# keyboard events
PRESSED = set()

COMBINATIONS = [
    {
        "keys": [
            {keyboard.Key.f12},
        ],
        "command": "start record",
    },
]


# record audio
def record_speech():
    """
    Set up the audio device and gather speech into
    a WAV file for later processing
    """
    global FILE_READY_COUNTER
    global STOP_RECORDING
    global IS_RECORDING

    IS_RECORDING = True
    device_info = sd.query_devices(device_index)
    channels = device_info["max_input_channels"]

    frames = queue.Queue()  # Initialize a queue to store frames

    print("Start recording...\n")

    icon.icon = create_image(64, 64, "green")
    icon._update_icon()

    def callback(indata):
        frames.put(indata.copy())

    with sd.InputStream(device=device_index, channels=channels, callback=callback):
        while STOP_RECORDING is False:
            time.sleep(0.1)
    print("Finish recording")
    icon.icon = create_image(64, 64, "red")
    icon._update_icon()

    # Convert the frames queue to a list
    frames_list = list(frames.queue)

    # Concatenate the recorded frames
    frames_concatenated = numpy.concatenate(frames_list)

    # Save the recorded data as a WAV file using soundfile library
    filepath = f"test{str(FILE_READY_COUNTER + 1)}.wav"
    sf.write(filepath, frames_concatenated, samplerate=sd.default.samplerate)

    STOP_RECORDING = False
    IS_RECORDING = False
    FILE_READY_COUNTER = FILE_READY_COUNTER + 1


# ------------

# transcribe speech in infinite loop
t2 = threading.Thread(target=transcribe_speech)
t2.start()


def on_press(key):
    """
    Get pressed key
    """
    PRESSED.add(key)


def on_release(_key):
    """
    get released key
    """
    global PRESSED
    global STOP_RECORDING
    global IS_RECORDING
    for commandkeys in COMBINATIONS:
        for keys in commandkeys["keys"]:
            if keys.issubset(PRESSED):
                if (
                    commandkeys["command"] == "start record"
                    and STOP_RECORDING is False
                    and IS_RECORDING is False
                ):
                    mainthread = threading.Thread(target=record_speech)
                    mainthread.start()
                else:
                    if (
                        commandkeys["command"] == "start record"
                        and IS_RECORDING is True
                    ):
                        STOP_RECORDING = True
                PRESSED = set()


with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    try:
        listener.join()
    except KeyboardInterrupt:
        print("Exiting...")
        listener.stop()
        os._exit(1)
