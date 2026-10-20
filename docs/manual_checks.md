# Manual checks (not automated)

## M-01 Error page layout and keyboard use

No browser was available when Foundation was built, so these were **not executed by the developer**. Please check them.

1. Run `flask --app wsgi.py run --debug` and open `http://127.0.0.1:5000/does-not-exist`.
2. At widths 320 px, 768 px and 1280 px: no horizontal scrolling, text readable, the error card is not clipped.
3. Press Tab once: the "Skip to main content" link appears with a visible outline. Press Enter: focus moves to the main content.
4. Zoom to 200 percent: layout still usable.
5. Confirm the page looks acceptable with the provisional palette (decision P-09 is still open).
6. In the browser developer tools, enable "prefers-reduced-motion: reduce" and confirm nothing animates (there are no animations yet).

## Checks that automated tests cannot replace

These remain manual for every phase that touches pages. System tests (Flask test client, decision D-30) cover server behaviour, not the browser.

- Real layout at 320, 768 and 1280 px: wrapping, overflow, clipping.
- Focus outline appearance and tab order using only the keyboard.
- Browser console: no Content-Security-Policy violations on each page.
- Cookie behaviour over real HTTPS, in at least two browsers.
- Screen reader reading order, landmarks and form labels.
- Touch targets on a real phone.
- Printed output, where a page is meant to be printed.
- Real email rendering for any message the system sends.

None of the above has been executed by the developer so far.
