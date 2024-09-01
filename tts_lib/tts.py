import librosa
import numpy as np
 
# 加载音频文件
wav_path = r'D:\Git\github\python-lib\localtest\1.wav'

y, sr = librosa.load(wav_path)
 
# 计算声谱谱（Mel Spectrogram）
spectrogram = librosa.feature.melspectrogram(y, sr)
 
# 转换为dB
log_spectrogram = librosa.power_to_db(spectrogram)
 
# 可视化声谱图
import matplotlib.pyplot as plt
plt.figure(figsize=(12,4))
librosa.display.specshow(log_spectrogram, sr=sr, x_axis='time', y_axis='mel')
plt.colorbar(format='%+02.0f dB')
plt.title('Mel Spectrogram')
plt.show()
 
# 提取MFCC特征
mfccs = librosa.feature.mfcc(y, sr)
 
# 打印MFCC的维度
print("MFCCs shape:", mfccs.shape)
 
# 进行更复杂的分析，例如音高检测、能量分析等
# 这些需要其他库的支持，例如PyAudioAnalysis