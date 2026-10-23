# extract-persona fixtures

Offline fixtures for `test/extract_persona_test.py`. The subject, "Captain Marlow
Vance", is invented for tests; every source below is fictional text written for
this repo, so there are no rights or privacy questions and no network access.

| File | Simulates | add-source flags |
| --- | --- | --- |
| `podcast-harbor-talk.txt` | speaker-labelled podcast transcript with timestamps | `--type podcast --attribution mixed --context casual` |
| `essay-fix-the-boat.txt` | the subject's own essay | `--type writing --attribution subject --context work` |
| `profile-article.txt` | third-party profile with quoted lines | `--type article-about --attribution about` |
| `hearing-transcript.txt` | hostile hearing transcript (pressure) | `--type transcript --attribution mixed --context pressure` |
| `analysis.json` | the agent-written analysis (v1 lens fields + evidence-mapped v2 sections); evidence ids are filled in by the test |
