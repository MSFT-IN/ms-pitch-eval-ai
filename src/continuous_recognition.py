import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import os
import time
import difflib
import string
import json

def extract_data(): 
    load_dotenv()  # to load variables from .env

    ########## setting ##########
    # set variables
    SPEECH_KEY = os.getenv("SPEECH_KEY")
    SERVICE_REGION = os.getenv("SERVICE_REGION")
    AUDIO_FILE = os.getenv("AUDIO_FILE")

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
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme, 
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
    reference_text = ""
    recognized_words = []
    fluency_scores = []
    durations = []
    speech_rates = []
    confidence_scores = []
    startOffset = 0
    endOffset = 0

    ########## function ##########
    def stop_cb(evt: speechsdk.SessionEventArgs):
        nonlocal done
        done = True

    def recognized(evt: speechsdk.SpeechRecognitionEventArgs):
        nonlocal reference_text, recognized_words, fluency_scores, durations, startOffset, endOffset
        pronunciation_result = speechsdk.PronunciationAssessmentResult(evt.result)

        # recognize
        reference_text += evt.result.text + " "
        recognized_words += pronunciation_result.words

        fluency_scores.append(pronunciation_result.fluency_score)

        json_result = evt.result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
        jo = json.loads(json_result)
        nb = jo["NBest"][0]
        
        durations.extend([int(w["Duration"]) + 100000 for w in nb["Words"] if w["PronunciationAssessment"]["ErrorType"] == "None"])
        if startOffset == 0:
            startOffset = nb["Words"][0]["Offset"]
        endOffset = nb["Words"][-1]["Offset"] + nb["Words"][-1]["Duration"] + 100000

        speech_rate = len(pronunciation_result.words) / int(endOffset - startOffset)
        speech_rates.append(speech_rate)

        confidence_score = nb["Words"][0]["Confidence"]
        confidence_scores.append(confidence_score)

        # data during recognition
        print("Accuracy score: {}, pronunciation score: {}, completeness score : {}, fluency score: {}, speech rate: {}, confidence score: {}".format(
                pronunciation_result.accuracy_score, 
                pronunciation_result.pronunciation_score,
                pronunciation_result.completeness_score, 
                pronunciation_result.fluency_score,
                speech_rate * 10**7, # ms to s
                confidence_score
        ))

    # connect events by recognizer
    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # start continuous pronunciation assessment
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(0.5)
    speech_recognizer.stop_continuous_recognition()

    # convert reference_text to lower case, split to words, and remove punctuations
    reference_words = [w.strip(string.punctuation) for w in reference_text.lower().split()]

    # detect error words 
    diff = difflib.SequenceMatcher(None, reference_words, [x.word.lower() for x in recognized_words])
        
    final_words = []
    for tag, i1, i2, j1, j2 in diff.get_opcodes():
        if tag in ['insert', 'replace']:
            for word in recognized_words[j1:j2]:
                word._error_type = 'Insertion'
                final_words.append(word)
                
        if tag in ['delete', 'replace']:
            for word_text in reference_words[i1:i2]:
                word = speechsdk.PronunciationAssessmentWordResult({
                    'Word': word_text,
                    'PronunciationAssessment': {
                        'ErrorType': 'Omission',
                    }
                })
                final_words.append(word)
            
        if tag == 'equal':
            final_words += recognized_words[j1:j2]

    durations_sum = sum([d for w, d in zip(recognized_words, durations) if w.error_type == "None"])

    # calculate whole accuracy by averaging
    final_accuracy_scores = [word.accuracy_score for word in final_words if word.error_type != 'Insertion']
    accuracy_score = sum(final_accuracy_scores) / len(final_accuracy_scores)

    # re-calculate fluency score
    fluency_score = (durations_sum / (endOffset - startOffset) * 100) if startOffset > 0 else 0

    # calculate whole completeness score
    handled_final_words = [w.word for w in final_words if w.error_type != "Insertion"]
    completeness_score = len([w for w in final_words if w.error_type == "None"]) / len(handled_final_words) * 100
    completeness_score = min(completeness_score, 100)

    sorted_scores = sorted([accuracy_score, completeness_score, fluency_score])
    pronunciation_score = sorted_scores[0] * 0.4 + sorted_scores[1] * 0.3 + sorted_scores[2] * 0.3

    return {
        "pronunciation_score": round(pronunciation_score, 2),
        "accuracy_score": round(accuracy_score, 2),
        "completeness_score": round(completeness_score, 2),
        "fluency_score": round(fluency_score, 2),
        "speech_rate": round(sum(speech_rates) / len(speech_rates), 2),
        "confidence_score": round(sum(confidence_scores) / len(confidence_scores), 2)
    }
