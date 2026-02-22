# model.py

import bot
from transformers import pipeline

pipe = pipeline("text-generation", model="deepseek-ai/DeepSeek-R1-Distill-Llama-8B")
initial_prompt = [
    {"role" : "system", "content" : "You are part of a Discord bot monitoring new users' messages. Use Chain-of-Thought reasoning."},
    {"role" : "user", "content" : "For the next message that is passed in, analyze the message and generate a confidence score based on how likely the user is to be a scammer. Scammers include people trying to sell belongings, tickets, etc. or trying to make people join their own Discord servers. They will typically ask other users to message them for more details or leave some method of communication open. Keep in mind that the Discord server is related to breakdancing, so be more lenient if the messages are related to breakdancing. Specifically, return only a single numeric value ranging from 0.00 to 1.00. An example would be \"0.85\". If you are unsure, then it is okay to return a lower score, as real humans will manually verify the message. But be confident on the obvious scammers."}
]

def judge(questionable_msg):

    total_prompt = initial_prompt
    total_prompt.append({"role" : "user", "content" : questionable_msg })

    print(pipe(total_prompt))

    return 0.5


def main():


if __name__ == "__main__":
    judge("I have a brand new PS5 that I'm looking to sell. Please DM me if you're interested!")



