import os
import customtkinter as ctk
import moviepy
from customtkinter import filedialog
import time
import uuid
from faster_whisper import WhisperModel


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.transcriber = Transcriber()
        self.geometry("350x400")
        self.title("AutoSubber")
        self.resizable(False, False)

        inner_frame = ctk.CTkFrame(self)
        inner_frame.place(relx = 0.5, rely = 0.5, relwidth = 0.95, relheight=0.95,  anchor="center")

        # browse & select video file
        browse_button= ctk.CTkButton(inner_frame, text="Browse video file", command=self.browse_file)
        browse_button.grid(row=0, column = 0 , padx=10, pady = 10)

        self.selected_file = ctk.CTkEntry(inner_frame,  placeholder_text="No file selected")
        self.selected_file.grid(row=0, column = 1, padx=10)

        # start button
        start_button = ctk.CTkButton(inner_frame, text="Start", command=self.start_button)
        start_button.place(relx = 0.5, rely = 0.8,  anchor="center")

        # progress bar
        self.progress_bar = ctk.CTkProgressBar(inner_frame, determinate_speed=10)
        self.progress_bar.set(0)
        self.progress_bar.place(relx = 0.5, rely = 0.9,  anchor="center")


    def browse_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select a video file (mp4, mkv, avi)",
            filetypes=[("Video Files", "*.mp4;*.mkv;*.avi;*.mov;*.webm")]
        )

        if file_path:
            self.selected_file.delete(0, ctk.END)
            self.selected_file.insert(0,file_path)

    def start_button(self):
        # convert to mp3
        self.transcriber.extract_audio(self.selected_file.get())
        self.progress_bar.step()

        # transcribe via Whisper
        self.transcriber.transcribe()
        self.progress_bar.step()



class Transcriber:
    def __init__(self):
        self.model = WhisperModel("large-v3")
        self.file_name = f"{uuid.uuid4().hex}"
        self.transcription_result = ""
        self.output_dir = "output/"

    def extract_audio(self, path):
        # load video
        clip = moviepy.VideoFileClip(path)

        # convert to mp3 using timestamp as file name
        clip.audio.write_audiofile(f'{self.output_dir}{self.file_name}.mp3')

    def transcribe(self):
        segments, info = self.model.transcribe(f'{self.output_dir}{self.file_name}.mp3')
        segments = list(segments)

        for seg in segments:
            print("[%.2fs -> %.2fs] %s" % (seg.start, seg.end, seg.text))
        return info.language, segments


   # def apply_caption_to_video:












app = GUI()
app.mainloop()