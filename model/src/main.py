import torch
import pandas as pd
import os
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import AutoTokenizer, AutoConfig
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

from model import ScamScorer
from dataset import ScoringDataset

def train():

    # Config
    model_name = "distilbert-base-uncased"
    batch_size = 16
    epochs = 4
    lr = 2e-5
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_path = "./data/discord-phishing-scam-detection.csv"

    # Time
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.add_special_tokens({
        'additional_special_tokens' : ["<URL>", "<USER>", "<EMOJI>", "<DISCORD_INVITE>", "<GIVEAWAY>", "<DM_ME>"]
    })

    # Model
    model = ScamScorer(model_name, vocab_size=len(tokenizer)).to(device)

    # Dataset
    df = pd.read_csv(data_path, sep=',', names=['label', 'msg_content'], header=0, encoding='latin1')

    # Balancing

    scams = df[df['label'] == 1.0]
    safe = df[df['label'] == 0.0]

    if len(safe) > len(scams):
        safe_balanced = safe.sample(n=len(scams) * 4, random_state=42)
        df_balanced = pd.concat([scams, safe_balanced])
    else:
        scams_balanced = scams.sample(n=len(safe) * 1/4, random_state=42)
        df_balanced = pd.concat([safe, scams_balanced])

    df = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

    scores = df.iloc[:, 0].tolist() 
    texts = df.iloc[:, 1:].astype(str).agg(','.join, axis=1).tolist() 

    train_texts, test_texts, train_scores, test_scores = train_test_split(
        texts, scores, test_size = 0.2, random_state=42
    )

    # for i in range(5):
    #     print(f"{train_texts[i]} : {train_scores[i]}")

    train_dataset = ScoringDataset(train_texts, train_scores, tokenizer)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Training Tools
    optimizer = AdamW(model.parameters(), lr=lr)
    criterion = torch.nn.MSELoss()

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


    # Testing 
    print("Starting Evaluation...")

    test_dataset = ScoringDataset(test_texts, test_scores, tokenizer)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    model.eval()
    total_eval_loss = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in test_loader:
            ids = batch['input_ids'].to(device)
            mask = batch['attention_mask'].to(device)
            targets = batch['score'].to(device).unsqueeze(1).float()

            outputs = model(ids, mask)
            loss = criterion(outputs, targets)

            total_eval_loss += loss.item()

            all_preds.extend(outputs.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())

    avg_test_loss = total_eval_loss / len(test_loader)
    print(f"Test Loss (MSE): {avg_test_loss:.4f}")
    mae = mean_absolute_error(all_targets, all_preds)
    print(f"Mean Absolute Error: {mae:.4f}")

    # Saving
    output_dir = f"./outputs/run_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    config = AutoConfig.from_pretrained("distilbert-base-uncased")

    model_save_path = os.path.join(output_dir, "final_model.pt")
    torch.save(model.state_dict(), model_save_path)
    tokenizer.save_pretrained(output_dir)
    config.save_pretrained(output_dir)
    print("Model, Tokenizer, and Config saved successfully!")

if __name__ == "__main__":
    train()
