import random
import sys
import torch
import gc
import os
import json
import speech_recognition as sr

from openchat.base.envs.base import BaseEnvironment
from openchat.base import (
    BaseAgent,
    ConvAI2Agent,
    WizardOfWikipediaAgent,
    SingleTurn,
    PromptAgent,
)

from openchat.utils.terminal_utils import (
    cprint,
    cinput,
    Colors,
)


class InteractiveEnvironment(BaseEnvironment):

    def __init__(
        self,
        user_color=Colors.GREEN,
        bot_color=Colors.YELLOW,
        special_color=Colors.BLUE,
        system_color=Colors.CYAN,
    ):
        super().__init__()
        self.user_id = "dummy_value"
        self.user_color = user_color
        self.bot_color = bot_color
        self.special_color = special_color
        self.system_color = system_color
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.PROMPT_LIMIT = 5
        #self.path_to_script = os.path.dirname(r"C:\Users\Thomas\AppData\Roaming\xVASynth\realTimeTTS")
        #self.my_log_filename = os.path.join(self.path_to_script, "xVASynthText.json")
        self.persona_settings = ["My name is Bob.", "I am a skooma dealer.", "I am addicted to skooma.", "I am an imperial male.", "I live in the land of Skyrim.", "I live in the village of Riverwood",".done"]

    def start(self, agent: BaseAgent):

        cprint(
            f"\n[SYSTEM]: Let's talk with [{agent.name.upper()}].\n"
            f"[SYSTEM]: Enter '.exit', if you want to exit chatting.\n"
            f"[SYSTEM]: Enter '.reset', if you want reset all histories.\n",
            color=self.system_color)

        self.clear_histories(self.user_id)
        gc.enable()

        while True:
            torch.cuda.empty_cache()
            if self.is_empty(self.user_id):
                pre_dialog_output = self.pre_dialog_for_special_tasks(agent)

            if isinstance(agent, PromptAgent):
                user_name, bot_name = pre_dialog_output
            for j in range(self.PROMPT_LIMIT):
                guess = self.recognize_speech_from_mic(self.recognizer, self.microphone)
                if guess["transcription"]:
                    break
                if not guess["success"]:
                    break

            if guess["error"]:
                user_message = guess["error"]
            else:
                user_message = guess["transcription"]

            if user_message == ".exit":
                cprint(
                    f"[SYSTEM]: good bye.\n",
                    color=self.system_color,
                )
                exit(0)
                sys.exit(0)

            if user_message == ".reset":
                cprint(
                    f"[SYSTEM]: reset all histories.\n",
                    color=self.system_color,
                )
                self.clear_histories(self.user_id)
                continue

            if isinstance(agent, WizardOfWikipediaAgent):
                user_message = agent.retrieve_knowledge(user_message)

            if isinstance(agent, PromptAgent):
                user_message = f"{user_name}: {user_message} {bot_name}:"

            if isinstance(agent, SingleTurn):
                model_input = user_message
            else:
                model_input = self.make_model_input(
                    self.user_id,
                    user_message,
                    agent,
                )

            self.add_user_message(self.user_id, user_message)

            if isinstance(agent, PromptAgent):
                bot_message = agent.predict(
                    model_input,
                    person_1=user_name,
                    person_2=bot_name,
                )["output"]

            else:
                bot_message = agent.predict(model_input)["output"]

            cprint(
                f"[{agent.name.upper()}]: {bot_message}",
                color=self.bot_color,
            )
            xVAJsonText = {
                "done": False,
                "ffmpeg_pitchMult": 1,
                "ffmpeg_tempo": 1.0,
                "gameId": "skyrim",
                "pad_end": 200,
                "pad_start": 0,
                "text": str({bot_message})[1:-1],
                "use_ffmpeg": True,
                "voiceId": "sk_maleslycynical",
                "vol": 0.9990000396966935
            }
            logger = open(r"F:\SteamLibrary\steamapps\common\SkyrimVR\Data\Sound\fx\ConvAiFollower\xVASynthText.json","w")
            logger.write(json.dumps(xVAJsonText,indent=4))
            logger.close()


            self.add_bot_message(self.user_id, bot_message)
            gc.collect()

    def pre_dialog_for_special_tasks(self, agent):
        if isinstance(agent, ConvAI2Agent):
            return self.pre_dialog_for_convai2(agent)

        if isinstance(agent, WizardOfWikipediaAgent):
            return self.pre_dialog_for_wow(agent)

        if isinstance(agent, PromptAgent):
            return self.pre_dialog_for_prompt(agent)

    def pre_dialog_for_prompt(self, agent):
        user_name = cinput(
            f"[YOUR NAME]: ",
            color=self.special_color,
        )

        bot_name = cinput(
            f"[{agent.name.upper()}'s NAME]: ",
            color=self.special_color,
        )

        agent.name = bot_name

        cprint(
            f"\n[SYSTEM]: Please input story you want.\n"
            f"[SYSTEM]: The story must contains '{user_name}' and '{bot_name}'.\n",
            color=self.system_color)

        story = cinput(
            "[STORY]: ",
            color=self.special_color,
        )

        while (user_name not in story) or (bot_name not in story):
            cprint(
                f"\n[SYSTEM]: Please input story you want.\n"
                f"[SYSTEM]: The story MUST contains '{user_name}' and '{bot_name}'.\n",
                color=self.system_color)

            story = cinput(
                "[STORY]: ",
                color=self.special_color,
            )

        cprint(
            f"[STORY]: Story setting complete.\n",
            color=self.special_color,
        )

        story += f" {user_name} and {bot_name} start talking. "
        story += f"{user_name}: Hello {bot_name}. "
        story += f"{bot_name}: Hi {user_name}. "

        agent.add_prompt(
            self.histories,
            self.user_id,
            story,
        )

        return user_name, bot_name

    def pre_dialog_for_convai2(self, agent):
        cprint(
            f"[SYSTEM]: Please input [{agent.name.upper()}]'s persona.\n"
            f"[SYSTEM]: Enter '.done' if you want to end input persona.\n",
            color=self.system_color)

        for x in self.persona_settings:
        #while True:
            #_persona = cinput(
             #   f"[{agent.name.upper()}'s PERSONA]: ",
              #  color=self.special_color,
            #)

            _persona = x

            if _persona == ".done":
                cprint(
                    f"[{agent.name.upper()}'s PERSONA]: Persona setting complete.\n",
                    color=self.special_color,
                )
                break
            else:
                agent.add_persona(
                    self.histories,
                    user_id=self.user_id,
                    text=_persona,
                )

    def pre_dialog_for_wow(self, agent):
        cprint(
            f"[SYSTEM]: Please input topic for Wizard of wikipedia.\n"
            f"[SYSTEM]: Enter '.topic' if you want to check random topic examples.\n",
            color=self.system_color)

        while True:
            _topic = cinput(
                "[TOPIC]: ",
                color=self.special_color,
            )

            if _topic == ".topic":
                random_list = agent.topic_list
                random.shuffle(random_list)
                random_list = random_list[:4]

                _topic = cprint(
                    f"[TOPIC]: {random_list}\n",
                    color=self.special_color,
                )

            else:
                if _topic in agent.topic_list:
                    cprint(
                        f"[TOPIC]: Topic setting complete.\n",
                        color=self.special_color,
                    )
                    agent.set_topic(_topic)
                    break
                else:
                    _topic = cprint(
                        f"[TOPIC]: Wrong topic: {_topic}. Please enter validate topic.\n",
                        color=self.special_color,
                    )

    def recognize_speech_from_mic(self, recognizer, microphone):

        if not isinstance(recognizer, sr.Recognizer):
            raise TypeError("`recognizer` must be `Recognizer` instance")

        if not isinstance(microphone, sr.Microphone):
            raise TypeError("`microphone` must be `Microphone` instance")

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        response = {
            "success": True,
            "error": None,
            "transcription": None
        }

        try:
            response["transcription"] = recognizer.recognize_google(audio)
        except sr.RequestError:
            response["success"] = False
            response["error"] = "API unavailable"
        except sr.UnknownValueError:
            response["error"] = "Unable to recognize speech"

        return response
