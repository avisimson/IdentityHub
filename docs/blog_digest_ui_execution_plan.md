# Blog Digest UI — Execution Plan

> **Generated from:** `docs/blog_digest_ui_hld.md`
>
> **Usage:** Check off tasks (`- [x]`) as they are completed. Each task includes a ready-to-copy **Agent Prompt** for Cursor.
>
> **Prerequisites:** All Phase 1–4 tasks from the master execution plan must be complete. The blog digest backend service (`backend/app/blog_digest/service.py`, `scheduler.py`) must already exist and work.

---

## Phase 1: Backend — Schemas, Service & Scheduler Changes

> **Goal:** Prepare the backend internals so the new router endpoints have everything they need.

---

### 1.1 — Blog Digest Pydantic Schemas

- [x] **Task 1.1: Create Pydantic request/response schemas for the Blog Digest API**

  **Target Files:**
  - `backend/app/blog_digest/schemas.py` (create)

  **Agent Prompt:**
  > Create the Pydantic schemas for the Blog Digest UI API. Refer to `docs/blog_digest_ui_hld.md` → Section 2.4 for the schema definitions.
  >
  > Create `backend/app/blog_digest/schemas.py` with three models:
  >
  > 1. `BlogDigestTriggerResponse(BaseModel)`:
  >    - `detail: str`
  >    - `ticket_key: str | None = None`
  >
  > 2. `ScheduleResponse(BaseModel)`:
  >    - `hour: int`
  >    - `minute: int`
  >    - `timezone: str`
  >    - `enabled: bool`
  >
  > 3. `ScheduleUpdateRequest(BaseModel)`:
  >    - `hour: int = Field(ge=0, le=23)`
  >    - `minute: int = Field(ge=0, le=59)`
  >    - `timezone: str = "UTC"` — must be a valid IANA timezone string. Add a Pydantic `field_validator` that checks `timezone` is valid using `zoneinfo.ZoneInfo(value)` and raises `ValueError` if invalid.
  >    - `enabled: bool = True`
  >
  > Import `BaseModel` and `Field` from `pydantic`.

  **Acceptance Criteria:**
  - All three schemas defined with correct types and defaults.
  - `ScheduleUpdateRequest.hour` is constrained 0–23, `minute` 0–59.
  - Invalid timezone strings are rejected by the validator.

---

### 1.2 — Scheduler Helper Functions

- [x] **Task 1.2: Add get_schedule() and update_schedule() helpers to the scheduler module**

  **Target Files:**
  - `backend/app/blog_digest/scheduler.py` (update)

  **Agent Prompt:**
  > Add two helper functions to the existing scheduler module so the new router can read and update the cron schedule at runtime. Refer to `docs/blog_digest_ui_hld.md` → Section 2.5 for the interface.
  >
  > Edit `backend/app/blog_digest/scheduler.py` and add the following functions (keep all existing code intact):
  >
  > 1. `get_schedule() -> dict`:
  >    - Get the job with id `"blog_digest"` from the `scheduler` instance using `scheduler.get_job("blog_digest")`.
  >    - If the job is None (scheduler not started yet or job removed), return a default: `{"hour": 9, "minute": 0, "timezone": "UTC", "enabled": False}`.
  >    - Extract `hour` and `minute` from `job.trigger.fields` — APScheduler `CronTrigger` stores fields as a list; `hour` is at index 5, `minute` is at index 4. Access `.expressions[0].first` on each field to get the int value.
  >    - Determine `timezone` from `str(job.trigger.timezone)`.
  >    - Determine `enabled` from `job.next_run_time is not None` (paused jobs have `next_run_time == None`).
  >    - Return `{"hour": hour, "minute": minute, "timezone": timezone, "enabled": enabled}`.
  >
  > 2. `update_schedule(hour: int, minute: int, timezone: str, enabled: bool) -> None`:
  >    - Import `CronTrigger` (already imported in the file).
  >    - Call `scheduler.reschedule_job("blog_digest", trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone))`.
  >    - If `enabled` is `False`, call `scheduler.pause_job("blog_digest")`.
  >    - If `enabled` is `True`, call `scheduler.resume_job("blog_digest")` to ensure the job is active.
  >    - Log the update: `logger.info("Blog digest schedule updated: %02d:%02d %s (enabled=%s)", hour, minute, timezone, enabled)`.

  **Acceptance Criteria:**
  - `get_schedule()` returns correct hour, minute, timezone, and enabled status from the live scheduler.
  - `get_schedule()` handles the case where the job doesn't exist (returns defaults).
  - `update_schedule()` reschedules the job and pauses/resumes based on `enabled`.
  - All existing code (`start_scheduler`, `stop_scheduler`, `_run_digest_job`) remains unchanged.

