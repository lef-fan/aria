# Aria
Meet Aria. A local and uncensored AI entity.

![Aria](https://github.com/lef-fan/aria/blob/main/assets/aria.png?raw=true)

https://github.com/lef-fan/aria/assets/23457676/d90b3f04-6d56-43a7-86ab-674fc558abe2

## Installation
Clone the repo.\
Install required libs.

[For llama llms installation check here](https://github.com/abetlen/llama-cpp-python)

Easy installation for server mode using docker:
```
docker buildx build --tag ghcr.io/lef-fan/aria-server:latest .
```

(Tested on Linux + NVIDIA GPUs with python >=3.10)

More are coming, work in progress...

## Usage
First run will take a while to download all the required models.\
You may edit the default config for your device or use case (change model, specify devices, etc...)\
If you have the resources, strongly recommended to use a model of bigger quant method such as:\
```Qwen2.5-32B-AGI-Q6_K_L.gguf```

```
python main.py
```
### Server and Client Mode

server machine:
```
python server.py 
```
or docker for server:
```
docker run --net=host --gpus all --name aria-server -it ghcr.io/lef-fan/aria-server:latest
python server.py
```
client machine (edit client target ip in the config):
```
python client.py
```

## Documentation
Work in progress...

## Contributions
🌟 We'd love your contribution! Please submit your changes via pull request to join in the fun! 🚀

## Disclaimer
Aria is a powerful AI entity designed for local use. Users are advised to exercise caution and responsibility when interacting with Aria, as its capabilities may have unintended consequences if used improperly or without careful consideration.

By engaging with Aria, you understand and agree that the suggestions and responses provided are for informational purposes only, and should be used with caution and discretion.

We cannot be held responsible for any actions, decisions, or outcomes resulting from the use of Aria. We explicitly disclaim liability for any direct, indirect, incidental, consequential, or punitive damages arising from reliance on Aria's responses.

We encourage users to exercise discernment, judgment, and thorough consideration when utilizing information from Aria. Your use of this service constitutes acceptance of these disclaimers and limitations.

Should you have any doubts regarding the accuracy or suitability of Aria's responses, we advise consulting with qualified professionals or experts in the relevant field.

## Acknowledgments

- [silero-vad](https://github.com/snakers4/silero-vad)
- [transformers](https://github.com/huggingface/transformers)
- [whisper](https://github.com/openai/whisper)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [TTS](https://github.com/coqui-ai/TTS)
- [TTS fork](https://github.com/idiap/coqui-ai-TTS)
- [opuslib](https://github.com/orion-labs/opuslib)
- [TheBloke](https://huggingface.co/TheBloke)
- [Bartowski](https://huggingface.co/bartowski)

## License Information

### ❗ Important Note:
While this project is licensed under GNU AGPLv3, the usage of some of the components it depends on might not and they will be listed below:

#### TTS MODEL
- **License**: Open-source only for non-commercial projects.
- **Commercial Use**: Requires a paid plan.
- **Details**: [Coqui Public Model License 1.0.0](https://coqui.ai/cpml)

#### opuslib
- **License**: BSD-3-Clause license
- **Details**: [opuslib license](https://github.com/orion-labs/opuslib?tab=BSD-3-Clause-1-ov-file#readme)