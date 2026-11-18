# FOOD01 · BUC2.2 demo site

The demo site for Nestlé Vietnam, hosted on GitHub Pages at **https://buc2-2-food1-demo.sozolab.tech**, with DNS on Cloudflare.

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
404.html            identical copy of index.html (see below)
s/v1/index.html     Outcome Survey (from the claude.ai artifact)
overview/index.html intro page
assets/             logo, screenshots, link-preview image (og.jpg)
CNAME               custom domain for GitHub Pages
.nojekyll           tells GitHub Pages to publish the files as-is
_headers            response headers, used only if the site is moved to Cloudflare Pages
robots.txt          keeps search engines out
favicon.svg
tools/import_artifact.py   re-imports either app from claude.ai
tools/build_demo_data.py   builds the chat demo's data and Excel file
assets/demo/               Chat with Evidence demo: script, data, Excel file
tools/serve.py             local preview that behaves like GitHub Pages
```

**Why 404.html is a copy of the Hub:** GitHub Pages can't rewrite URLs. For any path that isn't a file, it serves `404.html`. Because that file is the Hub, `/surveys`, `/inbox` and the other paths open the right page. These pages return HTTP status 404, which visitors don't see, but Zalo or Slack may skip the link preview for them. The home page `/` returns 200. The import script writes both files, so keep them identical.

## Hosting

- **GitHub Pages:** repository `SOZO-LAB-Tech/buc2-2-food1-demo` (public), branch `main`, folder `/`. Every push to `main` republishes the site within about a minute.
- **Custom domain:** set in **Settings › Pages** and in the `CNAME` file.
- **DNS (Cloudflare, zone `sozolab.tech`):** record `CNAME buc2-2-food1-demo → sozo-lab-tech.github.io`, proxy status **DNS only** (grey cloud). Once GitHub shows the certificate as ready, tick **Enforce HTTPS** under Settings › Pages.
- **Optional:** verify `sozolab.tech` for the organization (**Org settings › Pages › Add a domain**, a TXT record). That stops other GitHub accounts from claiming subdomains of it.
- **Privacy:** the repository and the site are public, so anyone with the link can open them. Search engines are asked not to index the site (`noindex` and `robots.txt`).

To move to Cloudflare Pages instead, connect the repository there with no build command and output directory `/`. The site works there unchanged.

## Chat with Evidence demo

A scripted conversation in the Hub's **Chat with Evidence** panel (the round button at the bottom right of every page):

1. **Ask about complaints.** For example: "Did anyone complain about Nescafé in 2025?" This is also the first suggestion in an empty chat. The answer gives the survey share, the number of complaint reports and the top three themes with quotes. It ends by offering a breakdown.
2. **Ask for a breakdown.** "Show by age group", "by region", "by gender", or "demographic" (gender and region together). The answer adds a donut chart of the share of complaints and a bar chart of the complaint rate per group.
3. **Ask to download.** "Download as Excel" or "export". The answer shows a file card with a real `.xlsx` file: summary, one sheet per breakdown with charts, and all 1,146 complaint rows.
4. **Ask what to fix first.** "What should we fix first?" The answer gives three priorities, each tied to a theme and an age group.

Each answer ends with chips for the next step. Questions can also be typed freely; the demo recognises the wording loosely, and Vietnamese without accents works for the main terms. Asking about Nescafé from another product's chat switches the chat to Nescafé. Any question the demo doesn't recognise gets the Hub's normal answer.

| File | What it is |
|---|---|
| `assets/demo/demo-chat.js` | Recognises the questions and writes the answers, charts, file card and chips. Loaded after the Hub's script. |
| `assets/demo/nescafe-2025.json` | The numbers the chat uses |
| `assets/demo/nescafe-complaints-2025.xlsx` | The file offered for download |
| `tools/build_demo_data.py` | Writes both data files from one set of numbers, so they always agree |

All figures are made-up sample data, and the Excel file says so on its first sheet. To change the story, edit the numbers at the top of `tools/build_demo_data.py`, then run:

```bash
python3 tools/build_demo_data.py
```

It needs `openpyxl`.

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
