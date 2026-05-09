## Goal
Let you preview the bottom suggestion drawer without having to record or upload audio first.

## Approach
Add a small "Preview suggestions" demo button on the home screen that opens the drawer pre-filled with a sample transcript and 5 example suggestion cards. This uses the existing Drawer UI exactly as it appears after a real upload — same layout, animation, and styling — just bypassing the AI call.

## What changes
- `src/routes/index.tsx`
  - Add a subtle "See example" link/button under the upload control.
  - On click, set a sample transcript + sample suggestions and open the drawer.
  - No changes to the recording, upload, or edge function flow.

## Sample content shown in the drawer
- Transcript: "I want to plan a weekend trip to the mountains with my friends."
- 5 suggestion cards (title + detail), e.g.:
  1. Pick a destination — shortlist 2–3 mountain spots within driving distance.
  2. Check the weather — review the forecast before locking dates.
  3. Build a packing list — layers, hiking shoes, water, snacks.
  4. Share an itinerary — send a draft plan to friends for input.
  5. Book early — reserve cabins or campsites this week.

## Out of scope
- No backend changes, no new dependencies, no design system changes.
- The demo button can be removed later in one line if you don't want it in production.