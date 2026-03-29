# model.py

from transformers import pipeline
import torch
import os

os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
pipe = pipeline("text-generation",
                model="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
                dtype=torch.bfloat16,
                )
initial_prompt = [
    {"role" : "system", "content" : "You are part of a Discord bot monitoring new users' messages. Do not spend too much time thinking"},
    {"role" : "user", "content" : "For the next message that is passed in, analyze the message and generate a confidence score based on how likely the user is to be a scammer. Scammers include people trying to sell belongings, tickets, etc. or trying to make people join their own Discord servers. They will typically ask other users to message them for more details or leave some method of communication open. Keep in mind that the Discord server is related to breakdancing, so be more lenient if the messages are related to breakdancing. Specifically, return only a single numeric value ranging from 0.00 to 1.00. An example would be \"0.85\". If you are unsure, then it is okay to return a lower score, as real humans will manually verify the message. But be confident on the obvious scammers."}
]


def judge(questionable_msg):

    prompt = f"""<｜User｜> 
    Task: Return likelihood of people selling something in public chat. Return only a single number. 
    Example: \"I'm selling a used PS5\" -> 0.95
    Example: \"Hi, I'm new to the club! Could someone show me around?\" -> 0.2
    Input: \"{questionable_msg}\"
    <｜Assistant｜><think>"""

    out = pipe(prompt,
               max_new_tokens=1024,
               temperature=0.6,
               repetition_penalty=1.2,
               )
    out_text = out[0]["generated_text"]
    thinking = ""
    answer = ""

    if "<think>" in out_text and "</think>" in out_text:
        good_stuff = out_text.split("<think>")[1]
        split_stuff = good_stuff.split("</think>")
        thinking = split_stuff[0].strip()
        answer = split_stuff[1].strip()

    else:
        answer = out_text

    return answer, thinking


if __name__ == "__main__":
    answer, thinking = judge("Hi, I'm Bailey, and I'm really excited to be here! I also have some tickets for the next Taylor Swift concert if anyone's interested in them.")
    print(f"Answer: {answer}")
    print(f"Thinking: {thinking}")



