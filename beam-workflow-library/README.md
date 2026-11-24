# Beam Workflow Library

A small, local-first library of six reusable workflows for working with an AI session. Built by Viktor for @beamnxw; this is v1 plus one addition: exporting all favourites as a single Markdown file (see below).

## Use it

Download [index.html](./index.html) and open the saved file in a browser. GitHub's file viewer shows the source, not the running app. No installation, account, API key or build step is needed.

Search the cards, filter by category or role, save favourites, copy a complete prompt, export a card as Markdown, or export all your favourites as one Markdown file. Replace the prompt's `{{PLACEHOLDERS}}` before using it in your AI session.

### Export all favourites as one Markdown file

1. Press **☆ Add favourite** on each workflow you want to keep.
2. Press **Export favourites as Markdown (N)** under the filters. The browser saves `beam-workflow-favourites.md`.

The file starts with the export date and the number of favourites, then lists each favourite in library order (BWL-001 first). Each entry has its ID, title, category, role sequence, task, inputs, steps, the full prompt in a code fence, completion checks, authority boundaries and its sources as links. Workflows that are not favourites are not included. Search and filters do not change what is exported.

With no favourites the button does not download anything; the page tells you to add a favourite first. If your browser blocks the download, a "Markdown text" box opens so you can copy the same text by hand. The single-card **Export as Markdown** button on each workflow works as before.

For more consistent clipboard and favourites behaviour, serve this folder locally:

```sh
python -m http.server 8000 --bind 127.0.0.1
```

On Windows, you can use `py` instead of `python`. Open `http://127.0.0.1:8000` in your browser. Python is only needed for this optional local server.

## The six workflows

1. **BWL-001:** Research a technical topic.
2. **BWL-002:** Turn research into a technical guide.
3. **BWL-003:** Plan a product feature.
4. **BWL-004:** Build an agreed feature.
5. **BWL-005:** Evaluate a result and report issues.
6. **BWL-006:** Write a handoff for the next session.

## Files and data

- `index.html` contains the complete app, workflow data, styles and embedded images. It makes no network requests on load. Source links open only when clicked.
- `workflows.json` is a readable copy of the six cards. The app does not fetch this file; its data lives in the `workflow-data` script block inside `index.html`. If you edit the cards, keep both copies in sync.
- `tests/test_export_favourites.py` is a developer-only check for the favourites export (Playwright with headless Chromium, run on a developer machine). It is not needed to use the library and adds no runtime dependency. `docs/` holds before/after screenshots and an example export file for the pull request that added this feature.
- Favourites are stored in this browser's local storage. Availability depends on browser settings, especially when opening a file directly. Clipboard and download fallbacks support manual copying.

## Scope and provenance

These cards are original beamnxw adaptations of public guidance, not official Anthropic presets. The app prepares instructions for you to paste elsewhere; it does not run a model, automate tasks or orchestrate agents. Roles describe sequential responsibilities, not separate autonomous workers.

This is a v1 snapshot, not a claim that the prompts have been validated. None of the six prompts has been tested in a separate model session. Real-device and screen-reader testing remains outstanding.

The original app includes supplied Clawd and Viktor artwork with recorded source URLs and hashes. Those records are provenance, not a licence verification. Third-party artwork and trademarks are not licensed by this repository's MIT licence; no ownership of those marks or endorsement by their owners is claimed. Review the relevant permissions before reusing the artwork.

Private conversations, internal reports and the original input packet are not included.
