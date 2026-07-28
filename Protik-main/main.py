import os
import eel

from engine.features import *
from engine.command import *
def start():
    
    eel.init("www")

    playAssistantSound()
    @eel.expose
    def init():
        subprocess.call([r'device.bat'])
        speak("Hello, Welcome Sir, How can i Help You")
        eel.hideStart()
        playAssistantSound()
    os.system('start msedge.exe --app="http://localhost:8000/index.html"')

    eel.start('index.html', mode=None, host='localhost', block=True)