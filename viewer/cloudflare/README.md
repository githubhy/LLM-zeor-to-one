# Cloud deployment (Cloudflare Pages + Functions + KV)

These steps deploy the gated, writable cloud viewer. They require a Cloudflare
account and are **not** automated.

## One-time provisioning

1. Create the KV namespace and copy its id into `wrangler.toml`:
   `npx wrangler kv namespace create ANNOTATIONS`
   → paste the printed `id` over `REPLACE_WITH_KV_NAMESPACE_ID`.
2. Generate a 256-bit access token: `openssl rand -hex 32`.
3. Store it as a Pages secret (never commit it):
   `npx wrangler pages secret put VIEWER_TOKEN` (paste the token when prompted).

## Publish + deploy

4. Build the static bundle (emits `dist/` at the **repo root**; default target
   is the whole `surveys/` tree):
   `npm run publish -- --target <survey-dir>`

   **Multi-root subset deploy** (decision 2026-06-14-04 — the live build): pass
   repeatable `--target <path>:<Label>` to publish several roots namespaced:
   `node viewer/publish.js --target surveys:Surveys --target wikis:Wikis --target theories:Theories`
   (a single `--target` keeps the legacy flat, byte-identical surveys-only bundle).
5. Stage the deploy layout, then deploy from the staging root. Two wrangler
   behaviors dictate the shape (verified on the first real deploy, 2026-06-10):
   `wrangler pages deploy` applies the KV binding only from a `wrangler.toml`
   found at the **cwd**, and it compiles Functions from `./functions` at the
   cwd (not from inside the output dir) — so the adapters'
   `../../../lib/cloud-api.js` imports must also resolve at the staging root:

   ```
   stage/
     wrangler.toml   # copy of viewer/cloudflare/wrangler.toml (real KV id)
     functions/      # copy of dist/functions
     lib/            # copy of dist/lib  (adapter imports resolve here)
     dist/           # the published bundle (= pages_build_output_dir)
   ```

   ```bash
   STAGE=$(mktemp -d)
   cp viewer/cloudflare/wrangler.toml "$STAGE"/
   cp -R dist "$STAGE"/dist
   cp -R dist/functions "$STAGE"/functions
   cp -R dist/lib "$STAGE"/lib
   (cd "$STAGE" && npx --prefix <repo>/viewer wrangler pages deploy --branch main)
   ```

   Deploying from the repo root (`wrangler pages deploy dist`) uploads the
   assets but finds no `wrangler.toml` → the KV binding is never applied and
   every annotation API call fails at runtime. Deploying from inside `dist/`
   trips on `pages_build_output_dir = "dist"` resolving to `dist/dist`.
6. Verify the gate before sharing the URL: bare URL → `404`; `?k=<token>` →
   `200` with `Set-Cookie: vt=` **and** `Cache-Control: no-store`;
   `Authorization: Bearer <token>` on `/api/annotations-manifest` → `200`.

### Local preview (optional)

To smoke-test the gated/writable build locally before deploying, run
`wrangler pages dev` **from inside `dist/`** (cwd, not the positional arg, is the
Functions root for `pages dev`), supplying the token binding and a local KV:

```
cd dist && npx wrangler pages dev . \
  --binding VIEWER_TOKEN=<token> --kv ANNOTATIONS --compatibility-date 2025-01-01
```

Then open `http://127.0.0.1:8788/?k=<token>`. (`tests/cloud-integration.test.js`
automates exactly this round-trip.)

## Access

- First-load URL (sets the session cookie + stashes the token, then the `?k` is
  stripped from the URL client-side): `https://<project>.pages.dev/?k=<token>`
- Anyone without the token gets a generic `404`.
- **Rotation:** regenerate the token (steps 2–3) and re-mint the `?k=` URL.

## Auth model: cookie cold-start vs bearer header

The gate accepts three credentials, in `handleGate` precedence order:
`Authorization: Bearer <token>` header → `vt=` session cookie → `?k=<token>`
query bootstrap. They split cleanly by *who* makes the request (decision
`2026-06-09-07`):

- **Cold-start (cookie).** The first navigation, the first-paint `<script>` /
  `<link>` / font subresources, and the survey `content/*.md` files are all issued
  by the browser **before** the service worker (SW) has installed and activated —
  no application JS has run, so nothing can attach an `Authorization` header. The
  HttpOnly `vt=` cookie set on the `?k=` bootstrap is the *only* mechanism that can
  gate those requests. It is infrastructure, not application-layer auth.
- **Steady-state (bearer header).** Once the page and SW are live, all
  application-layer auth — `viewer.js` `fetch()`/`XHR`, annotation API
  reads/writes, and SW-forwarded fetches — uses the `Authorization: Bearer` header.
  The cookie still rides along automatically (it stays the authoritative credential
  for any non-app browser request), but the header is the semantically primary path
  and the forward-compat seam for a future WKWebView native shell that injects the
  token from the Keychain.

### `Cache-Control: no-store` on the cookie-setting response (required)

The gate response that emits `Set-Cookie` (only the `?k=` bootstrap path does)
**must** carry `Cache-Control: no-store`, so neither Cloudflare's edge nor any
intermediate proxy caches a per-user cookie and re-serves it to another visitor.
This is set in `functions/_middleware.js` on the same `Response` that appends the
`Set-Cookie` header, and is covered by a unit assertion in
`viewer/tests/unit/cloud-api.test.js` ("cookie-setting gate path yields Set-Cookie
AND Cache-Control: no-store"). If you refactor the middleware's cookie branch, keep
the `no-store` header on whatever `Response` carries the `Set-Cookie`.

### Token-rotation recovery path

After rotating the token (steps 2–3 above) the old `vt=` cookie and any stashed
client token no longer match `VIEWER_TOKEN`, so the gate 404s every request — the
device looks "locked out". Recovery: open the freshly re-minted `?k=<new-token>`
URL once on the device. The bootstrap path overwrites the `vt=` cookie with the new
token and re-stashes it client-side, restoring access. No cache purge is needed
because the cookie-setting response is `no-store` (above); the stale cookie was
never edge-cached.

### Service-worker token flow (postMessage → IndexedDB)

The SW cannot read the HttpOnly `vt=` cookie, and cookies are not guaranteed to
persist for an iOS standalone PWA across launches. So the page hands the token to
the SW explicitly: on load the client reads the token from `localStorage`,
`postMessage`s it to the SW, and the SW persists it in IndexedDB. SW-forwarded
fetches then inject `Authorization: Bearer <token>` from IndexedDB. The cookie
remains authoritative for ordinary online browser requests; the IndexedDB copy is
what makes SW-mediated and offline-capable requests carry the bearer header. If iOS
clears the cookie between launches, the `localStorage → postMessage → IndexedDB`
re-supply on each launch self-heals it.

## Seed / sync annotations (run from the repo, not Cloudflare)

- Seed the cloud from your local git highlights (run after deploy / after desktop edits):
  `VIEWER_TOKEN=<token> npm run push-annotations -- --base https://<project>.pages.dev --target <survey-dir>`
- Pull phone edits back into the git-canonical sidecars:
  `VIEWER_TOKEN=<token> npm run pull-annotations -- --base https://<project>.pages.dev --target <survey-dir>`