---

### 1.3 — Service Changes (User Override & Return Value)

- [x] **Task 1.3: Modify BlogDigestService.run_digest to accept a user_id override and return ticket key**

  **Target Files:**
  - `backend/app/blog_digest/service.py` (update)

  **Agent Prompt:**
  > Modify the existing `BlogDigestService.run_digest()` method to support manual triggers from the UI. Refer to `docs/blog_digest_ui_hld.md` → Section 2.6 for the required changes.
  >
  > Edit `backend/app/blog_digest/service.py` and make these changes to the `run_digest` method:
  >
  > 1. Change the signature from `async def run_digest(db: AsyncSession) -> None` to:
  >    ```python
  >    async def run_digest(db: AsyncSession, *, user_id: str | None = None) -> str | None:
  >    ```
  >    The return value is the created `jira_ticket_key` on success, or `None` on failure.
  >
  > 2. Update the user lookup logic inside `run_digest`:
  >    - If `user_id` is provided, look up the user by `User.id == uuid.UUID(user_id)` instead of by `User.email == settings.BLOG_DIGEST_USER_EMAIL`.
  >    - If `user_id` is `None`, keep the existing behavior of looking up by `settings.BLOG_DIGEST_USER_EMAIL`.
  >    - Add `import uuid` at the top of the file.
  >
  > 3. Change the `create_ticket` call to use `user_id=str(system_user.id)` in both paths (this is already the case for the email lookup path; just ensure the same pattern for the `user_id` override path).
  >
  > 4. After the ticket is created, return `ticket.jira_ticket_key` instead of just logging.
  >
  > 5. In the `except Exception` block, return `None` instead of just logging (keep the `logger.exception` call).
  >
  > 6. At the top where it checks `if not settings.BLOG_DIGEST_USER_EMAIL` and returns — only do this check when `user_id is None`. When `user_id` is provided, skip the email check entirely.
  >
  > **Important:** The existing scheduler integration calls `run_digest(db)` with no `user_id`, so the default path must remain identical in behavior. Only the new `user_id` path is additive.

  **Acceptance Criteria:**
  - `run_digest(db)` (no `user_id`) behaves identically to before — uses `BLOG_DIGEST_USER_EMAIL`.
  - `run_digest(db, user_id="...")` uses the provided user's Jira connection.
  - Returns the ticket key string on success, `None` on failure.
  - Existing scheduler integration is not broken.

---

## Phase 2: Backend — Router & Wiring

> **Goal:** Expose the three new HTTP endpoints and register them with the FastAPI app.

---

### 2.1 — Blog Digest Router

