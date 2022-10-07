import time
import numpy as np
import speech_recognition as sr
import random
import pyttsx3
import globals
from text import *
from failing import *

########################################################################
######################## FUNCTIONS ########################
########################################################################
## Basics


def initConv():
    """
    Function to initiliase recogniser and microphone
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    print("Microphone and recognizer initiliased")

    return [recognizer, microphone]


def initSpeak():
    engine = pyttsx3.init()
    return engine


def speak(engine, text):
    try:
        engine.say(text)
        # print('START speaking')
        engine.runAndWait()
        # print('DONE speaking')
    except Exception as e:
        errorloc(e)


def say(text):
    try:
        os.system(f"say {text}")
    except Exception as e:
        errorloc(e)


def listenConv(recognizer, microphone, speaker, PROMPT_LIMIT=5):
    for j in range(PROMPT_LIMIT):
        speech = recognize_speech_from_mic(recognizer, microphone)
        if speech["transcription"]:
            break
        if not speech["success"]:
            break

        print(speech)

        listen_again = "I didn't catch that, what did you say?"
        speak(speaker, listen_again)
    return speech


# if there was an error, stop the game
def error_conv(speech):
    if speech["error"]:
        raise Exception("ERROR: {}".format(speech["error"]))


def checkCorrect(speech, word):
    guess_is_correct = speech["transcription"].lower() == word.lower()

    return guess_is_correct


def sayCorrect(guess_is_correct):
    if guess_is_correct:
        print("Correct.")
    else:
        print("Please. Try again.\n")


#################################################################
####################### IBM watson ##############################
#################################################################

try:
    import pyaudio
except:
    pass
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource
from threading import Thread
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

try:
    from Queue import Queue, Full
except ImportError:
    from queue import Queue, Full

###############################################
#### Initalize queue to store the recordings ##
###############################################

# Create an instance of AudioSource
CHUNK = 1024
BUF_MAX_SIZE = CHUNK * 10


def audioInstance(BUF_MAX_SIZE=BUF_MAX_SIZE, CHUNK=CHUNK):
    q = Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK)))
    audio_source = AudioSource(q, True, True)
    return [audio_source, q]


###############################################
#### Prepare Speech to Text Service ########
###############################################

# initialize speech to text service
def initSpeech2Text():
    authenticator = IAMAuthenticator("TYpFrLihy3SW0rwX9X81j6MS9i3XyE1kzhWbVqmlYMuH")
    speech_to_text = SpeechToTextV1(authenticator=authenticator)
    speech_to_text.set_service_url(
        "https://api.eu-gb.speech-to-text.watson.cloud.ibm.com/instances/c0042364-1a14-4eb3-b499-d9945a8564bc"
    )
    return speech_to_text


# define callback for the speech to text service
class MyRecognizeCallback(RecognizeCallback):
    def __init__(self, answer):
        RecognizeCallback.__init__(self)
        # print(text)

    def on_transcription(self, transcript):
        # print('LISTENING IN INSIDE')
        # print(transcript)

        # listened = transcript[0]['transcript']
        # if any(x in listened for x in ['yes', 'yeah', 'no']):
        #     globals.test = 1

        pass

    def on_connected(self):
        print("Connection was successful")

    def on_error(self, error):
        print("Error received: {}".format(error))

    def on_inactivity_timeout(self, error):
        print("Inactivity timeout: {}".format(error))

    def on_listening(self):
        print("\nSERVICE IS LISTENING\n")

    def on_hypothesis(self, hypothesis):
        globals.hypothesis = hypothesis
        # print(hypothesis)
        pass

    def on_data(self, data):
        listened = data["results"][0]["alternatives"][0]["transcript"]
        # print(data)
        try:
            globals.confidence = data["results"][0]["alternatives"][0]["confidence"]
        except:
            pass

        if any(x in listened for x in ["yes", "yeah", "no"]):
            globals.answer = 1
            globals.listened = listened
            if any(x in globals.listened for x in ["yes", "yeah"]):
                globals.answered = 1
                print(globals.listened)
            elif any(x in globals.listened for x in ["no"]):
                globals.answered = 0
                print(globals.listened)

    def on_close(self):
        print("Connection closed")


# this function will initiate the recognize service and pass in the AudioSource
def recognize_yes_no_weboscket(speech_to_text, audio_source, text, *args):
    mycallback = MyRecognizeCallback(text)
    # print('Speech recognition on')
    speech_to_text.recognize_using_websocket(
        audio=audio_source,
        content_type="audio/l16; rate=44100",
        recognize_callback=mycallback,
        interim_results=True,
    )
    print("Speech recognition off")


###############################################
#### Prepare the for recording using Pyaudio ##
###############################################

# Variables for recording the speech
try:
    FORMAT = pyaudio.paInt16
except:
    pass
CHANNELS = 1
RATE = 44100

# define callback for pyaudio to store the recording in queue


def startAudioWatson():
    # instantiate pyaudio
    audio = pyaudio.PyAudio()
    return audio


def openStream(audio, q):
    def pyaudio_callback(in_data, frame_count, time_info, status):
        try:
            q.put(in_data)
            globals.frames.append(in_data)
            # print(in_data)
            # print('WE ARE HERE')
        except Full:
            pass  # discard
        return (None, pyaudio.paContinue)

    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        stream_callback=pyaudio_callback,
        start=False,
    )

    return stream


def terminateSpeechRecognition(stream, audio, audio_source):

    stream.stop_stream()
    stream.close()

    audio.terminate()
    audio_source.completed_recording()

    print("Speech recognition terminated")


##### Functions of functions


def testingSpeechCov(words, repeats):
    recognizer, microphone = initConv()
    list_ws = words * repeats
    random.shuffle(list_ws)
    for i in np.arange(len(list_ws)):
        temp_word = list_ws[i]
        print(f"Say: {temp_word}")
        speech = listenConv(recognizer, microphone)
        error_conv(speech)

        print("You said: {}".format(speech["transcription"]))

        bo_co = checkCorrect(speech, temp_word)

        sayCorrect(bo_co)


def recognize_speech_from_mic(recognizer, microphone):
    """Transcribe speech from recorded from `microphone`.

    Returns a dictionary with three keys:
    "success": a boolean indicating whether or not the API request was
               successful
    "error":   `None` if no error occured, otherwise a string containing
               an error message if the API could not be reached or
               speech was unrecognizable
    "transcription": `None` if speech could not be transcribed,
               otherwise a string containing the transcribed text
    """
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    # set up the response object
    response = {"success": True, "error": None, "transcription": None}

    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #     update the response object accordingly
    try:
        response["transcription"] = recognizer.recognize_sphinx(audio)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response
