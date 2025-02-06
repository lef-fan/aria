FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu24.04

RUN apt update && apt upgrade -y \
    && apt install -y git opus-tools \
    python3-pip python3.12-venv \
    && git clone https://github.com/lef-fan/aria.git

WORKDIR /aria

RUN python3 -m venv venv
ENV VIRTUAL_ENV=venv
ENV PATH=venv/bin:$PATH

RUN bash -c "pip install --no-cache-dir -r <(grep -v 'PyAudio==0.2.14' requirements.txt)"
RUN pip install --no-cache-dir --no-build-isolation flash-attn==2.7.4.post1