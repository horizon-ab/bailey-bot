import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AdamW

from src.model import ScamScorer
from src.dataset import ScoringDataset

def train():

    # Config
    model_name = "distilbert-base-uncased"
    batch_size = 16
    epochs = 3
    lr = 2e-5
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.add_special_tokens({
        'additional_special_tokens' : ["<URL>", "<USER>", "<EMOJI>", "<DISCORD_INVITE>"]
    })

    # Model
    model = ScamScorer(model_name, vocab_size=len(tokenizer)).to(device)

    # Dataset
    train_texts = []
    train_scores = []

    train_dataset = ScoringDataset(train_texts, train_scores, tokenizer)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Training Tools
    optimizer = AdamW(model.parameters(), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()

    # Training Loop
    print(f"Starting training on {device}...")
    model.train()
    for epoch in range(epochs):
        for batch in train_loader:
            optimizer.zero_grad()

            ids = batch['input_ids'].to(device)
            mask = batch['attention_mask'].to(device)
            targets = batch['score'].to(device).unsqueeze(1)

            outputs = model(ids, mask)
            loss = criterion(outputs, targets)

            loss.backward()
            optimizer.step()

        print(f"Epoch {epoch + 1} complete. Loss: {loss.item():.4f}")

    model_save_path = "./outputs/final_model.pt"
    torch.save(model.state_dict(), model_save_path)
    tokenizer.save_pretrained("./outputs/")
    print("Model and Tokenizer saved successfully!")


if __name__ == "__main__":
    train()