- [x] **Task 2.1: Create the Blog Digest router with trigger, get schedule, and update schedule endpoints**

  **Target Files:**
  - `backend/app/blog_digest/router.py` (create)

  **Agent Prompt:**
  > Create the Blog Digest API router. Refer to `docs/blog_digest_ui_hld.md` → Sections 2.1, 2.2, 2.3 for the endpoint contracts. Follow the same patterns used in `backend/app/jira/router.py` and `backend/app/api_keys/router.py`.
  >
  > Create `backend/app/blog_digest/router.py` with `APIRouter(prefix="/blog-digest", tags=["Blog Digest"])`:
  >
  > 1. **`POST /blog-digest/trigger`** → triggers a manual blog digest run for the authenticated user.
  >    - Dependencies: `get_current_user`, `get_db`.
  >    - Call `BlogDigestService.run_digest(db, user_id=str(current_user.id))`.
  >    - If the service returns a ticket key, return `200 BlogDigestTriggerResponse(detail="Blog digest completed", ticket_key=ticket_key)`.
  >    - If the service returns `None`, raise `HTTPException(500)` with detail `"Blog digest failed — check server logs"` and header `X-Error-Code: BLOG_DIGEST_FAILED`.
  >    - Catch `JiraNotConnectedError` (imported from `app.jira.service`) and raise `HTTPException(403)` with detail `"Jira not connected"` and header `X-Error-Code: JIRA_NOT_CONNECTED`.
  >    - Catch `JiraAPIError` (imported from `app.jira.service`) and raise `HTTPException(502)` with detail `f"Jira API error: {exc}"` and header `X-Error-Code: JIRA_API_ERROR`.
  >
  > 2. **`GET /blog-digest/schedule`** → returns the current schedule.
  >    - Dependencies: `get_current_user` (auth required, but no DB needed).
  >    - Call `get_schedule()` from `app.blog_digest.scheduler`.
  >    - Return `200 ScheduleResponse(**schedule_dict)`.
  >
  > 3. **`PUT /blog-digest/schedule`** → updates the cron schedule.
  >    - Dependencies: `get_current_user`.
  >    - Body: `ScheduleUpdateRequest`.
  >    - Call `update_schedule(body.hour, body.minute, body.timezone, body.enabled)` from `app.blog_digest.scheduler`.
  >    - Return `200 ScheduleResponse(hour=body.hour, minute=body.minute, timezone=body.timezone, enabled=body.enabled)`.
  >
  > Import the schemas from `app.blog_digest.schemas`, the service from `app.blog_digest.service`, and the scheduler helpers from `app.blog_digest.scheduler`.

  **Acceptance Criteria:**
  - All three endpoints require Bearer auth.
  - `POST /blog-digest/trigger` runs the full pipeline and returns the ticket key.
  - `GET /blog-digest/schedule` returns the live cron configuration.
  - `PUT /blog-digest/schedule` updates the schedule at runtime without restart.
  - Error responses use the standard `X-Error-Code` header pattern.

---

### 2.2 — Wire Router in main.py

- [x] **Task 2.2: Register the Blog Digest router in the FastAPI app**

  **Target Files:**
  - `backend/app/main.py` (update)

  **Agent Prompt:**
  > Register the Blog Digest router in the FastAPI application. Follow the same pattern used for the other routers.
  >
  > Edit `backend/app/main.py`:
  >
  > 1. Add an import at the top, alongside the other router imports:
  >    ```python
  >    from app.blog_digest.router import router as blog_digest_router
  >    ```
  >
  > 2. Add `app.include_router(blog_digest_router)` after the existing `app.include_router(external_router)` line.
  >
  > Do not change anything else.

  **Acceptance Criteria:**
  - The blog digest router is imported and included.
  - All existing routers remain registered.
  - The app starts without errors.

---

## Phase 3: Frontend — Types, API Module & Hooks

> **Goal:** Build the data layer for the frontend before creating any UI components.

---

### 3.1 — Frontend TypeScript Types

- [x] **Task 3.1: Add Blog Digest types to the shared types file**

  **Target Files:**
  - `frontend/src/types/index.ts` (update)

  **Agent Prompt:**
  > Add TypeScript types for the Blog Digest feature. Refer to `docs/blog_digest_ui_hld.md` → Section 3.4 for the types.
  >
  > Edit `frontend/src/types/index.ts` and add the following interfaces at the end of the file:
  >
  > ```typescript
  > export interface BlogDigestSchedule {
  >   hour: number;
  >   minute: number;
  >   timezone: string;
  >   enabled: boolean;
  > }
  >
  > export interface BlogDigestTriggerResult {
  >   detail: string;
  >   ticket_key: string | null;
  > }
  > ```

  **Acceptance Criteria:**
  - Both interfaces are exported from `types/index.ts`.
  - Types match the backend response schemas exactly.

---

### 3.2 — Frontend Query Keys

