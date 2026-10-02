# Document sources

HTML sources for `Karbhari-Product-Document.pdf` and `Karbhari-Project-Guide.pdf` in the repo root.
Screenshots live in `guide-assets/`. To regenerate a PDF on Windows:

```bash
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --no-pdf-header-footer ^
  --print-to-pdf="Karbhari-Project-Guide.pdf" karbhari-project-guide.html
```

Any Chromium browser works the same way (`chrome --headless=new --print-to-pdf=...`).
