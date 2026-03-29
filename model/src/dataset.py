from torch.utils.data import Dataset, DataLoader

class ScoringDataset(Dataset):
    def __init__(self, texts, scores, tokenizer, max_length=256):
        self.texts = texts
        self.scores = scores
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)


    def __getitem__(self, idx):
        text = str(self.texts[idx])
        score = float(self.scores[idx])

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        return {
            'input_ids' : encoding['input_ids'].flatten(),
            'attention_mask' : encoding['attention_mask'].flatten(),
            'score' : torch.tensor(score, dtype=torch.float)
        }