- [x] **Task 3.2: Add Blog Digest query keys**

  **Target Files:**
  - `frontend/src/lib/queryKeys.ts` (update)

  **Agent Prompt:**
  > Add query keys for the Blog Digest feature. Follow the existing pattern in `frontend/src/lib/queryKeys.ts`.
  >
  > Edit `frontend/src/lib/queryKeys.ts` and add a `blogDigest` section to the `queryKeys` object:
  >
  > ```typescript
  > blogDigest: {
  >   schedule: ["blogDigest", "schedule"] as const,
  > },
  > ```
  >
  > Add it after the `apiKeys` section, before the closing `} as const;`.

  **Acceptance Criteria:**
  - `queryKeys.blogDigest.schedule` is available and typed as `readonly ["blogDigest", "schedule"]`.

---

### 3.3 — Frontend API Module

- [x] **Task 3.3: Create the Blog Digest API module**

  **Target Files:**
  - `frontend/src/api/blogDigestApi.ts` (create)

  **Agent Prompt:**
  > Create the API module for Blog Digest. Follow the same pattern used in `frontend/src/api/jiraApi.ts` — import the shared `api` axios instance from `./client`, define typed functions for each endpoint.
  >
  > Create `frontend/src/api/blogDigestApi.ts`:
  >
  > ```typescript
  > import api from "./client";
  > import type { BlogDigestSchedule, BlogDigestTriggerResult } from "@/types";
  >
  > export async function triggerDigest(): Promise<BlogDigestTriggerResult> {
  >   const { data } = await api.post<BlogDigestTriggerResult>("/blog-digest/trigger");
  >   return data;
  > }
  >
  > export async function getSchedule(): Promise<BlogDigestSchedule> {
  >   const { data } = await api.get<BlogDigestSchedule>("/blog-digest/schedule");
  >   return data;
  > }
  >
  > export async function updateSchedule(
  >   payload: Omit<BlogDigestSchedule, never>,
  > ): Promise<BlogDigestSchedule> {
  >   const { data } = await api.put<BlogDigestSchedule>("/blog-digest/schedule", payload);
  >   return data;
  > }
  > ```

  **Acceptance Criteria:**
  - All three functions call the correct endpoints.
  - Types match the backend schemas.
  - Uses the shared `api` axios instance with interceptors.

---

### 3.4 — React Query Hooks

- [x] **Task 3.4: Create TanStack Query hooks for Blog Digest**

  **Target Files:**
  - `frontend/src/features/blog-digest/hooks/useBlogDigest.ts` (create)

  **Agent Prompt:**
  > Create the React Query hooks for the Blog Digest feature. Follow the patterns in `frontend/src/features/jira/hooks/useCreateTicket.ts` for mutations and `frontend/src/features/jira/hooks/useJiraStatus.ts` for queries.
  >
  > Create `frontend/src/features/blog-digest/hooks/useBlogDigest.ts` with three hooks:
  >
  > 1. **`useBlogDigestSchedule()`** — a `useQuery` hook:
  >    - Query key: `queryKeys.blogDigest.schedule`.
  >    - Query function: `getSchedule` from `@/api/blogDigestApi`.
  >    - No special options needed.
  >
  > 2. **`useUpdateSchedule()`** — a `useMutation` hook:
  >    - Mutation function: `updateSchedule` from `@/api/blogDigestApi`.
  >    - `onSuccess`: invalidate `queryKeys.blogDigest.schedule` and show `toast.success("Schedule updated")`.
  >    - `onError`: show `toast.error(getErrorMessage(error))` using `getErrorMessage` from `@/lib/errors`.
  >
  > 3. **`useTriggerDigest()`** — a `useMutation` hook:
  >    - Mutation function: `triggerDigest` from `@/api/blogDigestApi`.
  >    - `onSuccess(data)`: if `data.ticket_key`, show `toast.success(\`Blog digest ticket created: ${data.ticket_key}\`)`. Otherwise show `toast.success("Blog digest completed")`.
  >    - `onError(error)`:
  >      - If `getErrorCode(error) === "JIRA_NOT_CONNECTED"`, show `toast.error("Jira not connected — connect Jira first")`.
  >      - Otherwise show `toast.error(getErrorMessage(error))`.
  >
  > Import `useQuery`, `useMutation`, `useQueryClient` from `@tanstack/react-query`. Import `toast` from `sonner`. Import `getErrorMessage`, `getErrorCode` from `@/lib/errors`. Import `queryKeys` from `@/lib/queryKeys`.

  **Acceptance Criteria:**
  - `useBlogDigestSchedule` returns schedule data via React Query.
  - `useUpdateSchedule` invalidates the schedule query on success.
  - `useTriggerDigest` shows the ticket key in the success toast.
  - Error handling distinguishes `JIRA_NOT_CONNECTED` from other errors.

