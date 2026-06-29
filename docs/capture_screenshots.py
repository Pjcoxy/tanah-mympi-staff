#!/usr/bin/env python3
"""Capture the guide screenshots from the LIVE site using headless Edge.

Writes docs/screenshots/{login,form,dashboard}.png. The login and dashboard are
captured straight from the live URLs; the form is captured from a local copy of
index.html auto-advanced to the sign-off screen (so the "Logged in as" banner and
checklist show without a real login).

Usage:  python docs/capture_screenshots.py   then   python docs/build_docs.py
Re-run after any UI change.
"""
import os, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "docs", "screenshots")
EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
LIVE = "https://pjcoxy.github.io/tanah-mympi-staff/"

AUTO_FORM = """
<script>
window.addEventListener('load', function(){
  setTimeout(function(){
    try{
      showForm('Pete C');
      var r=document.getElementById('roomNum'); if(r){ r.value='103'; if(typeof enableServiceType==='function') enableServiceType(); }
      var s=document.getElementById('serviceType'); if(s){ s.value='full'; if(typeof updateServiceItems==='function') updateServiceItems(); }
    }catch(e){ document.title='ERR '+e.message; }
  }, 400);
});
</script>
"""


def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("Could not find msedge.exe. Edit EDGE_CANDIDATES.")


def shot(edge, url, name, w, h):
    out = os.path.join(SHOTS, name)
    if os.path.exists(out):
        os.remove(out)
    subprocess.run([edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--window-size={w},{h}",
                    "--virtual-time-budget=9000", f"--screenshot={out}", url],
                   timeout=90)
    print(f"{name}: {'OK' if os.path.exists(out) else 'FAILED'}")


def main():
    edge = find_edge()
    os.makedirs(SHOTS, exist_ok=True)

    # form: local copy auto-advanced to the sign-off screen
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        html = f.read()
    fd, form_path = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html.replace("</body>", AUTO_FORM + "</body>"))
    try:
        shot(edge, LIVE, "login.png", 430, 920)
        shot(edge, "file:///" + form_path.replace("\\", "/"), "form.png", 430, 1100)
        shot(edge, LIVE + "dashboard.html", "dashboard.png", 1300, 1760)
    finally:
        os.remove(form_path)


if __name__ == "__main__":
    main()
