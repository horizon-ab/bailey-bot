# Bailey Bot

## Functionality

### Monitoring

Bailey Bot monitors all messages sent in specified channels. 

### Judgement

Bailey Bot uses an LLM (from HuggingFace) to review the message content and will return a judgement score. If the judgement score is above a certain threshold, it will automatically 

## Commands

`/test`
Enables/disables testing mode. In testing mode the bot is not allowed to enforce judgement (i.e. ban users).

`/set`
Adds a channel to be monitored.

`/remove`
Removes a channel to be monitored.

`/review`

`/confidence_auto`
Sets confidence threshold for auto ban. If `score > confidence_auto`, then the bot will automatically enforce judgement.

`/confidence_manual`
Sets confidence threshold for manual review. If score 
