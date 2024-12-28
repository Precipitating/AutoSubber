import os
import customtkinter as ctk
import moviepy
from customtkinter import filedialog
import uuid
import stable_whisper
from os.path import join
import threading

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
        browse_button.grid(row=0, column= 0 , padx=10, pady= 10, sticky="w",)

        self.selected_file = ctk.CTkEntry(inner_frame, width = 150)
        self.selected_file.configure(state="disabled")
        self.selected_file.grid(row=0, column = 1, sticky = 'w' )

        # progress bar
        self.progress_bar = ctk.CTkProgressBar(inner_frame, determinate_speed=20)
        self.progress_bar.set(0)
        self.progress_bar.place(relx = 0.5, rely = 0.9,  anchor="center")

        # clean audio checkbox
        self.clean_audio_checkbox = ctk.CTkCheckBox(inner_frame, text="Clean audio")
        self.clean_audio_checkbox.grid(row= 1, column= 0, sticky= "w", padx= 10, pady = 2)

        # word level checkbox
        self.word_timestamp_checkbox = ctk.CTkCheckBox(inner_frame, text="Word timestamp")
        self.word_timestamp_checkbox.select()
        self.word_timestamp_checkbox.grid(row= 2, column= 0, sticky= "w", padx= 10, pady = 2)

        # segment level checkbox
        self.segment_timestamp_checkbox = ctk.CTkCheckBox(inner_frame, text="Segment timestamp", command=self.segment_timestamp_options)
        self.segment_timestamp_checkbox.select()
        self.segment_timestamp_checkbox.grid(row= 3, column= 0, sticky= "w", padx= 10, pady = 2)

        # karaoke highlighting checkbox
        self.karaoke_checkbox = ctk.CTkCheckBox(inner_frame, text="Karaoke highlighting")
        self.karaoke_checkbox.grid(row= 4, column= 0, sticky= "w", padx= 10, pady = 5)

        # max words per line
        self.max_words_label = ctk.CTkLabel(inner_frame, text= "Max words per segment \n (0 = automatic)", padx = 10)
        self.max_words_label.grid(row= 5, column = 0)

        slider_val = ctk.IntVar()
        self.max_words_per_seg_slider = ctk.CTkSlider(inner_frame, from_= 0, to = 20, width= 150,
                                                       variable= slider_val)
        self.max_words_per_seg_slider.grid(row= 6, column= 0, sticky= "w", padx= 10)
        # display slider val
        self.max_word_slider_val = ctk.CTkLabel(inner_frame, textvariable= slider_val)
        self.max_word_slider_val.grid(row=6,column=1, sticky='w')

        # error messages if transcriptions fail
        self.error_msg = ctk.CTkLabel(inner_frame, text_color= "red", text="")
        self.error_msg.place(relx = 0.5, rely = 0.7,  anchor="center")

        # start button
        self.start_button = ctk.CTkButton(inner_frame, text="Start", command=self.start_button_thread)
        self.start_button.place(relx = 0.5, rely = 0.8,  anchor="center")

    # enable slider if segment_timestamp checkbox is on
    def segment_timestamp_options(self):
        if self.segment_timestamp_checkbox.get() == 1:
            self.max_words_per_seg_slider.configure(state= "normal")
        else:
            self.max_words_per_seg_slider.set(0)
            self.max_words_per_seg_slider.configure(state="disabled")


    def browse_file(self):
        file_path = filedialog.askopenfilename(
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

        # early error returns
        if self.selected_file.get() == "":
            self.error_msg.configure(text="Select a video before starting.")
            return

        if self.word_timestamp_checkbox.get() == 0 and self. segment_timestamp_checkbox.get() == 0:
            self.error_msg.configure(text= "Word timestamp or Segment timestamp must be enabled")
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
        transcription_result = self.transcriber.transcribe(isolate=self.clean_audio_checkbox.get(),
                                                           max_words = self.max_words_per_seg_slider.get())

        if not transcription_result:
            self.error_msg.configure(text="No transcription detected. Aborting.")
            self.start_button.configure(state="normal")
            return
        self.progress_bar.set(0.5)

        # put transcription into an ass file
        self.transcriber.generate_subtitles(transcription_result,
                                            word_timestamp= self.word_timestamp_checkbox.get(),
                                            seg_timestamp= self.segment_timestamp_checkbox.get(),
                                            karaoke_option= self.karaoke_checkbox.get())
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
        self.model = stable_whisper.load_faster_whisper('large-v3')
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
            if clip is not None:
                clip.close()


    # analyze mp3 file and generate transcription & timestamps
    def transcribe(self, **kwargs):
        result = self.model.transcribe_stable(self.file_path,
                                              vad= True if kwargs.get("isolate") == 1 else False,
                                              denoiser="demucs" if kwargs.get("isolate") == 1 else None,
                                              regroup= False if kwargs.get('max_words') != 0 else True
                                              )
        if kwargs.get('max_words', 0) != 0:
            result.split_by_length(max_words=kwargs.get('max_words'))



    # if no transcription, no point continuing
        if not result.has_words:
            print("No transcription found")
            return False

    # debug to see transcription results on console
        for seg in result.segments:
            print("[%.2fs -> %.2fs] %s" % (seg.start, seg.end, seg.text))

        return result


    # put subtitles in the .ass file
    def generate_subtitles(self, result, **kwargs):
        self.sub_path = join(self.subtitle_dir, f'{self.file_name}-sub.ass')
        result.to_ass(self.sub_path,
                      word_level = True if kwargs.get("word_timestamp", 0) == 1 else False,
                      segment_level = True if kwargs.get("seg_timestamp", 0) == 1 else False,
                      karaoke = True if kwargs.get('karaoke_option', 0) == 1 else False)



    # combine subtitles to video and save to output/
    def subtitle_to_video(self, input_video, sub_file):
        output = join(self.output_dir, f'{self.file_name}{input_video[1]}')
        os.system(f'ffmpeg -i "{input_video[0] + input_video[1]}" -vf subtitles="{sub_file}" "{output}"')
        os.remove(self.file_path)








app = GUI()
app.mainloop()