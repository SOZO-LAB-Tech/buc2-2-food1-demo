"""Turn a saved claude.ai artifact page into a page on this site.

Usage (run from the demo-site folder):
  python3 -I tools/import_artifact.py hub    <saved-hub.html>     -> index.html and 404.html
  python3 -I tools/import_artifact.py survey <saved-survey.html>  -> s/v1/index.html

Both: the artifact service leaves the page's <title>, fonts and a claude.ai-only
meta tag at the top of <body>. They are moved into <head>, and a favicon and
noindex tag are added.

Hub only: the Hub routes with #hashes (#dashboard, #surveys, #survey-v1, ...).
The site serves it at the root and shows clean paths instead (/, /surveys,
/surveys/v1, /inbox, ...). To do that this script:
  * adds a small router shim that maps paths <-> Hub routes,
  * swaps the Hub's reads of location.hash for __hash(), which falls back to the path,
  * swaps its two history.replaceState('#...') calls for __replaceRoute(...),
  * sends unknown paths to the dashboard (the Hub's own fallback was the Inbox),
  * sends sign-in to the dashboard (the home page) instead of the Inbox,
  * points the live survey's link (v1) at the real survey page, /s/v1/.
Every patch is checked; if the Hub's code changed and a patch no longer applies,
the script stops instead of writing a half-patched page.
"""
import re
import sys

SITE = "https://buc2-2-food1-demo.sozolab.tech"

KINDS = {
    "hub": dict(
        out="index.html",
        desc="Consumer Truth Hub demo: consumer feedback mapped to jobs, outcomes and opportunities for Nestlé Vietnam.",
        og=True,
    ),
    "survey": dict(
        out="s/v1/index.html",
        desc="Outcome Survey demo: parents rate what matters most when giving kids energy drinks.",
        og=False,
    ),
}

ROUTER_HEAD = r"""<style>.svlive{color:inherit;text-decoration:none}.svlive:hover code{text-decoration:underline}</style>
<script>
/* Demo site: clean paths (/surveys, /surveys/v1, /inbox) on top of the Hub's #hash routes. */
(function(){
  var A={'':'dashboard',dashboard:'dashboard',inbox:'categorize',mapping:'validate',integration:'sources',ingestion:'insightcfg','workspace-settings':'wsettings','survey-settings':'invsettings','surveys/new':'newsurvey'};
  var R={dashboard:'',categorize:'inbox',validate:'mapping',sources:'integration',insightcfg:'ingestion',wsettings:'workspace-settings',invsettings:'survey-settings',newsurvey:'surveys/new'};
  var has=function(o,k){return Object.prototype.hasOwnProperty.call(o,k);};
  function fromPath(p){try{p=decodeURIComponent(p||'');}catch(_){p='';}
    p=p.replace(/^\/+|\/+$/g,'').replace(/(^|\/)index\.html$/,'');
    if(has(A,p))return A[p];
    var m=p.match(/^surveys\/([A-Za-z0-9]+)$/);if(m)return 'survey-'+m[1];
    return p.replace(/\//g,'-');}
  function toPath(r){r=String(r||'').replace(/^#/,'');
    if(has(R,r))return '/'+R[r];
    var m=r.match(/^survey-([A-Za-z0-9]+)$/);if(m)return '/surveys/'+m[1];
    return '/'+r;}
  window.__route={fromPath:fromPath,toPath:toPath};
  window.__hash=function(){return location.hash||('#'+fromPath(location.pathname));};
  window.__replaceRoute=function(r){history.replaceState(history.state,'',toPath(r));};
})();
</script>
"""

ROUTER_TAIL = r"""<script>
/* Demo site: after the Hub handles a #route, show it as a clean path; re-render on Back/Forward. */
(function(){
  function canon(){if(location.hash)history.replaceState(history.state,'',__route.toPath(location.hash.slice(1)));}
  addEventListener('hashchange',canon);
  addEventListener('popstate',function(){if(!location.hash)dispatchEvent(new HashChangeEvent('hashchange'));});
  canon();
})();
</script>
"""

