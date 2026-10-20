# JeSU Osaka website

Static website for the Osaka esports Union. Published production is served from
`main` through GitHub Pages at https://www.jesu-osaka.jp/.

The redesign is prepared on `design/jesu-refresh-20261020`; it has not been pushed
or deployed. A separate existing test repository is available at
`entry-package/jesu-osaka-test-site`. External preview publication requires the
president's approval of the prepared version; production follows a separate
confirmation of that preview.

## Build and verify

Run on pkg-home (Toyonaka Mac mini):

```sh
node --test test/*.cjs
python3 scripts/build.py --output ../release-production
python3 scripts/build.py --preview --output ../release-preview
python3 scripts/validate.py ../release-production
python3 scripts/validate.py ../release-preview --preview
python3 scripts/export-review.py ../release-preview ../offline-review
```

Output directories must be outside the checkout and empty. Release files are
selected explicitly; development reports, tests and source history are excluded.
Preview has no production CNAME, disallows indexing and blocks inquiry submission.
Production and preview retain identical page content, CSS, scripts and assets;
only indexing metadata, robots.txt and production CNAME differ. Do not change the
prepared page content between approved preview and production.

The six pages share navigation and styles. Date-dependent event labels stop
inviting registration when the published event end time passes. Review copies are
not an event management system and do not submit inquiries.

## Preserved inquiry integration

`contact-submit.js` is unchanged from the verified production baseline. The form
keeps the receiver, honeypot, timestamp, request ID, length limits, exact-origin
response allowlist and nonce handshake. A successful iframe load alone does not
mean accepted. The redesign does not modify the Apps Script receiver.

Live receipt, administrator email arrival and persistence require verification
after production deployment; local tests do not prove those outcomes.

## Sources and rollback

Published site, current repository and the public Peatix event 5230213 supplied
the content. Earlier event listings remain dated archives, without expired
application calls. Board member names, roles and comments are retained from the
published site. No new artwork or unverified claims about completed events were
introduced.

Baseline production commit: `35626f0`. Before publishing, compare the remote HEAD
and production files again; preserve any intervening changes. Return to the
baseline with a new revert commit if needed, never rewrite remote history.
