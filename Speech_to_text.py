import os
import math
import concurrent.futures
from google.cloud import speech
from pydub import AudioSegment
import pandas as pd
import asyncio
from rasa.core.agent import Agent   
import shutil

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'D:\Scienceproject\AI\Speech to Text with Python\Speech_to_text_GGCLOUD\key.json'
speech_client = speech.SpeechClient()
agent = Agent.load(r"D:\Scienceproject\AI\RASA\models\20230228-211440-urbane-offset.tar.gz",action_endpoint=None)
class SplitWavAudioMubin():
    def __init__(self, filepath, sample_rate_hertz=24000):
        self.filepath = filepath
        self.folder = os.path.dirname(self.filepath)
        self.wav_filepath = os.path.join(self.folder, os.path.splitext(os.path.basename(self.filepath))[0] + '.wav')
        self.convert_mp3_to_wav(self.filepath, self.wav_filepath, sample_rate_hertz)
        self.audio = AudioSegment.from_wav(self.wav_filepath)

    def delete_non_mp3_files(self, folder_path):
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if not file_name.endswith('.mp3'):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

    def convert_mp3_to_wav(self, mp3_file, wav_file, sample_rate_hertz):
        sound = AudioSegment.from_file(mp3_file, format="mp3")
        sound = sound.set_frame_rate(sample_rate_hertz)
        sound.export(wav_file, format="wav")

    def get_duration(self):
        return self.audio.duration_seconds

    def single_split(self, from_min, to_min, split_filename):
        t1 = from_min * 50 * 1000
        t2 = to_min * 50 * 1000
        split_audio = self.audio[t1:t2]
        split_filepath = os.path.join(self.folder, split_filename)
        split_audio.export(split_filepath, format="wav")
        return split_filepath

    def multiple_split(self, min_per_split):
        total_mins = math.ceil(self.get_duration() / 50)
        split_folder = os.path.join(self.folder, 'split_files')
        if not os.path.exists(split_folder):
            os.makedirs(split_folder)
        for i in range(0, total_mins, min_per_split):
            split_fn = str(i) + '_' + os.path.basename(self.wav_filepath)
            split_filepath = self.single_split(i * min_per_split, (i+min_per_split) * min_per_split, split_fn)
            split_savepath = os.path.join(split_folder, split_fn)
            os.rename(split_filepath, split_savepath)
            print(f"Segment {i//min_per_split+1}/{math.ceil(total_mins/min_per_split)} done.")
        print('Chờ xử lý, sẽ tốn 1 ít thời gian')

    def recognize_audio(self, file_path):
        # Đọc nội dung của tệp
        with open(file_path, 'rb') as f:
            byte_data = f.read()

        # Tạo đối tượng RecognitionConfig
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=24000,
            enable_automatic_punctuation=False,
            language_code='vi-VN',
            model='latest_long'
        )

        # Tạo đối tượng RecognitionAudio
        audio = speech.RecognitionAudio(content=byte_data)

        # Tạo đối tượng SpeechClient
        client = speech.SpeechClient()

        # Gọi phương thức recognize để chuyển đổi âm thanh sang văn bản
        response = client.recognize(config=config, audio=audio)

        # Lấy kết quả từ đối tượng response
        result = response.results[0]
        alternative = result.alternatives[0]
        transcript = alternative.transcript.encode('utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')

        return transcript

    def recognize_audio_files_in_directory(self, save_path=None):
        audio_folder = os.path.join(self.folder, 'split_files')
        # Lấy danh sách các tệp âm thanh trong thư mục
        audio_files = [os.path.join(audio_folder, f) for f in os.listdir(audio_folder) if f.endswith('.wav')]

        # Create output directory if it doesn't exist
        if save_path is not None:
            os.makedirs(save_path, exist_ok=True)

        # Tạo một đối tượng ThreadPoolExecutor để xử lý các tệp đồng thời
        results = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i, file in enumerate(audio_files):
                # Gọi phương thức `recognize_audio` cho mỗi tệp âm thanh
                future = executor.submit(self.recognize_audio, file)
                results[os.path.basename(file)] = future  # Thay đổi tên file ở đây

            # Lấy kết quả từ các future đã được gọi
            final_results = []
            for file in sorted(results.keys()):
                future = results[file]
                result = future.result()
                final_results.append(result)

                # Lưu kết quả vào file nếu cung cấp đường dẫn lưu
                if save_path is not None:
                    transcription = result
                    filename = os.path.basename(file)
                    with open(os.path.join(save_path, f"transcript_{filename}.txt"), "w", encoding="utf-8") as f:
                        f.write(transcription)

        # Trả về danh sách các đoạn văn bản được chuyển đổi từ âm thanh theo thứ tự của tên file âm thanh
        return final_results


    def run_exam(self,file_path, dapan, Cau):
        
        text = ''.join(self.recognize_audio_files_in_directory())  # Thay đổi đối số my_list thành kết quả của phương thức recognize_audio_files_in_directory
        list_cau1 = text.lower().split('kết thúc cảm ơn')[0:-1]
        print(list_cau1)

        cau = []
        traloi = []
        ketqua = []
        questions3 = []
        score = 0
        for j in range(len(list_cau1)):
            cau1 = list_cau1[j].split()
            print(cau1)
            dau_1 = 0
            ket_1 = len(cau1)

            for i in range(len(cau1)):
                if cau1[i] == 'trả':
                    if i+3 < len(cau1) and cau1[i+1] == 'lời' and cau1[i+2] == 'câu' and cau1[i+3] == 'hỏi':
                        dau_1 = i+6
                if cau1[i] == 'thời':
                    if i+3 < len(cau1) and cau1[i+1] == 'gian' and cau1[i+2] == 'trả' and cau1[i+3] == 'lời':
                        ket_1 = i

            list_cau1[j] = cau1[int(dau_1):int(ket_1)]
            questions2 = list_cau1
            cau1.clear()

        for q in questions2:
            question = ' '.join(q)
            questions3.append(question)

        for i in range(len(questions3)):
            response = agent.parse_message(message_data=questions3[i])
            result = asyncio.run(response)
            intent_name = result["intent"]["name"]
            cau.append(intent_name)

        for j in range(len(cau)):
            if cau[j] == 'DAP_AN_A':
                traloi.append('A')

            elif cau[j] == 'DAP_AN_B':
                traloi.append('B')

            elif cau[j] == 'DAP_AN_C':
                traloi.append('C')

            elif cau[j] == 'DAP_AN_D':
                traloi.append('D')
            else:
                traloi.append('0')

        for i in range(len(dapan)):
            ketqua.append("Đúng" if dapan[i] == traloi[i] else "Sai")
            if dapan[i] == traloi[i]:
                score += 1
        print("Điểm của bạn là {}/{}".format(score, len(dapan)))
        df = pd.DataFrame(zip(dapan, traloi, ketqua), index=Cau, columns=['ĐÁP ÁN', 'CÂU TRẢ LỜI', 'KẾT QUẢ'])

        with open(file_path + "\df.json", 'w', encoding='utf-8') as file:
            df.to_json(file, force_ascii=False)
        print("Đây là kết quả:.........")
        print(df)

# Tạo một đối tượng SplitWavAudioMubin với đường dẫn đến thư mục chứa file âm thanh và tên file âm thanh
dapan = []
CAU = []
path = input("Nhập đường dẫn: ")
folder_path, file_name = os.path.split(path)
number = int(input("Nhập số lượng câu hỏi: "))
for i in range(number):
    b = i+1
    B = input("Nhập đáp án câu %d: " %b).upper()
    while B not in ["A", "B", "C", "D"]:
        print("Đáp án không hợp lệ, vui lòng nhập lại!")
        B = input("Nhập đáp án câu %d: " %b)
    dapan.append(B)
    CAU.append("%d" %b)
splitter = SplitWavAudioMubin(path)
results = splitter.delete_non_mp3_files(folder_path)
splitter.multiple_split(1)
results = splitter.recognize_audio_files_in_directory()
print(results)
results = splitter.run_exam(folder_path,dapan,CAU)