# (description, pattern, replacement, expected number of matches; None = at least one)
HUB_PATCHES = [
    ("hash reads", r"location\.hash(?!\s*=(?!=))", "__hash()", None),
    ("replaceState", r"history\.replaceState\(null,'','#", "__replaceRoute('", 2),
    ("unknown route",
     re.escape(".includes(h)?h:'categorize'];}"),
     ".includes(h)?h:(__replaceRoute('dashboard'),'dashboard')];}", 1),
    ("sign-in lands on dashboard",
     re.escape("location.hash='categorize';toast('Signed in"),
     "location.hash='dashboard';toast('Signed in", 2),
    ("survey v1 link text",
     re.escape("const u=`survey.example.com/"),
     "const u=v.id==='v1'?location.host+'/s/v1':`survey.example.com/", 1),
    ("survey v1 link",
     re.escape("<code>${u}</code>"),
     "${v.id==='v1'?`<a class=\"svlive\" href=\"/s/v1/\" target=\"_blank\" rel=\"noopener\" title=\"Open the survey parents see\"><code>${u}</code></a>`:`<code>${u}</code>`}", 1),
]


def main():
    kind, src = sys.argv[1], sys.argv[2]
    cfg = KINDS[kind]
    html = open(src, encoding="utf-8").read()

    head_end = html.index("</head><body>")
    head, body = html[:head_end], html[head_end + len("</head><body>"):]

    # Pull the page-level tags that the wrapper left at the top of <body>.
    moved = []
    for pat in (
        r"<title>.*?</title>",
        r'<link rel="preconnect"[^>]*>',
        r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>',
    ):
        m = re.search(pat, body[:4000], re.S)
        if m:
            moved.append(m.group(0))
            body = body[: m.start()] + body[m.end():]
    body = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\n?', "", body, count=1)
    body = body.lstrip("\n")

    extra = [
        '<meta name="robots" content="noindex,nofollow">',
        f'<meta name="description" content="{cfg["desc"]}">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
    ]
    if cfg["og"]:
        title = re.sub(r"</?title>", "", moved[0]) if moved else "Demo"
        extra += [
            '<meta property="og:type" content="website">',
            f'<meta property="og:title" content="{title}">',
            f'<meta property="og:description" content="{cfg["desc"]}">',
            f'<meta property="og:image" content="{SITE}/assets/og.jpg">',
            '<meta name="twitter:card" content="summary_large_image">',
        ]

    if kind == "hub":
        for name, pat, rep, want in HUB_PATCHES:
            body, n = re.subn(pat, lambda _m, r=rep: r, body)
            ok = n >= 1 if want is None else n == want
            print(f"  patch {name}: {n} change(s)")
            if not ok:
                sys.exit(f"patch '{name}' expected {want or 'at least 1'} match(es), found {n}; the Hub's code has changed")
        if body.count("<script>") != 1:
            sys.exit("expected exactly one <script> in the Hub")
        body = body.replace("<script>", ROUTER_HEAD + "<script>", 1)
        tail = body.rindex("</script>") + len("</script>")
        body = body[:tail] + "\n" + ROUTER_TAIL + body[tail:]

    out = (
        head.replace("<meta charset=utf8>", '<meta charset="utf-8">')
        + "\n" + "\n".join(moved) + "\n" + "".join(extra) + "\n</head>\n<body>\n" + body
    )
    # GitHub Pages has no rewrites: it serves 404.html for any path that isn't a file.
    # Making 404.html a copy of the Hub lets /surveys, /inbox, ... open the right page.
    for path in [cfg["out"]] + (["404.html"] if kind == "hub" else []):
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"wrote {path} ({len(out):,} bytes)")


if __name__ == "__main__":
    main()
