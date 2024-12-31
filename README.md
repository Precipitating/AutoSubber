# AutoSubber
![image](https://github.com/user-attachments/assets/f4082bc6-728d-4be9-b62e-1c9d6ee74b1b)\
A simple program designed to make auto-subbing videos easy.\
It uses customtkinter for the GUI and stable-ts for the auto captioning.
# How to use:
Simply type the model to use in models.txt and open the exe.\
It will take a while to load, as it's downloading the model in your system if you don't have it.\
The large model requires the GPU to use, with this required:
* [cuBLAS for CUDA 12](https://developer.nvidia.com/cublas)
* [cuDNN 9 for CUDA 12](https://developer.nvidia.com/cudnn)
# Options:
## Word/segment timestamp:

https://github.com/jianfch/stable-ts/assets/28970749/c22dcdf9-79cb-485a-ae38-184d006e513e

## Clean audio:
Uses VAD and demucs to remove all background noise and get a clearer transcription output, resulting in better caption quality.

## Max words per segment:
Only works if you have segment timestamp on. Simply limits the words per line.

## Karaoke highlighting:
Does progressive highlight filling on the text if you have segment and word timestamp on. Karaoke effect.
## Font:
Self explanatory, it can use any font that you've installed on the system.


