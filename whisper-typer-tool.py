"""
Uses OpenAi Whisper to transcribe text and types it using pynput
"""

import os
import threading
import time
import sounddevice as sd
import simpleaudio as sa
from pynput import keyboard
from faster_whisper import WhisperModel
import queue


import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback

assert numpy  # avoid "imported but unused" message (W0611)

print(sd.query_devices())
device_index = input("Enter the device name: ")
# model selection -> (tiny base small medium large)
model_size = "medium"
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


def transcribe_speech():
    """
    Handles the main speech transcription
    """
    i = 1
    print("ready - start transcribing with F12 ...\n")
    while True:
        while FILE_READY_COUNTER < i:
            time.sleep(0.01)
        result, info = MODEL.transcribe("test" + str(i) + ".wav", beam_size=5, word_timestamps=False)
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
    device_name = device_info["name"]
    channels = device_info["max_input_channels"]

    print(f"Recording from '{device_name}'...")
    print(f"Channels: {sd.default.channels}")
    print(f"Sample Rate: {sd.default.samplerate}")

    frames = queue.Queue()  # Initialize a queue to store frames

    print("Start recording...\n")

    def callback(indata, frame_count, time_info, status):
        frames.put(indata.copy())

    with sd.InputStream(device=device_index, channels=channels, callback=callback):
        while STOP_RECORDING is False:
            time.sleep(0.1)
    print("Finish recording")

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
