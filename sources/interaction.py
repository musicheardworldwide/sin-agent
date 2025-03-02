
from sources.text_to_speech import Speech
from sources.utility import pretty_print
from sources.router import AgentRouter
from sources.speech_to_text import AudioTranscriber, AudioRecorder

class Interaction:
    def __init__(self, agents,
                 tts_enabled: bool = True,
                 stt_enabled: bool = True,
                 recover_last_session: bool = False):
        self.tts_enabled = tts_enabled
        self.agents = agents
        self.current_agent = None
        self.router = AgentRouter(self.agents)
        self.speech = Speech()
        self.is_active = True
        self.last_query = None
        self.last_answer = None
        self.ai_name = self.find_ai_name()
        self.tts_enabled = tts_enabled
        self.stt_enabled = stt_enabled
        if stt_enabled:
            self.transcriber = AudioTranscriber(self.ai_name, verbose=False)
            self.recorder = AudioRecorder()
        if tts_enabled:
            self.speech.speak("Hello Sir, we are online and ready. What can I do for you ?")
        if recover_last_session:
            self.recover_last_session()
    
    def find_ai_name(self) -> str:
        ai_name = "jarvis"
        for agent in self.agents:
            if agent.role == "talking":
                ai_name = agent.agent_name
                break
        return ai_name
    
    def recover_last_session(self):
        for agent in self.agents:
            agent.memory.load_memory()

    def is_active(self):
        return self.is_active
    
    def read_stdin(self) -> str:
        buffer = ""

        while buffer == "" or buffer.isascii() == False:
            try:
                buffer = input(f">>> ")
            except EOFError:
                return None
            if buffer == "exit" or buffer == "goodbye":
                return None
        return buffer
    
    def transcription_job(self):
        self.recorder = AudioRecorder()
        self.transcriber = AudioTranscriber(self.ai_name, verbose=False)
        self.transcriber.start()
        self.recorder.start()
        self.recorder.join()
        self.transcriber.join()
        query = self.transcriber.get_transcript()
        return query

    def get_user(self):
        if self.stt_enabled:
            query = self.transcription_job()
        else:
            query = self.read_stdin()
        if query is None:
            self.is_active = False
            self.last_query = "Goodbye (exit requested by user, dont think, make answer very short)"
            return None
        self.last_query = query
        return query
    
    def think(self):
        if self.last_query is None:
            return
        agent = self.router.select_agent(self.last_query)
        if self.current_agent != agent:
            self.current_agent = agent
            # get history from previous agent
            self.current_agent.memory.push('user', self.last_query)
        self.last_answer, _ = agent.process(self.last_query, self.speech)
    
    def show_answer(self):
        if self.last_query is None:
            return
        self.current_agent.show_answer()
        if self.tts_enabled:
            self.speech.speak(self.last_answer)

