import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from scipy.signal import butter, lfilter
from scipy.fft import fft, ifft
import pywt
import time

##Capturing Audio
RATE = 44100
CHUNK = 1024
CHANNELS = 1
FORMAT = pyaudio.paInt16  ##Audio format (16-bit PCM)

##Low-pass filter
cutoff = 1000  ##Initial cutoff frequency (Hz)
order = 6  ##Filter order

class AudioVisualizer:
    def __init__(self, rate, chunk, cutoff, order):
        self.rate = rate
        self.chunk = chunk
        self.cutoff = cutoff
        self.order = order
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], lw=2)
        self.ax.set_ylim(-2500, 2500)
        self.ax.set_xlim(0, self.chunk)
        self.fig.subplots_adjust(left=0.1, bottom=0.2)
        plt.ion()

    def update_plot(self, filtered_data):
        self.line.set_ydata(filtered_data)
        self.line.set_xdata(np.arange(len(filtered_data)))
        plt.draw()
        plt.pause(0.01)
        self.ax.figure.canvas.flush_events()

class NoiseFilter:
    def __init__(self, cutoff, fs, order=5):
        self.cutoff = cutoff
        self.fs = fs
        self.order = order

    def butter_lowpass(self):
        nyquist = 0.5 * self.fs
        normal_cutoff = self.cutoff / nyquist
        b, a = butter(self.order, normal_cutoff, btype='low', analog=False)
        return b, a

    def butter_lowpass_filter(self, data):
        b, a = self.butter_lowpass()
        return lfilter(b, a, data)

def spectral_subtraction(data, noise_estimation_factor=0.1):
    data_fft = fft(data)
    magnitude = np.abs(data_fft)
    noise_estimate = np.mean(magnitude) * noise_estimation_factor
    magnitude_cleaned = np.maximum(magnitude - noise_estimate, 0)
    cleaned_fft = magnitude_cleaned * np.exp(1j * np.angle(data_fft))
    cleaned_data = np.real(ifft(cleaned_fft))
    return cleaned_data

def wavelet_denoising(data, wavelet='db8', level=5):
    coeffs = pywt.wavedec(data, wavelet, level=level)
    threshold = np.median(np.abs(coeffs[-1])) / 0.6745
    coeffs = [pywt.threshold(c, threshold, mode='soft') for c in coeffs]
    denoised_data = pywt.waverec(coeffs, wavelet)
    return denoised_data[:len(data)]

def moving_average(data, window_size=5):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def plot_audio_waveform():
    data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
    spectral_data = spectral_subtraction(data, noise_estimation_factor=0.1)
    wavelet_data = wavelet_denoising(spectral_data, wavelet=current_wavelet, level=5)
    smoothed_data = moving_average(wavelet_data, window_size=5)
    visualizer.update_plot(smoothed_data)

def update_cutoff(val):
    global cutoff
    cutoff = val
    filter.cutoff = cutoff
    print(f"Updated cutoff frequency: {cutoff}")

def update_wavelet(val):
    global current_wavelet
    current_wavelet = wavelet_options[int(val)]
    print(f"Updated wavelet: {current_wavelet}")

##Interactive controls
wavelet_options = ['db8', 'sym2', 'coif1', 'bior1.3']
current_wavelet = wavelet_options[0]

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
visualizer = AudioVisualizer(RATE, CHUNK, cutoff, order)
filter = NoiseFilter(cutoff, RATE, order)

##Sliders control
ax_cutoff = plt.axes([0.1, 0.01, 0.65, 0.03], facecolor='lightgoldenrodyellow')
slider_cutoff = Slider(ax_cutoff, 'Cutoff (Hz)', 100, 5000, valinit=cutoff, valstep=10)
slider_cutoff.on_changed(update_cutoff)

##Slider for wavelet selection
ax_wavelet = plt.axes([0.1, 0.06, 0.65, 0.03], facecolor='lightgoldenrodyellow')
slider_wavelet = Slider(ax_wavelet, 'Wavelet', 0, len(wavelet_options) - 1, valinit=0, valstep=1)
slider_wavelet.on_changed(update_wavelet)

try:
    while True:
        plot_audio_waveform()
        time.sleep(0.05)  ##slower animation
except KeyboardInterrupt:
    print("Exiting...")

stream.stop_stream()
stream.close()
p.terminate()