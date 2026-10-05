/**
 * zalo_client.js — Zalo Official Account (OA) reference client
 *
 * Platform-neutral: no storage, logging or web-server code. The host app
 * supplies those (see "Zalo OA Integration Reference", section
 * "Host responsibilities checklist").
 *
 * Runtime requirements:
 *   - global fetch            (Node 18+, Deno, Bun, browsers, Workers)
 *   - global Web Crypto       (Node 19+, Deno, Bun, browsers, Workers)
 *     only needed by verifyWebhookSignature() and buildAuthorizationRequest()
 *
 * Contents:
 *   1. Constants          endpoints and Zalo error codes
 *   2. createZaloClient   initial authorization, token refresh,
 *                         send with retry-once
 *   3. Webhook helpers    verifyWebhookSignature, parseWebhookEvent
 */

// ---------------------------------------------------------------------------
// 1. Constants
// ---------------------------------------------------------------------------

export const ZALO_ENDPOINTS = {
  OA_PERMISSION: "https://oauth.zaloapp.com/v4/oa/permission",
  OA_TOKEN: "https://oauth.zaloapp.com/v4/oa/access_token",
  SEND_CS: "https://openapi.zalo.me/v3.0/oa/message/cs",
  SEND_GROUP: "https://openapi.zalo.me/v3.0/oa/group/message",
};

export const ZALO_ERRORS = {
  OK: 0,
  ACCESS_TOKEN_EXPIRED: -216,   // returned inside an HTTP 200 body
  OA_TIER_REQUIRED: -224,       // OA package does not include the feature
  REFRESH_TOKEN_INVALID: -14020 // refresh token already used or expired
};

export const ZALO_EVENTS = {
  CS_TEXT: "user_send_text",
  GROUP_TEXT: "user_send_group_text",
};

// Fallback when a refresh response has no expires_in (25 hours, as observed).
const DEFAULT_ACCESS_TOKEN_TTL_SEC = 90000;

// Refresh proactively when the stored token has less than this left.
const PROACTIVE_REFRESH_MARGIN_MS = 5 * 60 * 1000;

const NOOP_LOGGER = { info() {}, warn() {}, error() {} };

// ---------------------------------------------------------------------------
// 2. Client: token refresh + sending
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} ZaloTokens
 * @property {string} accessToken
 * @property {string} refreshToken
 * @property {number} [expiresAt]  Epoch milliseconds; optional.
 */

/**
 * @typedef {Object} TokenStore            HOST PROVIDES
 * @property {() => Promise<ZaloTokens|null>} get
 *   Return the currently stored tokens (or null if none).
 * @property {(tokens: ZaloTokens) => Promise<void>} save
 *   Persist all fields together in ONE operation. Must complete before
 *   resolving: the old refresh token is already dead at this point.
 */

/**
 * @typedef {Object} SendResult
 * @property {boolean} ok        true only for HTTP 200 with error === 0
 * @property {number}  [status]  HTTP status, when a response was received
 * @property {Object}  [data]    Parsed JSON body, when parseable
 * @property {string}  [error]   Short reason when ok is false
 */

/**
 * Create a Zalo OA client.
 *
 * @param {Object} config
 * @param {string} config.appId          Zalo app ID.
 * @param {string} config.appSecretKey   App secret key (refresh header).
 *                                       NOT the OA secret key.
 * @param {TokenStore} config.tokenStore Host token persistence.
 * @param {(fn: () => Promise<any>) => Promise<any>} [config.withRefreshLock]
 *   HOST PROVIDES. Runs fn while holding an exclusive lock so that only one
 *   refresh runs at a time across all processes. The default runs fn with
 *   NO lock, which is only safe for a single-process host.
 * @param {{info:Function, warn:Function, error:Function}} [config.logger]
 *   Optional. Never receives tokens or secrets.
 * @param {typeof fetch} [config.fetchImpl]  Optional fetch override (tests).
 */
