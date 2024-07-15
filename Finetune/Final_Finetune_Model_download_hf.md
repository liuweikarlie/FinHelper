
# Download our Finetune Model from HF

## Link for our Model 
- Finetune 1: https://huggingface.co/Andy1124233/capstone_fingpt
- Finetune 2: https://huggingface.co/Andy1124233/Capstone_Forecaster


## How to donwload 
- Finetune Model 1
```bash
huggingface-cli download Andy1124233/capstone_fingpt

```

- Finetune Model 2

```bash
huggingface-cli download Andy1124233/Capstone_Forecaster

```

The Model download in here is the peft format, you need to combine it with the original model LLAMA2-8b to use. The make the model run, please check the `load_model` folder.