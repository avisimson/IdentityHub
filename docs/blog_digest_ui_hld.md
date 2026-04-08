# Blog Digest UI — High-Level Design

> **Goal:** Expose the Blog Digest feature in the IdentityHub frontend so authenticated users can (1) manually trigger a digest run and (2) view & update the scheduled job's cron time — all without restarting the backend.

---

## 1. Current State

| Layer | What exists today |
|-------|-------------------|
| **Backend** | `BlogDigestService.run_digest(db)` — full scrape → LLM → Jira pipeline. `scheduler.py` starts an APScheduler `CronTrigger(hour=9, minute=0)` job at app startup. No HTTP endpoints to trigger or reconfigure. |
| **Frontend** | No blog digest page or route. The `Ticket.source` type already includes `"blog_digest"`. `TicketCard` shows a "via Blog Digest" badge. |

---

## 2. New Backend API Endpoints

A new router: `backend/app/blog_digest/router.py`, prefix `/blog-digest`, tag `Blog Digest`.

All endpoints require Bearer auth (`get_current_user` dependency).

### 2.1 `POST /blog-digest/trigger`

Manually triggers a one-shot blog digest run for the current user.

| Field | Detail |
|-------|--------|
| **Auth** | Bearer (current user) |
| **Request body** | None |
| **Behavior** | Calls `BlogDigestService.run_digest(db)` inline (awaited). Uses the current authenticated user's Jira connection rather than `BLOG_DIGEST_USER_EMAIL`, so any connected user can trigger a digest. If no Jira connection exists, returns 403. |
| **Success response** | `200 { "detail": "Blog digest completed", "ticket_key": "SEC-42" }` |
| **Error responses** | `403 JIRA_NOT_CONNECTED` — user has no Jira connection. `502 JIRA_API_ERROR` — Jira API call failed. `500 BLOG_DIGEST_FAILED` — scrape or LLM failure. |

**Service change:** Add an optional `user_id` override parameter to `BlogDigestService.run_digest()` so it can run on behalf of the calling user instead of the env-configured system user.

### 2.2 `GET /blog-digest/schedule`

Returns the current cron schedule configuration.

| Field | Detail |
|-------|--------|
| **Auth** | Bearer |
| **Response** | `200 { "hour": 9, "minute": 0, "timezone": "UTC", "enabled": true }` |

Reads live values from the APScheduler job registered under id `"blog_digest"`.

### 2.3 `PUT /blog-digest/schedule`

Updates the scheduled cron time at runtime (no restart needed).

| Field | Detail |
|-------|--------|
| **Auth** | Bearer |
| **Request body** | `{ "hour": 14, "minute": 30, "timezone": "UTC", "enabled": true }` |
| **Validation** | `hour` 0-23, `minute` 0-59, `timezone` must be a valid IANA tz string, `enabled` boolean. |
| **Behavior** | Calls `scheduler.reschedule_job("blog_digest", trigger=CronTrigger(...))`. If `enabled=false`, pauses the job via `scheduler.pause_job(...)`. If `enabled=true` and currently paused, resumes via `scheduler.resume_job(...)`. |
| **Response** | `200 { "detail": "Schedule updated", "hour": 14, "minute": 30, "timezone": "UTC", "enabled": true }` |

### 2.4 Pydantic Schemas

New file: `backend/app/blog_digest/schemas.py`

```python
class BlogDigestTriggerResponse(BaseModel):
    detail: str
    ticket_key: str | None = None

class ScheduleResponse(BaseModel):
    hour: int
    minute: int
    timezone: str
    enabled: bool

class ScheduleUpdateRequest(BaseModel):
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    timezone: str = "UTC"
    enabled: bool = True
```

### 2.5 Scheduler Module Changes

Add helper functions to `backend/app/blog_digest/scheduler.py`:

```python
def get_schedule() -> dict:
    """Return the current cron trigger config from the live scheduler."""

def update_schedule(hour: int, minute: int, timezone: str, enabled: bool) -> None:
    """Reschedule / pause / resume the blog_digest job."""
```

### 2.6 Service Module Changes

Modify `BlogDigestService.run_digest()` signature:

```python
async def run_digest(db: AsyncSession, *, user_id: str | None = None) -> str | None:
```

- When `user_id` is provided, use that user's Jira connection instead of looking up `BLOG_DIGEST_USER_EMAIL`.
- Return the created `jira_ticket_key` (or `None` on failure) so the router can include it in the response.

### 2.7 Wire the Router

In `backend/app/main.py`:

```python
from app.blog_digest.router import router as blog_digest_router
app.include_router(blog_digest_router)
```

---

## 3. New Frontend Components

### 3.1 Route & Navigation

| Item | Detail |
|------|--------|
| **Route** | `/settings/blog-digest` (inside the `ProtectedRoute > AppShell` layout) |
| **Page** | `frontend/src/pages/BlogDigestPage.tsx` |
| **Nav item** | Add to `navItems` in `AppShell.tsx` under the "Settings" section, using the `Newspaper` icon from Lucide, label "Blog Digest" |

### 3.2 Page Layout — `BlogDigestPage`

The page has two cards stacked vertically inside a `max-w-2xl` container (matching `JiraSettingsPage` style):

