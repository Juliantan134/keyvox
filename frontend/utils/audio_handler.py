import os
import wave
import pyaudio
import threading
import frontend_config as config
from tkinter import messagebox

# PyAudio format constant
FORMAT = pyaudio.paInt16

def record_audio_blocking(app, filepath, duration=4):
    """Records audio for a fixed duration, blocking the main thread until complete."""
    stream = app.pyaudio_instance.open(
        format=FORMAT,
        channels=config.CHANNELS,
        rate=config.RATE,
        input=True,
        frames_per_buffer=config.CHUNK
    )
    
    frames = []
    print(f"[*] Starting {duration}-second blocking recording...")
    
    for _ in range(0, int(config.RATE / config.CHUNK * duration)):
        try:
            data = stream.read(config.CHUNK, exception_on_overflow=False)
            frames.append(data)
        except IOError as e:
            print(f"An error occurred during recording: {e}")
            break

    print("[*] Blocking recording finished.")
    stream.stop_stream()
    stream.close()
    
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(config.CHANNELS)
        wf.setsampwidth(app.pyaudio_instance.get_sample_size(FORMAT))
        wf.setframerate(config.RATE)
        wf.writeframes(b''.join(frames))

def toggle_recording(app, event=None):
    """Starts or stops the enrollment recording thread."""
    if app.is_recording:
        app.is_recording = False
        app.recording_status_label.config(text="Saving...")
    else:
        app.is_recording = True
        app.next_btn.config(state="disabled")
        app.recording_status_label.config(text="Recording... Click mic to stop.")
        app.recording_thread = threading.Thread(target=_record_audio_thread, args=(app,), daemon=True)
        app.recording_thread.start() 
    print("toggle_recording")
    messagebox.showinfo("TRIAL 1", "Trial 2 3 4 5 ")

def _record_audio_thread(app):
    """The target function for the recording thread."""
    username = app.new_enrollment_data.get('username', 'user')
    filepath = os.path.join(config.AUDIO_DIR, f"{username}_phrase_{app.current_phrase_index + 1}.wav")
    
    stream = app.pyaudio_instance.open(
        format=FORMAT,
        channels=config.CHANNELS,
        rate=config.RATE,
        input=True,
        frames_per_buffer=config.CHUNK
    )
    frames = []
    
    while app.is_recording:
        frames.append(stream.read(config.CHUNK, exception_on_overflow=False))
        
    stream.stop_stream()
    stream.close()
    
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(config.CHANNELS)
        wf.setsampwidth(app.pyaudio_instance.get_sample_size(FORMAT))
        wf.setframerate(config.RATE)
        wf.writeframes(b''.join(frames))
        
    app.root.after(0, _on_recording_finished, app)

def _on_recording_finished(app):
    """Callback to update the UI after recording is saved."""
    app.recording_status_label.config(text="Recording saved!")
    app.next_btn.config(state="normal")