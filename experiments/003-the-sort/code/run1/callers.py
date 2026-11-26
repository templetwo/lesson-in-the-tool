"""Caller interface. Two-turn build (2026-11-25): a caller takes the whole conversation so far and returns the next
reply.

  Conversation(messages, labels)  messages: [{"role": "user" | "assistant", "content": text}, ...], in order, starting
                                  with a user message. labels: the prompt's labels, used ONLY by the dry-run caller;
                                  a real adapter sends the messages and nothing else.
  caller.call(conversation, env=None) -> Reply(text, record)
                                  text: the reply text, or None when the call failed or the maker said the reply was
                                  incomplete. record: what the runner keeps about the call (never a request header,
                                  never a key).

The dry-run caller never reads a message's text and never calls anything. On turn 1 (one user message so far) it
returns LABEL | main: DRYRUN | second: none for every label; on turn 2 it returns LABEL | DRYRUN.

The real adapters live in real_callers.py, one per sorter, named "<provider>:<model id>". The top-level caller of a
runner config is "dryrun" or "by_sorter"; with "by_sorter" the config's real_callers maps each sorter to an adapter.
"""
from common import Refuse, DRYRUN

TOP_LEVEL = ("dryrun", "by_sorter")
OUTPUT_TOKEN_LIMIT = 19000
SMOKE_OUTPUT_TOKEN_LIMIT = 2000


def validate_output_token_limit(value):
    if type(value) is not int or not 1 <= value <= OUTPUT_TOKEN_LIMIT:
        raise Refuse("output_token_limit must be an integer from 1 through %d" % OUTPUT_TOKEN_LIMIT)
    return value


class Conversation(object):
    def __init__(self, messages, labels):
        self.messages = messages
        self.labels = list(labels)

    def turn(self):
        return sum(1 for m in self.messages if isinstance(m, dict) and m.get("role") == "user")


class Reply(object):
    def __init__(self, text, record):
        self.text = text
        self.record = record


class Caller(object):
    name = None
    is_dry = None
    provider = None

    def call(self, conversation, env=None):
        raise NotImplementedError


class DryRunCaller(Caller):
    name = "dryrun"
    is_dry = True

    def call(self, conversation, env=None):
        turn = conversation.turn()
        if turn == 1:
            text = "".join("%s | main: %s | second: none\n" % (label, DRYRUN) for label in conversation.labels)
        else:
            text = "".join("%s | %s\n" % (label, DRYRUN) for label in conversation.labels)
        return Reply(text, {"caller": self.name, "turn": turn})


CALLERS = {"dryrun": DryRunCaller}


def get_caller(name, require_model_match=True, output_token_limit=OUTPUT_TOKEN_LIMIT):
    if not isinstance(require_model_match, bool):
        raise Refuse("require_model_match must be a boolean")
    validate_output_token_limit(output_token_limit)
    if name in CALLERS:
        return CALLERS[name]()
    import real_callers
    if name in real_callers.ADAPTERS:
        return real_callers.get_adapter(name, require_model_match=require_model_match,
                                        output_token_limit=output_token_limit)
    raise Refuse("no caller named %r exists in this build; only %s"
                 % (name, sorted(CALLERS) + sorted(real_callers.ADAPTERS)))
