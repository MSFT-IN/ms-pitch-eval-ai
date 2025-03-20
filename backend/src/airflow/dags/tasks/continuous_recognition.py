import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import os
import time
import json

def extract_data(): 
    load_dotenv()  # to load variables from .env

    ########## setting ##########
    # set variables
    SPEECH_KEY = os.getenv("SPEECH_KEY")
    SERVICE_REGION = os.getenv("SERVICE_REGION")
    AUDIO_FILE = os.getenv("AUDIO_FILE")

    # check file type
    if not AUDIO_FILE.lower().endswith(".wav"):
        raise ValueError("Only .wav files are allowed.")

    # set speech config
    speech_config = speechsdk.SpeechConfig(
        subscription=SPEECH_KEY, 
        region=SERVICE_REGION
    )
    speech_config.output_format = speechsdk.OutputFormat.Detailed

    # set audio config
    audio_config = speechsdk.audio.AudioConfig(filename=AUDIO_FILE)

    # set pronunciation config
    pronunciation_config = speechsdk.PronunciationAssessmentConfig( 
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark, 
        granularity=speechsdk.PronunciationAssessmentGranularity.Word, 
        enable_miscue=True
    ) 
    pronunciation_config.enable_prosody_assessment()

    # set speech recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, 
        language="ko-KR", 
        audio_config=audio_config
    )
    pronunciation_config.apply_to(speech_recognizer)

    # initial setting
    done = False
    word_accuracy_list = []
    accuracy_scores = []
    pron_scores = []
    fluency_scores = []

    ########## function ##########
    def stop_cb(evt: speechsdk.SessionEventArgs):
        nonlocal done
        done = True

    def recognized(evt: speechsdk.SpeechRecognitionEventArgs):
        nonlocal word_accuracy_list, accuracy_scores, pron_scores, fluency_scores
        pronunciation_result = speechsdk.PronunciationAssessmentResult(evt.result)

        # recognize
        json_result = evt.result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
        jo = json.loads(json_result)
        nb = jo["NBest"][0]
        words = nb['Words']

        recognized_words = [
            {word_data['Word']: word_data['PronunciationAssessment']['AccuracyScore']}
            for word_data in words
            if len(word_data['Word']) >= 3
        ]

        word_accuracy_list += recognized_words
        accuracy_scores.append(pronunciation_result.accuracy_score)
        pron_scores.append(pronunciation_result.pronunciation_score)
        fluency_scores.append(pronunciation_result.fluency_score)

        """
        # data during recognition
        print("Target Words: {}, Accuracy Score: {}, Pronunciation Score: {}, Fluency Score: {})".format(
                recognized_words,
                accuracy_scores,
                pron_scores,
                fluency_scores
        ))
        """

    # connect events by recognizer
    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # start continuous pronunciation assessment
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(0.5)
    speech_recognizer.stop_continuous_recognition()

    return {
        "avg_accuracy_score": round(sum(accuracy_scores) / len(accuracy_scores), 2), # pronunciation accuracy
        "avg_pron_score": round(sum(pron_scores) / len(pron_scores), 2), # overall score of the pronunciation quality
        "avg_fluency_score": round(sum(fluency_scores) / len(fluency_scores), 2), # fluency (native use of silent breaks)
        "bad_words": sorted(
            word_accuracy_list, key=lambda x: list(x.values())[0]
        )[:10]
    }