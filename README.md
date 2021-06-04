# Introduction

- Lung Sound Analyzer (Healthy/Unhealthy) for audio recorded from digital Stretroscope

# How to run

- Install the dependencies from requirements.txt then run: `python app/server.py`

# Docker build and run

- Build Image
```
    docker build -t lung_sound .
```
- Run Image

Locally:

```
    docker run -p 5000:5000 lung_sound
```

# Dependencies

This project is based on:
- fast.ai for deep learning model training and inference
- Starlette for creating WebService