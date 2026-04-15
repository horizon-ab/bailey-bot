import torch
import os
import re
import emoji
from transformers import AutoTokenizer

from model.src.model import ScamScorer

def clean_text(text):

    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    user_pattern = r'<@(?:!|&)?\d+>|@everyone|@here'
    discord_invite_pattern = r'(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/([a-zA-Z0-9-]{2,32})'
    custom_emoji_pattern = r'<(a?):(\w+):(\d+)>'
    giveaway_pattern = r'(?i)\b(?:giving\s+away|giveaway|free|winner|win|claim)\b'
    dm_pattern = r'(?i)\b(?:dm|pm|hmu|msg|message|direct\s+message)\s+me\b'

    text = re.sub(discord_invite_pattern, "<DISCORD_INVITE>", text)
    text = re.sub(url_pattern, "<URL>", text)
    text = re.sub(user_pattern, "<USER>", text)
    text = re.sub(custom_emoji_pattern, "<EMOJI>", text)
    text = emoji.replace_emoji(text, replace="<EMOJI>")
    text = re.sub(giveaway_pattern, "<GIVEAWAY>", text)
    text = re.sub(dm_pattern, "<DM_ME>", text)

    return text

def load_model(run_dir):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(run_dir)
    model = ScamScorer("distilbert-base-uncased", vocab_size=len(tokenizer))

    weights_path = f"{run_dir}/final_model.pt"
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Weights not found at {model_path}. Did you run training?")


    model.load_state_dict(torch.load(weights_path, map_location=device))

    model.to(device)
    model.eval()

    return model, tokenizer, device

def predict(text, model, tokenizer, device):
    
    cleaned_text = clean_text(text)

    # print(cleaned_text)

    inputs = tokenizer(
        cleaned_text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256
    ).to(device)

    with torch.no_grad():
        output = model(inputs['input_ids'], inputs['attention_mask'])

    return output.item()

if __name__ == "__main__":
    
    RUN_FOLDER = "./outputs/run_20260331-203654"

    model, tokenizer, device = load_model(RUN_FOLDER)

    scam_texts = ["@everyone Giving away my Canon EOS R7 Mirrorless Camera (Body Only), Hybrid Camera, 32.5 Megapixel (APS-C) CMOS Sensor, 4K Video, for Sports, Action, Content Creators, Vlogging Camera, Black Comes with extra lens DM me if interested", "Hello everyone I never thought I’d be in this position, but life has taken an unexpected turn. I have 4 amazing seats for the upcoming Ariana Grande concert on Sunday, June 14, 2026 at 8:00 PM at Cryptocom Arena in Los Angeles. These tickets promise an incredible view and an unforgettable night. Unfortunately, I’m no longer able to attend, so I’m hoping to pass these tickets along to someone who can truly enjoy the experience. It would mean a lot to know they’re going to a real fan who will make the most of the show. If you’re interested, please reach out to me privately. Thank you so much for taking the time to read this, and for any help you can offer Please DM or text if you’re interested:", "Hey! @everyone  I’m looking to sell my tickets to Ariana Grande concert at Crypto Arena, Los Angeles, CA! (Date; Sunday, June 14). HMU if you’re interested ❤️, MSG on iMessage if you want them! +12139355757"]

    good_texts = ["Does anyone have a clipboard we can use for specifically April 10th session", "Hello everyone, I'm Aiden, I want to keep this message short. So the reason I would like to join this club is because I want to learn how to get groovy with it", "Thank you", "Hello", "Hello everyone"]

    print("\nStart Scam Texts...\n")

    for text in scam_texts:
        score = predict(text, model, tokenizer, device)
        print(f"Score: {score:.4f}")

    print("\nStart Good Texts...\n")

    for text in good_texts:
        score = predict(text, model, tokenizer, device)
        print(f"Score: {score:.4f}")

