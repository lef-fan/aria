FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

RUN apt update && apt upgrade -y \
    && apt install -y git \
    python3-pip python3.10-venv \
    && git clone https://github.com/lef-fan/aria.git

WORKDIR /aria

RUN python3 -m venv venv
ENV VIRTUAL_ENV venv
ENV PATH venv/bin:$PATH

RUN pip install wheel numpy torch onnxruntime \
    git+https://github.com/huggingface/transformers \
    && CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python \
    TTS accelerate flash-attn deepspeed
