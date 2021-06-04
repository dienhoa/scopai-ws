# uvicorn imports
# import aiohttp
# import asyncio
import uvicorn
import aiofiles
from statistics import mode


# starlette imports
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from io import BytesIO
import os

# fastai
# from fastai.vision.all import *
from fastai.learner import load_learner
from pathlib import Path
import random
import torch
import gdown
import torchaudio
import librosa
import time

# Any custom imports should be done here, for example:
# from lib.utilities import *
# lib.utilities contains custom functions used during training that pickle is expecting


random.seed(23)
# export_file_url = YOUR_GDRIVE_LINK_HERE
export_file_name = 'resnet-lung.pkl'
export_file_url = 'https://drive.google.com/uc?export=download&id=17UuhqaNZ8ksx0TM75vJsa21WfWgg7J3c'
audio_folder = 'audio-files'

path = Path(__file__).parent
app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

if not (path / export_file_name).exists():
    gdown.download(export_file_url, str(path / export_file_name), quiet=False)

if not (path / audio_folder).exists():
    os.mkdir(path / audio_folder)

def get_y(): pass

# configuration for audio processing
n_fft=1024
hop_length=256
target_rate=4000
num_samples=int(target_rate)*8

## Helper method to tranform audio array to Spectrogram
au2spec = torchaudio.transforms.MelSpectrogram(sample_rate=target_rate,n_fft=n_fft, hop_length=hop_length, n_mels=128, f_max=target_rate//2)
ampli2db = torchaudio.transforms.AmplitudeToDB()

def get_x(path, target_rate=target_rate, num_samples=num_samples):
    x, rate = torchaudio.load(path)
    if rate != target_rate: 
        x = torchaudio.transforms.Resample(orig_freq=rate, new_freq=target_rate, resampling_method='sinc_interpolation')(x)
    x = x[0] / torch.max(torch.abs(x))
    x = x.numpy()
    sample_total = x.shape[0]
    randstart = target_rate if sample_total-num_samples > 0 else 0
    x = x[randstart:num_samples+randstart]
    x = librosa.util.fix_length(x, num_samples)
    torch_x = torch.tensor(x)
    spec = au2spec(torch_x)
    spec_db = ampli2db(spec)
    spec_db = spec_db.data.squeeze(0).numpy()
    spec_db = spec_db - spec_db.min()
    spec_db = spec_db/spec_db.max()*255
    return spec_db

learn = load_learner(path / export_file_name)
classes = learn.dls.vocab

@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    name = f'./{time.time()}.wav'
    audio_path = path/audio_folder/name
    async with aiofiles.open(audio_path, mode='bx') as f:
        await f.write(img_bytes)
    img_np = get_x(audio_path)
    print(name)
    pred = learn.predict(img_np)
    print(pred)
    return JSONResponse({
        'result': str(pred[0])
    })

if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
