# Example 10.14 Text to Speech
# pip install pyttsx3
import pyttsx3
import sys
engine = pyttsx3.init()


def speak(text='hi'):
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    text = sys.argv[1]
    speak(text)