---

## Phase 4: Frontend — UI Components & Page

> **Goal:** Build the UI components, assemble the page, and wire it into routing and navigation.

---

### 4.1 — ManualTriggerCard Component

- [x] **Task 4.1: Create the ManualTriggerCard component**

  **Target Files:**
  - `frontend/src/features/blog-digest/components/ManualTriggerCard.tsx` (create)

  **Agent Prompt:**
  > Create the manual trigger card component for the Blog Digest page. Refer to `docs/blog_digest_ui_hld.md` → Section 3.2 for the layout and Section 6 for UX details. Use the existing shadcn/ui components from `@/components/ui/`.
  >
  > Create `frontend/src/features/blog-digest/components/ManualTriggerCard.tsx`:
  >
  > 1. Import `Card`, `CardContent`, `CardDescription`, `CardHeader`, `CardTitle` from `@/components/ui/card`.
  > 2. Import `Button` from `@/components/ui/button`.
  > 3. Import `Loader2`, `CheckCircle2`, `Newspaper` from `lucide-react`.
  > 4. Import `useTriggerDigest` from the hooks file.
  > 5. Import `Link` from `react-router-dom` (for linking to Jira settings on error).
  >
  > Build the component `ManualTriggerCard`:
  >
  > - Card header: title "Manual Trigger", description "Scrape the latest Oasis Security blog post, generate an AI summary, and create a Jira ticket."
  > - Card content:
  >   - A "Run Now" button with the `Newspaper` icon.
  >   - While the mutation is pending (`isPending`), show `Loader2` with `animate-spin` class and text "Running…". Button should be disabled.
  >   - When the mutation succeeds (`isSuccess` and `data`), show a success message below the button: a green `CheckCircle2` icon + "Ticket created: {data.ticket_key}" if `ticket_key` exists.
  >   - The button calls `triggerDigest.mutate()` on click.
  >   - Use `onClick={() => mutate()}` pattern.
  >
  > Style to match the existing app: Tailwind classes, `space-y-4` for content spacing, `text-sm text-muted-foreground` for secondary text.

  **Acceptance Criteria:**
  - "Run Now" button triggers the digest.
  - Loading state shows spinner and "Running…" text with button disabled.
  - Success state shows the ticket key.
  - Component uses shadcn/ui Card components.

---

### 4.2 — ScheduleCard Component

