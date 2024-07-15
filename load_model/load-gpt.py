from torch import cuda, bfloat16
import torch
import transformers
from transformers import AutoTokenizer,AutoModelForCausalLM
from time import time

from peft import PeftModel

device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, AutoPeftModelForCausalLM

output_dir="/kaggle/working/capstone_fingpt"
device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'


hf_auth="<your hf-auth>"
model_id = 'meta-llama/Llama-2-7b-chat-hf'
perft_model='Andy1124233/Capstone_Forecaster'

#     model_config = transformers.AutoConfig.from_pretrained(
#     model_id,
# )
model = transformers.AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    device_map='auto',
    token=hf_auth,
)
model.model_parallel = True

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True,token=hf_auth)

tokenizer.padding_side = "right"

tokenizer.pad_token_id = tokenizer.eos_token_id

# if not tokenizer.pad_token or tokenizer.pad_token_id == tokenizer.eos_token_id:
#     tokenizer.add_special_tokens({'pad_token': '[PAD]'})
#     model.resize_token_embeddings(len(tokenizer))

# model.config.use_cache = False

model = PeftModel.from_pretrained(model,perft_model)
model = model.eval()

model = model.merge_and_unload()
model.save_pretrained("merged")
tokenizer.save_pretrained("token")
