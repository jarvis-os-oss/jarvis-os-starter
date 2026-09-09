# Onboarding a new agent by interview

The kit is data-driven: a new agent is a `SOUL.md` plus a roster entry in
`dashboard/team_config.json` (see the README "Customising the team"). You can
write the `SOUL.md` by hand from `agents/_TEMPLATE.SOUL.md`. This file offers a
faster, more reliable path: let the orchestrator (or any Hermes chat) **interview you**
and draft the soul file, instead of filling a template freehand.

Why an interview instead of freehand: the template's angle-bracket fields are
easy to leave vague, and a vague `SOUL.md` produces a vague agent. A structured
question-by-question pass forces the two things that actually matter for a team
member: a sharp boundary of what it owns, and an explicit list of what it must
never do without approval.

## How to use it

Open a Hermes chat (terminal or Telegram) and paste the prompt below. Answer the
questions one at a time in plain language. At the end you get a `SOUL.md` and a
roster snippet to review before anything is written.

This defines **one sub-agent** at a time. Keep the team's shape in mind: every
agent reports to the orchestrator, hands off through the orchestrator, and never
both writes code and signs off on its own deployment (the developer/maintenance
split in `docs/BRANCH_PROTECTION.md`).

## The interview prompt (copy this)

```
You are helping me add one new sub-agent to an AI-OS team. One coordinator (the
orchestrator) runs the team; every sub-agent takes work from the orchestrator,
reports back to it, and pulls in other agents only through it. Before writing
anything, INTERVIEW
me. Ask these questions ONE at a time and wait for my answer after each:

1. What is this agent's name and its one-line role, the way you would introduce
   a new hire to the team?
2. What does it own day to day? List the concrete tasks that are clearly its job.
3. What is explicitly NOT its job, so it hands those off to another agent
   through the orchestrator instead of doing them itself?
4. How should it work: which tools, conventions, and (if it changes systems) what
   branch, handoff, or review steps does it follow?
5. What must it NEVER do without my explicit approval (send, publish, spend,
   book, delete, deploy)?
6. When should it stop and escalate to the orchestrator rather than decide on its own?
7. How should it talk: terse and factual, or fuller with reasoning? Any severity
   tags or format it should always use?
8. What free port should its cockpit roster entry use, and what accent colour?

If an answer is vague, ask exactly one follow-up. Invent nothing.

Then produce TWO things and SHOW them to me BEFORE writing any file:

A. agents/<key>.SOUL.md, following the section order in
   agents/_TEMPLATE.SOUL.md (Role, Scope, Way of working, Collaboration,
   Escalation, Communication style, Hard rules). Keep it lean; every character
   ships on every single turn (see the length note in agents/README.md). The
   Hard rules section MUST keep: never send/spend/book without explicit
   approval; no em-dashes; never expose secrets; verify before handoff.

B. a dashboard/team_config.json entry: {key, name, role, desc, port, accent}.

Wait for my go-ahead, then write agents/<key>.SOUL.md and tell me exactly which
roster entry to add.
```

## The question that matters most

Question 5 is the one people skip. A soul that lists what the agent does but not
what it must never do is the soul you switch off after two days. "Draft always,
send never" is not timidity, it is the difference between an agent you leave
running and one you do not trust. Keep the guardrail even when the agent feels
reliable, and re-read `docs/GOING_LIVE.md` before the team runs unattended.

## After the interview

1. Save the drafted soul as `agents/<key>.SOUL.md`.
2. Add the roster entry to `dashboard/team_config.json`.
3. Create the profile and give it the soul:
   `hermes profile create <key> --clone-from default --description "<role>"`,
   then copy `agents/<key>.SOUL.md` over that profile's `SOUL.md`
   (see the README "Creating the agent profiles", including the one-bot-per-agent
   Telegram rule).