- [x] **Task 4.2: Create the ScheduleCard component**

  **Target Files:**
  - `frontend/src/features/blog-digest/components/ScheduleCard.tsx` (create)

  **Agent Prompt:**
  > Create the schedule management card for the Blog Digest page. Refer to `docs/blog_digest_ui_hld.md` → Section 3.2 for the layout and Section 6 for UX details. Use shadcn/ui components.
  >
  > Create `frontend/src/features/blog-digest/components/ScheduleCard.tsx`:
  >
  > 1. Import `Card`, `CardContent`, `CardDescription`, `CardHeader`, `CardTitle` from `@/components/ui/card`.
  > 2. Import `Button` from `@/components/ui/button`.
  > 3. Import `Label` from `@/components/ui/label`.
  > 4. Import `Switch` from `@/components/ui/switch`.
  > 5. Import `Select`, `SelectContent`, `SelectItem`, `SelectTrigger`, `SelectValue` from `@/components/ui/select`.
  > 6. Import `Loader2`, `Clock` from `lucide-react`.
  > 7. Import `useBlogDigestSchedule` and `useUpdateSchedule` from the hooks file.
  > 8. Import `useState`, `useEffect` from `react`.
  >
  > Build the component `ScheduleCard`:
  >
  > - Use `useBlogDigestSchedule()` to fetch current schedule. Show a loading skeleton while loading (simple `animate-pulse` placeholder divs).
  > - Use local state (`useState`) for `hour`, `minute`, `timezone`, and `enabled`. Initialize from the query data via a `useEffect` that runs when `data` changes.
  > - **Enable toggle:** A `Switch` component with label "Enable scheduled digest". When toggled off, the time/timezone fields become disabled (add `opacity-50 pointer-events-none` classes to the fields container).
  > - **Hour select:** A `Select` component with values 0–23, displayed as two-digit strings (e.g., "00", "01", …, "23").
  > - **Minute select:** A `Select` component with values 0, 15, 30, 45 (quarter-hour increments), displayed as two-digit strings.
  > - **Timezone select:** A `Select` component with options: `UTC`, `US/Eastern`, `US/Pacific`, `Europe/London`, `Europe/Berlin`, `Asia/Jerusalem`, `Asia/Tokyo`.
  > - **Save button:** "Save Schedule" with `Clock` icon. Disabled when mutation is pending. Shows `Loader2` spinner when saving.
  > - On save, call `updateSchedule.mutate({ hour, minute, timezone, enabled })`.
  >
  > Layout inside the card content:
  > - Row 1: Enable toggle (flex, items-center, justify-between).
  > - Row 2: Time selects (hour : minute) and timezone select in a flex row with gap-3. Wrapped in a div that gets disabled styling when `enabled` is false.
  > - Row 3: Save button aligned to the right.

  **Acceptance Criteria:**
  - Schedule loads from the API and populates the form.
  - Toggle disables/enables the time fields visually.
  - Hour, minute, and timezone are selectable.
  - Save button submits the update and shows loading state.
  - Toast shows on success/error (handled by the hook).

---

### 4.3 — BlogDigestPage

- [x] **Task 4.3: Create the BlogDigestPage and wire routing + navigation**

  **Target Files:**
  - `frontend/src/pages/BlogDigestPage.tsx` (create)
  - `frontend/src/App.tsx` (update)
  - `frontend/src/layouts/AppShell.tsx` (update)

  **Agent Prompt:**
  > Create the Blog Digest settings page and add it to the app routing and navigation. Follow the same patterns as `JiraSettingsPage` and `ApiKeysPage`.
  >
  > **1. Create `frontend/src/pages/BlogDigestPage.tsx`:**
  >
  > ```tsx
  > import { ManualTriggerCard } from "@/features/blog-digest/components/ManualTriggerCard";
  > import { ScheduleCard } from "@/features/blog-digest/components/ScheduleCard";
  >
  > export function BlogDigestPage() {
  >   return (
  >     <div className="mx-auto max-w-2xl space-y-6">
  >       <div className="space-y-1">
  >         <h1 className="text-xl font-semibold">Blog Digest</h1>
  >         <p className="text-sm text-muted-foreground">
  >           Manage automated NHI blog digests
  >         </p>
  >       </div>
  >       <ManualTriggerCard />
  >       <ScheduleCard />
  >     </div>
  >   );
  > }
  > ```
  >
  > **2. Update `frontend/src/App.tsx`:**
  >
  > - Add an import: `import { BlogDigestPage } from "@/pages/BlogDigestPage";`
  > - Add a route inside the `ProtectedRoute > AppShell` children array, after the `settings/api-keys` route:
  >   ```tsx
  >   { path: "settings/blog-digest", element: <BlogDigestPage /> },
  >   ```
  >
  > **3. Update `frontend/src/layouts/AppShell.tsx`:**
  >
  > - Add `Newspaper` to the lucide-react import: `import { ..., Newspaper } from "lucide-react";`
  > - Add a new nav item to the `navItems` array, after the "API Keys" entry:
  >   ```tsx
  >   {
  >     label: "Blog Digest",
  >     to: "/settings/blog-digest",
  >     icon: <Newspaper className="size-4" />,
  >     section: "Settings",
  >   },
  >   ```

  **Acceptance Criteria:**
  - `/settings/blog-digest` route renders the `BlogDigestPage`.
  - "Blog Digest" appears in the sidebar under "Settings" with the Newspaper icon.
  - Page layout matches the existing settings pages (max-w-2xl, same spacing).
  - Both cards render on the page.
  - Navigation highlights the correct item when on the page.

