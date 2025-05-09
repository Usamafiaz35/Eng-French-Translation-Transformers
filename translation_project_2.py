# -*- coding: utf-8 -*-
"""Translation Project 2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KWdfMMnR1SZySDsh1P1DoIfD0nlLsfms
"""

!pip install datasets

from datasets import load_dataset

raw_datasets = load_dataset("kde4", lang1="en", lang2="fr")

raw_datasets

split_datasets = raw_datasets["train"].train_test_split(train_size=0.9, seed=20)
split_datasets

#Renaming the test to "validation"
split_datasets["validation"] = split_datasets.pop("test")

split_datasets["train"][1]["translation"]

#Checking the behaviour of model
from transformers import pipeline

model_checkpoint = "Helsinki-NLP/opus-mt-en-fr"
translator = pipeline("translation", model=model_checkpoint)
translator("Default to expanded threads")

split_datasets["train"][172]["translation"]

translator(
    "Unable to import %1 using the OFX importer plugin. This file is not the correct format."
)

"""Preprocessing"""

from transformers import AutoTokenizer

model_checkpoint = "Helsinki-NLP/opus-mt-en-fr"
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint, return_tensors="pt")

en_sentence = split_datasets["train"][1]["translation"]["en"]
fr_sentence = split_datasets["train"][1]["translation"]["fr"]

inputs = tokenizer(en_sentence, text_target=fr_sentence)
inputs

max_length = 128

def preprocess_function(examples):
    inputs = [ex["en"] for ex in examples["translation"]]
    targets = [ex["fr"] for ex in examples["translation"]]
    model_inputs = tokenizer(
        inputs, text_target=targets, max_length=max_length, truncation=True
    )
    return model_inputs

tokenized_datasets = split_datasets.map(
    preprocess_function,
    batched=True,
    remove_columns=split_datasets["train"].column_names,
)

from transformers import TFAutoModelForSeq2SeqLM

model = TFAutoModelForSeq2SeqLM.from_pretrained(model_checkpoint, from_pt=True)

from transformers import DataCollatorForSeq2Seq

data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, return_tensors="tf")

batch = data_collator([tokenized_datasets["train"][i] for i in range(1, 3)])
batch.keys()

batch["labels"]

batch["decoder_input_ids"]

#59513 at start , they are shifted versions of the labels

for i in range(1, 3):
    print(tokenized_datasets["train"][i]["labels"])

tf_train_dataset = model.prepare_tf_dataset(
    tokenized_datasets["train"],
    collate_fn=data_collator,
    shuffle=True,
    batch_size=32,
)
tf_eval_dataset = model.prepare_tf_dataset(
    tokenized_datasets["validation"],
    collate_fn=data_collator,
    shuffle=False,
    batch_size=16,
)

!pip install sacrebleu

!pip install evaluate

import evaluate

metric = evaluate.load("sacrebleu")

#example test
predictions = [
    "This plugin lets you translate web pages between several languages automatically."
]
references = [
    [
        "This plugin allows you to automatically translate web pages between several languages."
    ]
]
metric.compute(predictions=predictions, references=references)

import numpy as np
import tensorflow as tf
from tqdm import tqdm

generation_data_collator = DataCollatorForSeq2Seq(
    tokenizer, model=model, return_tensors="tf", pad_to_multiple_of=128  #128 per batch-padding
)

#Again training with new collater
tf_generate_dataset = model.prepare_tf_dataset(
    tokenized_datasets["validation"],
    collate_fn=generation_data_collator,
    shuffle=False,
    batch_size=8,
)

@tf.function(jit_compile=True)
def generate_with_xla(batch):
    return model.generate(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        max_new_tokens=128,
    )

#function for calculating the score
def compute_metrics():
    all_preds = []
    all_labels = []

    for batch, labels in tqdm(tf_generate_dataset):
        predictions = generate_with_xla(batch)
        decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
        labels = labels.numpy()
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        decoded_preds = [pred.strip() for pred in decoded_preds]
        decoded_labels = [[label.strip()] for label in decoded_labels]
        all_preds.extend(decoded_preds)
        all_labels.extend(decoded_labels)

    result = metric.compute(predictions=all_preds, references=all_labels)
    return {"bleu": result["score"]}

from huggingface_hub import notebook_login

notebook_login()

from transformers import create_optimizer
from transformers.keras_callbacks import PushToHubCallback
import tensorflow as tf


num_epochs = 3
num_train_steps = len(tf_train_dataset) * num_epochs

optimizer, schedule = create_optimizer(
    init_lr=5e-5,
    num_warmup_steps=0,
    num_train_steps=num_train_steps,
    weight_decay_rate=0.01,
)
model.compile(optimizer=optimizer)

# Train in mixed-precision float16
tf.keras.mixed_precision.set_global_policy("mixed_float16")

from transformers.keras_callbacks import PushToHubCallback

callback = PushToHubCallback(
    output_dir="marian-finetuned-kde4-en-to-fr", tokenizer=tokenizer
)

model.fit(
    tf_train_dataset,
    validation_data=tf_eval_dataset,
    callbacks=[callback],
    epochs=num_epochs,
)

#model.save('/content/drive/MyDrive/mymodel', save_format='tf')

'''
#Reload the model
import tensorflow as tf
model = tf.keras.models.load_model('/content/drive/MyDrive/mymodel')
'''

#print(compute_metrics())

# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text2text-generation", model="usama35/marian-finetuned-kde4-en-to-fr")
pipe("Default to expanded threads")