```
┌───────────────────────────────────────────┐
│  Blog Digest Settings                      │
│  Manage automated NHI blog digests         │
│                                            │
│  ┌─────────────────────────────────────┐   │
│  │  Manual Trigger                      │   │
│  │                                      │   │
│  │  Scrape the latest Oasis Security    │   │
│  │  blog post, generate an AI summary,  │   │
│  │  and create a Jira ticket.           │   │
│  │                                      │   │
│  │         [ Run Now ]  (button)        │   │
│  │                                      │   │
│  │  ✓ Ticket created: SEC-42 (success)  │   │
│  └─────────────────────────────────────┘   │
│                                            │
│  ┌─────────────────────────────────────┐   │
│  │  Schedule                            │   │
│  │                                      │   │
│  │  Enable scheduled digest  [ toggle ] │   │
│  │                                      │   │
│  │  Time    [ 09 ] : [ 00 ]  UTC       │   │
│  │  Timezone  [ UTC ▼ ]                │   │
│  │                                      │   │
│  │         [ Save Schedule ]            │   │
│  └─────────────────────────────────────┘   │
└───────────────────────────────────────────┘
```

### 3.3 API Module

New file: `frontend/src/api/blogDigestApi.ts`

```typescript
export async function triggerDigest(): Promise<{ detail: string; ticket_key: string | null }>
export async function getSchedule(): Promise<ScheduleResponse>
export async function updateSchedule(payload: ScheduleUpdateRequest): Promise<ScheduleResponse>
```

### 3.4 TypeScript Types

Add to `frontend/src/types/index.ts`:

```typescript
export interface BlogDigestSchedule {
  hour: number;
  minute: number;
  timezone: string;
  enabled: boolean;
}

export interface BlogDigestTriggerResult {
  detail: string;
  ticket_key: string | null;
}
```

### 3.5 React Query Hooks

New file: `frontend/src/features/blog-digest/hooks/useBlogDigest.ts`

| Hook | Type | API call |
|------|------|----------|
| `useBlogDigestSchedule()` | `useQuery` | `GET /blog-digest/schedule` |
| `useUpdateSchedule()` | `useMutation` | `PUT /blog-digest/schedule` → invalidates schedule query |
| `useTriggerDigest()` | `useMutation` | `POST /blog-digest/trigger` → shows success/error toast |

### 3.6 Feature Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `ManualTriggerCard` | `frontend/src/features/blog-digest/components/ManualTriggerCard.tsx` | "Run Now" button with loading state + success/error feedback |
| `ScheduleCard` | `frontend/src/features/blog-digest/components/ScheduleCard.tsx` | Form with hour/minute selects, timezone dropdown, enable toggle, save button |

---

## 4. Files to Create

| # | File | Type |
|---|------|------|
| 1 | `backend/app/blog_digest/router.py` | New |
| 2 | `backend/app/blog_digest/schemas.py` | New |
| 3 | `frontend/src/pages/BlogDigestPage.tsx` | New |
| 4 | `frontend/src/api/blogDigestApi.ts` | New |
| 5 | `frontend/src/features/blog-digest/hooks/useBlogDigest.ts` | New |
| 6 | `frontend/src/features/blog-digest/components/ManualTriggerCard.tsx` | New |
| 7 | `frontend/src/features/blog-digest/components/ScheduleCard.tsx` | New |

## 5. Files to Modify

| # | File | Change |
|---|------|--------|
| 1 | `backend/app/main.py` | Import & register `blog_digest_router` |
| 2 | `backend/app/blog_digest/scheduler.py` | Add `get_schedule()` and `update_schedule()` helpers |
| 3 | `backend/app/blog_digest/service.py` | Accept optional `user_id` param; return ticket key |
| 4 | `frontend/src/App.tsx` | Add `/settings/blog-digest` route |
| 5 | `frontend/src/layouts/AppShell.tsx` | Add "Blog Digest" nav item to `navItems` array |
| 6 | `frontend/src/types/index.ts` | Add `BlogDigestSchedule` and `BlogDigestTriggerResult` types |

---

## 6. UX Details

| Aspect | Behavior |
|--------|----------|
| **Run Now loading** | Button shows spinner + "Running…" text. Disabled while in-flight. |
| **Run Now success** | Toast: "Blog digest ticket created: {ticket_key}". Inline success message in card. |
| **Run Now error (no Jira)** | Toast: "Jira not connected — connect Jira first". Link to `/settings/jira`. |
| **Schedule save** | Toast: "Schedule updated". Optimistic update on the form. |
| **Schedule toggle off** | Hour/minute/timezone fields become disabled (greyed out). Job is paused. |
| **Timezone dropdown** | Common timezones: UTC, US/Eastern, US/Pacific, Europe/London, Europe/Berlin, Asia/Jerusalem, Asia/Tokyo. |

---

## 7. Dependency Order

```
1. Backend schemas (schemas.py)
2. Backend scheduler helpers (scheduler.py changes)
3. Backend service changes (service.py)
4. Backend router (router.py) + wire in main.py
5. Frontend types (types/index.ts)
6. Frontend API module (blogDigestApi.ts)
7. Frontend hooks (useBlogDigest.ts)
8. Frontend components (ManualTriggerCard, ScheduleCard)
9. Frontend page (BlogDigestPage.tsx)
10. Frontend routing + navigation (App.tsx, AppShell.tsx)
```