---

## Phase 5: Smoke Test

> **Goal:** Verify end-to-end that the feature works.

---

### 5.1 — End-to-End Smoke Test

- [x] **Task 5.1: Verify Blog Digest UI end-to-end**

  **Target Files:**
  - No new files — manual verification.

  **Agent Prompt:**
  > Run the full stack and verify the Blog Digest feature works end-to-end.
  >
  > 1. Start the stack: `docker compose up --build`.
  > 2. Verify the backend starts without errors and the `/blog-digest/schedule` endpoint is listed in `http://localhost:8000/docs` (Swagger UI).
  > 3. Test the API endpoints directly:
  >    - `GET /blog-digest/schedule` — should return `{"hour": 9, "minute": 0, "timezone": "UTC", "enabled": true}`.
  >    - `PUT /blog-digest/schedule` with `{"hour": 14, "minute": 30, "timezone": "US/Eastern", "enabled": true}` — should return updated schedule.
  >    - `GET /blog-digest/schedule` again — should reflect the update.
  >    - `PUT /blog-digest/schedule` with `{"enabled": false}` — should pause the job.
  > 4. Open `http://localhost:3000` and log in.
  > 5. Verify "Blog Digest" appears in the sidebar under Settings.
  > 6. Navigate to `/settings/blog-digest`.
  > 7. Verify the schedule card loads and displays the current schedule.
  > 8. Verify the enable/disable toggle works (fields grey out when disabled).
  > 9. Verify the hour/minute/timezone selects work.
  > 10. Note: the "Run Now" button requires Jira to be connected and Ollama to be running. If those aren't available, verify the button shows an appropriate error toast.

  **Acceptance Criteria:**
  - All API endpoints return correct responses.
  - Blog Digest page loads in the frontend.
  - Schedule can be viewed and updated from the UI.
  - Enable/disable toggle works.
  - No console errors in the browser.

---

## Dependency Graph

```
Phase 1 (Backend Internals)         Phase 2 (Backend Router)        Phase 3 (Frontend Data)         Phase 4 (Frontend UI)           Phase 5
───────────────────────             ────────────────────────        ───────────────────────          ─────────────────────           ───────
1.1 Schemas ──────────┐
1.2 Scheduler helpers ┤── 2.1 Router ──┐
1.3 Service changes ──┘   2.2 Wire ────┤── 3.1 Types ──────────┐
                                       │   3.2 Query keys ─────┤
                                       │   3.3 API module ─────┤── 4.1 ManualTriggerCard ──┐
                                       │   3.4 Hooks ──────────┘   4.2 ScheduleCard ───────┤── 5.1 Smoke test
                                       │                           4.3 Page + routing ─────┘
                                       │
                                       └── (backend must be running for frontend to test)
```

---

## Execution Notes

1. **Sequential within phases**: Tasks within each phase should be executed in order — later tasks may depend on earlier ones.
2. **Phase gates**: Do not start Phase 2 until Phase 1 is complete. Do not start Phase 3 until Phase 2 is complete (the API must exist for the frontend to type against). Phase 4 depends on Phase 3. Phase 5 depends on all previous phases.
3. **Phase 3 parallelism**: Tasks 3.1, 3.2, and 3.3 are independent of each other and can be done in parallel. Task 3.4 depends on all three.
4. **Phase 4 parallelism**: Tasks 4.1 and 4.2 are independent and can be done in parallel. Task 4.3 depends on both.
5. **Each task = one Cursor prompt**: Every task is scoped to be completable in a single Cursor Agent session.
6. **Commit after each task**: Create a git commit after each successful task.
7. **Total tasks**: 11 tasks across 5 phases (3 + 2 + 4 + 3 + 1). Minus the smoke test, 10 implementation tasks.
