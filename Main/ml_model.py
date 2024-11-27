import whisper
def audio_to_text(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]
    # For now, simulate a model response
    return f"The uploaded audio file '{audio_path}' has been successfully processed into text."