# Bailey Bot

## Functionality

### Monitoring

Bailey Bot monitors all messages sent in specified channels. Specified channels can be set by moderators.  Only the first few messages (specified by `message_threshold`) sent by a given user will be checked.

### Judgement

Bailey Bot uses an LLM (DeepSeek-R1-Distill-Llama-8B from HuggingFace) to review the message content and will return a judgement score. If the judgement score is above a certain threshold, it will automatically delete the message and ban the offending user. If the judgement score is above a lower threshold, it will ping a moderator for manual review. If testing mode is enabled, only manual review will be permitted. Both of these thresholds can be set by a moderator.

## Commands

`/test`
Enables/disables testing mode. In testing mode the bot is not allowed to enforce judgement (i.e. ban users).

`/set`
Adds a channel to be monitored.

`/remove`
Removes a channel to be monitored.

`/review`

`/confidence_auto`
Sets confidence threshold for auto ban. If `score >= confidence_auto`, then the bot will automatically enforce judgement. By default, this is `0.9`.

`/confidence_manual`
Sets confidence threshold for manual review. If `confidence_auto > score >= confidence_manual`, then the bot will ping a moderator for manual review. By default, this is `0.7`

`/message_threshold`
Sets message threshold for monitoring. The first `message_threshold` messages will be checked by the bot. 
