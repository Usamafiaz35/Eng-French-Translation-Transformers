# 🌍 English to French Translation using Transformers (TensorFlow & Keras)

This project demonstrates a **Sequence-to-Sequence (Seq2Seq)** machine translation task that translates **English sentences to French** using pretrained Transformer models from Hugging Face. The complete pipeline is implemented in **TensorFlow and Keras**.

---

## 📁 Dataset
- **Dataset Used:** `KDE4` (from Hugging Face Datasets)
- **Language Pair:** English → French

---

## ⚙️ Steps Performed

### ✅ 1. Data Loading & Splitting
- Loaded the `KDE4` dataset which contains English-French sentence pairs.
- Split the dataset into **training** and **testing** sets.

### ✅ 2. Tokenization
- Tokenized the English inputs and French targets using a pretrained tokenizer (e.g., `t5-small` or `mbart`).

### ✅ 3. Model Loading
- Loaded a pretrained transformer model for translation tasks (e.g., `t5-small`).
- Fine-tuned the model on our dataset.

### ✅ 4. Data Collator (Seq2Seq)
- Used `DataCollatorForSeq2Seq` to correctly pad inputs and target sequences for Seq2Seq training.

### ✅ 5. TensorFlow Dataset Preparation
- Converted the processed data into **TensorFlow Datasets** for both training and testing using `prepare_tf_dataset`.

### ✅ 6. Metric: SacreBLEU
- Used `sacrebleu` metric to evaluate the translation quality.
- Implemented a custom function to calculate BLEU scores on the test set.

### ✅ 7. Evaluation
- Generated translations on test data.
- Compared with actual French targets.
- Reported BLEU score as evaluation result.

---

## 🌐 Sample Translation
```python
Input: "How are you?"
Predicted Translation: "Comment ça va ?"
