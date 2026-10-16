# AI usage disclosure

This record describes the AI assistance in this Codex conversation. Review it and correct anything that does not match your own account before submitting.

## AI tools used

- OpenAI Codex desktop, model identified in this session as GPT-6. The exact build/version was not exposed in the conversation UI.

## Prompts provided to the tools

- The full pasted company assignment, **“AI-Assisted Box Selection System — Django Hiring Assignment,”** asking for a complete Django packaging recommendation app, staged implementation, tests, documentation, and an honest disclosure template.
- Follow-up requests to run the project, add sample products and remove any AI watermark, and replace the dashed product dropdown placeholder.
- The pasted **“Final Project Audit, Bug Fixing and Test Verification — BoxWise Django Assignment”** requesting an audit, bug fixes, broad tests, documentation updates, and final verification.

The real exported conversation is still required separately; use it as the authoritative full prompt record.

## Outputs accepted

- The working Django models, forms, views, templates, recommendation service, migration, test suite, demo-catalog command, README, and GitHub Actions workflow were produced or updated during this conversation and remain in the project.
- The deterministic packing approach and its limitations were documented. Demo products and boxes were added to the local SQLite database through the repeatable `seed_demo` command.

## Outputs rejected or modified

- The dashed empty product option was changed to the clearer “Select a product” prompt.
- The duplicate-line validation was revised after testing showed Django's default uniqueness message appeared before the custom message.
- No application attribution or watermark was present to remove. The required AI disclosure was retained.

## Mistakes discovered in AI output

- An earlier `TEST_OUTPUT.md` recorded 18 tests but said “Found 16 test(s).” The audit caught the contradiction; the file is being updated with the latest captured run.
- The initial duplicate-line view implementation used a private formset attribute. It was replaced with public formset validation and covered by a regression test.
- The quantity input initially advertised a minimum of zero even though zero was invalid. The form now enforces a minimum of one in both browser markup and server-side validation.

## How the final code was verified

Record final results after the last run. The latest captured run for this audit is dated 2026-10-17 (Asia/Kolkata):

- `python3 --version`: Python 3.13.15.
- `python3 -m django --version`: Django 5.2.18.
- `python3 -m pip check`: no broken requirements found.
- `python3 manage.py check`: no issues.
- `python3 manage.py makemigrations --check --dry-run`: no changes detected.
- `python3 manage.py migrate --noinput`: no migrations pending; the existing database was preserved.
- `python3 manage.py test`: 33 tests passed, 0 failed.
- The workflow YAML was parsed locally with Ruby's YAML library. A remote GitHub Actions run was not performed.

## Chat transcript and personal learning reflection

- **Transcript:** Not yet exported or included. Export the real current conversation and place the actual exported file under `submission/` (for example `submission/chat-transcript.html`); do not create a replacement transcript.
- **Personal reflection:** Not written by the assistant. Complete `LEARNING_REFLECTION.md` in your own words before submission.