export function createZaloClient({
  appId,
  appSecretKey,
  tokenStore,
  withRefreshLock = (fn) => fn(),
  logger = NOOP_LOGGER,
  fetchImpl = globalThis.fetch,
}) {
  if (!appId || !appSecretKey) throw new Error("appId and appSecretKey are required");
  if (!tokenStore?.get || !tokenStore?.save) throw new Error("tokenStore.get and tokenStore.save are required");
  if (typeof fetchImpl !== "function") throw new Error("No fetch implementation available");

  /**
   * POST to the OA token endpoint (shared by the code exchange and refresh).
   * @param {Object} fields  Form fields besides app_id.
   * @param {string} context "authorize" or "refresh", for log lines.
   * @returns {Promise<ZaloTokens|null>} New tokens (not yet saved), or null.
   */
  async function requestTokens(fields, context) {
    let status, text, data;
    try {
      const res = await fetchImpl(ZALO_ENDPOINTS.OA_TOKEN, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          secret_key: String(appSecretKey),
        },
        body: new URLSearchParams({ app_id: String(appId), ...fields }).toString(),
      });
      status = res.status;
      text = await res.text();
      data = safeJsonParse(text);
    } catch (err) {
      logger.error(`[zalo] ${context}: network error: ${err?.message || err}`);
      return null;
    }

    // Zalo may return HTTP 200 with an error in the body.
    const bodyError = data && (data.error || data.error_name);
    if (status !== 200 || !data || bodyError || !data.access_token || !data.refresh_token) {
      const reason = data?.error_description || data?.error_name || data?.message || data?.error;
      logger.error(`[zalo] ${context} failed: HTTP ${status}${reason !== undefined ? `, ${reason}` : ""}`);
      if (data?.error === ZALO_ERRORS.REFRESH_TOKEN_INVALID) {
        logger.error("[zalo] refresh token already used or expired; check token storage or re-authorize");
      }
      return null;
    }

    const expiresInSec = Number(data.expires_in) || DEFAULT_ACCESS_TOKEN_TTL_SEC;
    return {
      accessToken: String(data.access_token),
      refreshToken: String(data.refresh_token),
      expiresAt: Date.now() + expiresInSec * 1000,
    };
  }

  /**
   * Step 1 of the one-time OA authorization (bootstrap or recovery).
   * Builds the link an OA admin opens to grant the app permission.
   *
   * HOST MUST keep codeVerifier and state (e.g. keyed by state) until the
   * callback arrives; the callback handler needs both.
   *
   * @param {string} redirectUri  Must equal the "Official Account Callback
   *                              URL" registered in the Zalo console.
   * @returns {Promise<{url: string, codeVerifier: string, state: string}>}
   */
  async function buildAuthorizationRequest(redirectUri) {
    const codeVerifier = randomUrlSafe(32);
    const state = randomUrlSafe(16);
    const codeChallenge = base64Url(await sha256Bytes(codeVerifier));
    const url =
      `${ZALO_ENDPOINTS.OA_PERMISSION}?` +
      new URLSearchParams({
        app_id: String(appId),
        redirect_uri: redirectUri,
        code_challenge: codeChallenge,
        state,
      }).toString();
    return { url, codeVerifier, state };
  }

  /**
   * Step 2 of the one-time OA authorization. Call from the callback route
   * with the "code" query parameter (after checking "state" matches) and
   * the codeVerifier kept from step 1. Saves the first token pair.
   *
   * @param {string} code
   * @param {string} codeVerifier
   * @returns {Promise<boolean>} true when tokens were obtained and saved.
   */
  async function exchangeAuthorizationCode(code, codeVerifier) {
    if (!code || !codeVerifier) {
      logger.error("[zalo] authorize: code and codeVerifier are required");
      return false;
    }
    return withRefreshLock(async () => {
      const tokens = await requestTokens(
        { code: String(code), code_verifier: String(codeVerifier), grant_type: "authorization_code" },
        "authorize"
      );
      if (!tokens) return false;
      await tokenStore.save(tokens);
      logger.info("[zalo] OA authorized; first token pair saved");
      return true;
    });
  }

  /**
   * Exchange the stored refresh token for a new token pair and save it.
   *
   * @param {string|null} staleAccessToken  The token the caller saw fail
   *   (or was about to use). If the store already holds a different access
   *   token once the lock is acquired, another process refreshed first and
   *   that token is returned without refreshing again.
   * @returns {Promise<string|null>} A usable access token, or null.
   */
  async function refreshAccessToken(staleAccessToken = null) {
    return withRefreshLock(async () => {
      const stored = await tokenStore.get();

      // Someone else refreshed while we waited for the lock.
      if (stored?.accessToken && stored.accessToken !== staleAccessToken && !isExpiringSoon(stored)) {
        return stored.accessToken;
      }

      if (!stored?.refreshToken) {
        logger.error("[zalo] refresh: no refresh token stored; re-authorize the OA");
        return null;
      }

      const tokens = await requestTokens(
        { refresh_token: stored.refreshToken, grant_type: "refresh_token" },
        "refresh"
      );
      if (!tokens) return null;

      // CRITICAL: the old refresh token is dead now. Save before returning.
      await tokenStore.save(tokens);
      logger.info("[zalo] access token refreshed");
      return tokens.accessToken;
    });
  }

  /**
   * POST a JSON body to a Zalo OpenAPI endpoint. On an expired-token signal
   * (HTTP 401, or HTTP 200 with error -216) it refreshes once and retries once.
   *
   * @param {string} url
   * @param {Object} body
   * @param {string} [context]  Label for log lines, e.g. "CS" or "GROUP".
   * @returns {Promise<SendResult>}
   */
  async function postWithTokenRefresh(url, body, context = "API") {
    const stored = await tokenStore.get();
    let accessToken = stored?.accessToken || null;

    // Proactive refresh when we know the token is about to expire.
    if (!accessToken || isExpiringSoon(stored)) {
      accessToken = await refreshAccessToken(accessToken);
    }
    if (!accessToken) {
      logger.error(`[zalo] ${context}: no valid access token`);
      return { ok: false, error: "no_access_token" };
    }

    for (let attempt = 1; attempt <= 2; attempt++) {
      let status, text, data;
      try {
        const res = await fetchImpl(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            access_token: accessToken,
          },
          body: JSON.stringify(body),
        });
        status = res.status;
        text = await res.text();
        data = safeJsonParse(text);
      } catch (err) {
        logger.error(`[zalo] ${context}: network error: ${err?.message || err}`);
        return { ok: false, error: "network_error" };
      }

      if (!data) {
        logger.warn(`[zalo] ${context}: response is not JSON (HTTP ${status})`);
      }

      const tokenExpired =
        status === 401 ||
        (status === 200 && data?.error === ZALO_ERRORS.ACCESS_TOKEN_EXPIRED);

      if (tokenExpired && attempt === 1) {
        const newToken = await refreshAccessToken(accessToken);
        if (!newToken) {
          return { ok: false, status, data, error: "refresh_failed" };
        }
        accessToken = newToken;
        continue; // retry once
      }

      if (status === 200 && data?.error === ZALO_ERRORS.OK) {
        return { ok: true, status, data };
      }

      const reason = data?.message ?? (data ? JSON.stringify(data) : text);
      logger.error(`[zalo] ${context}: failed, HTTP ${status}, error ${data?.error}: ${reason}`);
      return {
        ok: false,
        status,
        data,
        error: tokenExpired ? "token_expired_after_refresh" : "api_error",
      };
    }

    return { ok: false, error: "unreachable" };
  }

  /**
   * Send a text message to a user in a 1:1 (CS) chat.
   * @param {string} userId  sender.id from a user_send_text event.
   * @param {string} text
   * @returns {Promise<SendResult>}
   */
  function sendCSMessage(userId, text) {
    return postWithTokenRefresh(
      ZALO_ENDPOINTS.SEND_CS,
      { recipient: { user_id: String(userId) }, message: { text: String(text) } },
      "CS"
    );
  }

  /**
   * Send a text message from the OA into a group chat (GMF).
   * @param {string} groupId  recipient.id from a user_send_group_text event.
   * @param {string} text
   * @returns {Promise<SendResult>}
   */
  function sendGMFMessage(groupId, text) {
    return postWithTokenRefresh(
      ZALO_ENDPOINTS.SEND_GROUP,
      { recipient: { group_id: String(groupId) }, message: { text: String(text) } },
      "GROUP"
    );
  }

  return {
    sendCSMessage,
    sendGMFMessage,
    postWithTokenRefresh,
    refreshAccessToken,
    buildAuthorizationRequest,
    exchangeAuthorizationCode,
  };
}

