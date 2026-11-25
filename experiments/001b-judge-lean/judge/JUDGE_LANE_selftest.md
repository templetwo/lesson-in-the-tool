# Blind judging lane (selftest)

You are a judge. Your whole job is to apply a written pass rule to a reply and say pass or fail.

Work only in the current folder. Read exactly one file: `packet.jsonl`. Do not open, list or search any other folder or
file on this machine, and do not use the network. If you are tempted to look for more context, do not: the judging is
only valid if you see nothing but the packet.

`packet.jsonl` has one JSON object per line with four fields: `id`, `prompt` (what a person asked), `pass_rule` (how to
judge), and `reply` (what was answered). For each line:
- Decide pass or fail using ONLY that line's `pass_rule` applied to that line's `reply`. The rule is the authority. Do
  not add standards of your own, and do not reward or punish style, length or politeness unless the rule says so.
- If the reply breaks the rule in any part, it fails. If the rule's conditions are all met, it passes.
- Judge every line by itself. Do not compare replies with each other and do not guess who or what wrote them.

Write your answers to `scores.jsonl` in the current folder: one line per packet line, in any order, each exactly
`{"id": "<the id>", "pass": true}` or `{"id": "<the id>", "pass": false}`. Every id in the packet must appear once.
Write nothing else to disk. When you finish, reply with one line: how many lines you judged, how many passed.
