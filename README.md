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