// ---------------------------------------------------------------------------
// 3. Webhook helpers (stateless)
// ---------------------------------------------------------------------------

/**
 * Verify the X-ZEvent-Signature header of a webhook request.
 * Signature = SHA-256 hex of (app_id + rawBody + timestamp + OA secret key),
 * where timestamp is the "timestamp" field of the body.
 *
 * Test against a real event before rejecting on failure: developers on the
 * Zalo forum report mismatches, most often from hashing re-serialized JSON
 * instead of the raw body.
 *
 * @param {Object} params
 * @param {string} params.rawBody          Request body exactly as received.
 * @param {string} params.signatureHeader  Value of X-ZEvent-Signature.
 * @param {string} params.oaSecretKey      OA secret key (NOT the app secret).
 * @param {string} [params.appId]          Defaults to app_id in the body.
 * @returns {Promise<boolean>}
 */
export async function verifyWebhookSignature({ rawBody, signatureHeader, oaSecretKey, appId }) {
  if (!rawBody || !signatureHeader || !oaSecretKey) return false;

  const body = safeJsonParse(rawBody);
  if (!body || body.timestamp === undefined) return false;

  const id = appId ?? body.app_id;
  if (!id) return false;

  const expected = await sha256Hex(`${id}${rawBody}${body.timestamp}${oaSecretKey}`);
  const received = String(signatureHeader).trim().replace(/^mac\s*=\s*/i, "").toLowerCase();
  return timingSafeEqual(expected, received);
}

