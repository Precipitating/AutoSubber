import os
import customtkinter as ctk
import moviepy
from customtkinter import filedialog
import uuid
from faster_whisper import WhisperModel
from os.path import join
import pysubs2
import threading

class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.transcriber = Transcriber()
        self.geometry("350x400")
        self.title("AutoSubber")
        self.resizable(False, False)
        self.progress_steps = 4

        inner_frame = ctk.CTkFrame(self)
        inner_frame.place(relx = 0.5, rely = 0.5, relwidth = 0.95, relheight=0.95,  anchor="center")

        # browse & select video file
        browse_button= ctk.CTkButton(inner_frame, text="Browse video file", command=self.browse_file)
        browse_button.grid(row=0, column= 0 , padx=5, pady= 10)

        self.selected_file = ctk.CTkEntry(inner_frame)
        self.selected_file.insert(0,"No file selected")
        self.selected_file.configure(state="disabled")
        self.selected_file.grid(row=0, column = 1)

        # start button
        self.start_button = ctk.CTkButton(inner_frame, text="Start", command=self.start_button_thread)
        self.start_button.place(relx = 0.5, rely = 0.8,  anchor="center")

        # progress bar
        self.progress_bar = ctk.CTkProgressBar(inner_frame, determinate_speed=20)
        self.progress_bar.set(0)
        self.progress_bar.place(relx = 0.5, rely = 0.9,  anchor="center")

        # clean audio checkbox
        self.clean_audio_checkbox = ctk.CTkCheckBox(inner_frame, text="Clean audio")
        self.clean_audio_checkbox.grid(row= 1, column= 0, sticky= "w", padx= 10)

        # error messages if transcription fail
        self.error_msg = ctk.CTkLabel(inner_frame, text_color= "red", text="")
        self.error_msg.place(relx = 0.5, rely = 0.7,  anchor="center")


    def browse_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select a video file (mp4, mkv, avi)",
            filetypes=[("Video Files", "*.mp4;*.mkv;*.avi;*.mov;*.webm")]
        )

        if file_path:
            self.selected_file.configure(state="normal")
            self.selected_file.delete(0, ctk.END)
            self.selected_file.insert(0,file_path)
            self.selected_file.configure(state="disabled")

    def start_button_function(self):
        self.progress_bar.set(0)
        self.error_msg.configure(text="")
        if self.selected_file.get() == "":
            self.error_msg.configure(text="Select a video before starting.")
            return

        # start the process
        self.start_button.configure(state="disabled")

        # convert to mp3
        if not self.transcriber.extract_audio(self.selected_file.get()):
            self.error_msg.configure(text="Cannot extract audio file. Ensure there's audio.")
            self.start_button.configure(state="normal")
            return
        self.progress_bar.set(0.25)

        #transcribe via Whisper
        if self.clean_audio_checkbox.get() == 1:
            transcription_result = self.transcriber.transcribe(True)
        else:
            transcription_result = self.transcriber.transcribe(False)

        if not transcription_result:
            self.error_msg.configure(text="No transcription detected. Aborting.")
            self.start_button.configure(state="normal")
            return
        self.progress_bar.set(0.5)

        # put transcription into an ass file
        self.transcriber.generate_subtitles(transcription_result[0], transcription_result[1])
        self.progress_bar.set(0.75)

        # generate video with subtitles
        self.transcriber.subtitle_to_video((os.path.splitext(self.selected_file.get())),self.transcriber.sub_path)
        self.progress_bar.set(1)

        self.start_button.configure(state="normal")
        print("done")


    def start_button_thread(self):
        thread = threading.Thread(target=self.start_button_function)
        thread.start()









class Transcriber:
    def __init__(self):
        self.model = WhisperModel("large-v3")
        self.file_name = ""
        self.transcription_result = ""
        self.audio_dir = "audio/"
        self.subtitle_dir = "subtitles/"
        self.output_dir = "output/"
        self.file_path = ""
        self.sub_path = ""

    def extract_audio(self, path):
        clip = None
        try:
            # load video
            clip = moviepy.VideoFileClip(path)
            # convert to mp3 using timestamp as file name
            self.file_name = f"{uuid.uuid4().hex}"
            self.file_path = join(self.audio_dir, f'{self.file_name}.mp3')
            clip.audio.write_audiofile(self.file_path)
            return True
        except Exception as e:
            return False
        finally:
            clip.close()


    # analyze mp3 file and generate transcription & timestamps
    def transcribe(self, isolate_vocals):
        if isolate_vocals:
            segments, info = self.model.transcribe(self.file_path, vad_filter= True)
        else:
            segments, info = self.model.transcribe(self.file_path)

        segments = list(segments)

    # if no transcription, no point continuing
        if not segments:
            print("No transcription found")
            return False

    # debug to see transcription results on console
        for seg in segments:
            print("[%.2fs -> %.2fs] %s" % (seg.start, seg.end, seg.text))

    # returns lang and transcription results
        return info.language, segments


    # put subtitles in the .ass file
    def generate_subtitles(self, language, segments):
        self.sub_path = join(self.subtitle_dir, f'{self.file_name}-sub.ass')
        results = []
        for s in segments:
            seg_dict = {'start': s.start, 'end': s.end, 'text': s.text}
            results.append(seg_dict)

        subs = pysubs2.load_from_whisper(results)
        subs.save(self.sub_path)


    def subtitle_to_video(self, input_video, sub_file):
        output = join(self.output_dir, f'{self.file_name}{input_video[1]}')
        os.system(f'ffmpeg -i "{input_video[0] + input_video[1]}" -vf subtitles="{sub_file}" "{output}"')
        os.remove(self.file_path)








app = GUI()
app.mainloop()