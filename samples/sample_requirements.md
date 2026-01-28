# Campus Event Companion — Requirements Pack (Sample)

## 1. Problem Statement
Students struggle to discover campus events and keep track of what they plan to attend. Organizers struggle to manage RSVPs and communicate changes.

## 2. Personas
- Student: discovers events, RSVPs, receives reminders.
- Organizer: creates/edits events, views RSVPs, cancels events.

## 3. In Scope (MVP)
### 3.1 Authentication & Roles
- Users can sign up and log in.
- Roles: `student`, `organizer`.
- Students can only RSVP/manage their own RSVPs.
- Organizers can only manage events they created.

### 3.2 Events
- Organizer can create an event with:
  - title, description, category (e.g., sports, academic, social), start/end datetime, location, capacity (optional), visibility (public).
- Organizer can edit/cancel their event.
- Students can list events with filters:
  - date range, category, keyword search, location.
- Students can view event details.

### 3.3 RSVP
- Student can RSVP/un-RSVP.
- If event has capacity, prevent RSVP when full.
- Organizer can view RSVP list for their event.

### 3.4 Notifications (Basic)
- System sends reminder notifications (email placeholder is OK for MVP):
  - 24 hours before start time.
- If event is canceled, RSVP’d students are notified.

## 4. Out of Scope (for now)
- Payments/ticketing
- Social features (comments, likes)
- Mobile app
- Complex recommendation engine

## 5. Non-Functional Requirements
- Security:
  - JWT auth, role-based authorization, input validation.
- Reliability:
  - Must handle empty/invalid inputs with friendly errors.
- Performance:
  - Event list endpoint should respond in < 500ms for typical loads (MVP).

## 6. Edge Cases
- RSVP race condition when capacity is nearly full.
- Organizer tries to edit an event they don’t own.
- Student tries to view organizer-only RSVP list.
- Invalid date ranges (end before start).

## 7. Success Metrics
- Time to find an event and RSVP: < 2 minutes.
- RSVP conversion rate increases for organizers.

## 8. Demo Data (Examples)
- Category examples: Academic, Sports, Social, Career
- Locations: Main Hall, Library, Gym
