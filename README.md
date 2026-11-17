# FOOD01 · BUC2.2 demo site

The demo site for Nestlé Vietnam, hosted on Cloudflare Pages at **https://buc2-2-food1-demo.sozolab.tech**.

| URL | Page |
|---|---|
| `/` | **Consumer Truth Hub**: the dashboard (home page) |
| `/surveys` | Hub: survey list |
| `/surveys/v1` | Hub: results for "Kids' energy drinks: what matters most to parents" |
| `/inbox`, `/mapping`, `/integration`, `/insights`, `/ingestion`, `/landscape`, `/team`, `/workspace-settings`, `/survey-settings`, `/settings` | The other Hub pages, matching the sidebar |
| `/s/v1/` | **Outcome Survey**: the survey parents take. The link on `/surveys/v1` opens it. |
| `/overview/` | Optional intro page about both prototypes, with screenshots. Delete the folder if you don't want it. |

Any other path opens the Hub, and the Hub sends unknown paths to the dashboard.

Everything is plain static files with no build step. All data is sample data and stays in the visitor's browser.

## Files

```
index.html          Consumer Truth Hub (from the claude.ai artifact, with clean-path routing added)
s/v1/index.html     Outcome Survey (from the claude.ai artifact)
overview/index.html intro page
assets/             logo, screenshots, link-preview image (og.jpg)
_headers            Cloudflare response headers: noindex, basic security headers, asset caching
robots.txt          keeps search engines out
favicon.svg
tools/import_artifact.py   re-imports either app from claude.ai
tools/serve.py             local preview that behaves like Cloudflare Pages
```

**Don't add a top-level `404.html`.** Without one, Cloudflare Pages serves `index.html` for any path that isn't a file. That's how `/surveys` and the other clean URLs work. GitHub Pages has no equivalent, so it can't host this version.

## Deploy on Cloudflare Pages

1. In Cloudflare, open **Workers & Pages › Create › Pages**. Then do one of these:
   - **Connect to Git** and pick the GitHub repository. Framework preset: **None**. Leave the build command empty. Set the output directory to `/`.
   - **Upload assets** and drag in this folder. You'll need to re-upload after every change.
2. In the project, open **Custom domains** and add `buc2-2-food1-demo.sozolab.tech`. `sozolab.tech` is already on Cloudflare, so the DNS record is created for you.
3. Optional: limit who can open it with Cloudflare Access (**Zero Trust › Access › Applications**), for example to `@sozolab.tech` emails.

## Preview locally

```bash
python3 tools/serve.py 4173
```

Then open http://localhost:4173. Clean paths such as http://localhost:4173/surveys work here too.

## Refreshing the apps from claude.ai

When either artifact changes on claude.ai, save its page (for example with Claude's Artifact *read* action, which writes the HTML to disk). Then, from this folder:

```bash
python3 -I tools/import_artifact.py hub <saved-hub.html>
```

```bash
python3 -I tools/import_artifact.py survey <saved-survey.html>
```

For the Hub, the script reapplies the routing patches and stops with an error if the Hub's code has changed so that a patch no longer fits. The docstring at the top of the script lists every patch.

## Sources

- Consumer Truth Hub: https://claude.ai/artifact/X475n5iG8WFNEG6x3yWEEj
- Outcome Survey: https://claude.ai/artifact/Juw4NKTQZ6eNrMLp6R8YL4
