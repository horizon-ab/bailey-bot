import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer

MODEL_NAME = "distilbert-base-uncased"

class ScamScorer(nn.Module):
    
    def __init__(self, model_name, vocab_size=None):
        super(ScamScorer, self).__init__()
        self.base_model = AutoModel.from_pretrained(model_name)

        if vocab_size:
            self.base_model.resize_token_embeddings(vocab_size)

        hidden_size = self.base_model.config.hidden_size

        self.regression_head = nn.Sequential(
            nn.Linear(hidden_size * 2, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)

        # might use mean pooling or pooler output or something

        # First token
        cls_representation = outputs.last_hidden_state[:, 0, :]

        # Mean pooling
        last_hidden_state = outputs.last_hidden_state
        input_mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        sum_embeddings = torch.sum(last_hidden_state * input_mask, 1)
        sum_mask = torch.clamp(input_mask.sum(1), min=1e-9)

        mean_pooled_representation = sum_embeddings / sum_mask

        combined = torch.cat((cls_representation, mean_pooled_representation), dim=1)
         
        score = self.regression_head(combined)
        return score


tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = ScamScorer(MODEL_NAME)
