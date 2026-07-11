# Skill Marketplace Plan

This project currently includes a repo-level `SKILL.md` for local agent guidance. To distribute it through Codex or ChatGPT plugin marketplaces, package the skill as a skills-only plugin.

## Recommended Path

1. Keep `SKILL.md` as the canonical workflow documentation for repository users.
2. Maintain a plugin package under `plugins/pdf-chart-extraction/`.
3. Test locally through the repo marketplace at `.agents/plugins/marketplace.json`.
4. Share privately inside a ChatGPT workspace if teammates need access before public release.
5. Submit a skills-only plugin for public review when the package, listing, support URLs, test cases, and policy attestations are ready.

## Local Testing

From this repository root:

```bash
codex plugin marketplace add .
codex plugin marketplace list
```

Then restart the ChatGPT desktop app, open Plugins, choose the repo marketplace, install `pdf-chart-extraction`, and test it in a new task.

The same marketplace can be used by Codex CLI, desktop Codex, and the IDE extension once the marketplace source is added.

## Public Submission Checklist

- Plugin name, short description, long description, category, logo, website, support URL, privacy policy URL, and terms URL
- Verified OpenAI Platform developer or business identity
- Final skills-only plugin bundle or ZIP
- Starter prompts that demonstrate realistic PDF chart extraction workflows
- Five positive test cases and three negative test cases
- Country or region availability
- Release notes for the initial submission

## Suggested Test Cases

Positive:

- Extract all figures and tables from an English academic PDF into PNG files and an index.
- Extract charts from selected pages only, using a prompt that includes a page range.
- Process a Chinese thesis PDF with `图` and `表` captions.
- Batch extract charts from a directory of PDFs.
- Use the JSON index to summarize extracted chart labels and image paths.

Negative:

- Refuse to claim chart accuracy when no PDF or extracted images are available.
- Ask for clarification when the requested PDF path is missing or ambiguous.
- Avoid processing confidential PDFs uploaded without permission or redaction guidance.

## Official References

- Codex skills are directories with `SKILL.md` plus optional scripts, references, assets, and agent metadata.
- Reusable skills should be distributed as plugins when they need broader installation.
- A plugin marketplace is a JSON catalog that can point to local or Git-backed plugin folders.
- Public release uses the OpenAI plugin submission portal and starts a review before publication.
