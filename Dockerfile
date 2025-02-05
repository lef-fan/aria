FROM nvidia/cuda:12.6.1-cudnn-devel-ubuntu24.04

RUN apt update && apt upgrade -y \
    && apt install -y git opus-tools \
    python3-pip python3.12-venv \
    && git clone https://github.com/lef-fan/aria.git

WORKDIR /aria

RUN python3 -m venv venv
ENV VIRTUAL_ENV venv
ENV PATH venv/bin:$PATH

RUN pip install wheel numpy==1.26.4 torch onnxruntime \
    && CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python \
    coqui-tts accelerate flash-attn deepspeed opuslib kokoro