/**
 * Normalize a webhook body into a small event object for the host to route.
 * Does not deduplicate: the host checks event.msgId against its own store.
 *
 * @param {string|Object} rawBodyOrPayload  Raw JSON string or parsed object.
 * @returns {{
 *   type: "cs"|"group"|"other",
 *   eventName: string,
 *   msgId: string|null,
 *   text: string|null,
 *   senderId: string|null,
 *   replyToId: string|null,   // user ID for "cs", group ID for "group"
 *   timestamp: Date|null,
 *   appId: string|null,
 *   oaId: string|null,
 *   raw: Object
 * } | null}  null when the body is not valid JSON or has no event_name.
 */
export function parseWebhookEvent(rawBodyOrPayload) {
  const payload =
    typeof rawBodyOrPayload === "string" ? safeJsonParse(rawBodyOrPayload) : rawBodyOrPayload;
  if (!payload || typeof payload !== "object" || !payload.event_name) return null;

  const eventName = payload.event_name;
  const type =
    eventName === ZALO_EVENTS.CS_TEXT ? "cs" :
    eventName === ZALO_EVENTS.GROUP_TEXT ? "group" :
    "other";

  const senderId = payload.sender?.id ?? null;
  const recipientId = payload.recipient?.id ?? null;
  const ts = payload.timestamp !== undefined ? new Date(Number(payload.timestamp)) : null;

  return {
    type,
    eventName,
    msgId: payload.message?.msg_id ?? null,
    text: typeof payload.message?.text === "string" ? payload.message.text.trim() : null,
    senderId,
    replyToId: type === "cs" ? senderId : type === "group" ? recipientId : null,
    timestamp: ts && !isNaN(ts.getTime()) ? ts : null,
    appId: payload.app_id ?? null,
    oaId: payload.oa_id ?? null,
    raw: payload,
  };
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function isExpiringSoon(tokens) {
  if (!tokens?.expiresAt) return false; // unknown expiry: rely on reactive refresh
  return Date.now() >= Number(tokens.expiresAt) - PROACTIVE_REFRESH_MARGIN_MS;
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function webCrypto() {
  const c = globalThis.crypto;
  if (!c?.subtle || !c?.getRandomValues) throw new Error("Web Crypto is not available in this runtime");
  return c;
}

async function sha256Bytes(input) {
  const digest = await webCrypto().subtle.digest("SHA-256", new TextEncoder().encode(input));
  return new Uint8Array(digest);
}

async function sha256Hex(input) {
  return Array.from(await sha256Bytes(input), (b) => b.toString(16).padStart(2, "0")).join("");
}

// Base64url without padding (RFC 7636 code_challenge format).
function base64Url(bytes) {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function randomUrlSafe(byteLength) {
  return base64Url(webCrypto().getRandomValues(new Uint8Array(byteLength)));
}

function timingSafeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/* ---------------------------------------------------------------------------
 * USAGE SKETCH (host side; replace the in-memory parts with real storage)
 * ---------------------------------------------------------------------------
 *
 * import { createZaloClient, parseWebhookEvent, verifyWebhookSignature } from "./zalo_client.js";
 *
 * // Secrets come from the host's secret storage, e.g. environment variables.
 * const zalo = createZaloClient({
 *   appId: process.env.ZALO_APP_ID,
 *   appSecretKey: process.env.ZALO_APP_SECRET_KEY,
 *   tokenStore: {
 *     async get() { return db.loadZaloTokens(); },          // host
 *     async save(tokens) { await db.saveZaloTokens(tokens); } // host, one write
 *   },
 *   withRefreshLock: (fn) => db.withLock("zalo_refresh", fn), // host
 *   logger: console,
 * });
 *
 * // One-time authorization (bootstrap, or recovery if the refresh token is lost)
 * //   GET /zalo/authorize  -> const { url, codeVerifier, state } =
 * //                             await zalo.buildAuthorizationRequest(CALLBACK_URL);
 * //                           pending.save(state, codeVerifier);  // host
 * //                           redirect(url);                       // OA admin approves
 * //   GET /zalo/callback?code=...&state=...
 * //                        -> const verifier = pending.take(state); // host; reject if missing
 * //                           const ok = await zalo.exchangeAuthorizationCode(code, verifier);
 *
 * // Sending
 * const result = await zalo.sendGMFMessage(groupId, "Machine 86 accepted");
 * if (!result.ok) { ... }
 *
 * // Receiving (inside the host's HTTP handler)
 * const valid = await verifyWebhookSignature({
 *   rawBody, signatureHeader: req.headers["x-zevent-signature"],
 *   oaSecretKey: process.env.ZALO_OA_SECRET_KEY,
 * });
 * if (!valid) return respond(401);
 * const event = parseWebhookEvent(rawBody);
 * respond(200);                                   // answer fast
 * if (!event?.msgId || await dedupe.seen(event.msgId)) return; // host
 * if (event.type === "cs")    handleCS(event);    // host business logic
 * if (event.type === "group") handleGroup(event); // host business logic
 */
