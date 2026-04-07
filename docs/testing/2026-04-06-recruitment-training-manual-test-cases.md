# Recruitment & Training Enhancement — Manual Test Cases

**Date:** 2026-04-06
**Scope:** Phase 1-4 + Cross-Cutting (Notifications, Audit, Events, Permissions)
**Platforms:** Backend API, Web App, Mobile App

---

## Prerequisites

Before testing, ensure:
- [ ] Backend is running with latest migrations applied
- [ ] `recruitmentEnabled` and `trainingEnabled` are `true` in SystemControls (run `UPDATE "SystemControls" SET "recruitmentEnabled" = true, "trainingEnabled" = true;` for existing companies)
- [ ] Test user has `hr:read`, `hr:create`, `hr:update`, `hr:delete`, `hr:configure` permissions (or `hr:*`)
- [ ] Number Series configured for: Recruitment (REC-), Training (TRN-), Offer Management (OFF-), Training Session (TSN-), Training Program (PRG-), Employee
- [ ] At least 1 department, 1 designation, and 5+ employees exist in the system

---

## 1. Sidebar & Navigation

### TC-1.1: Recruitment sidebar items visible
**Steps:**
1. Login as Company Admin
2. Open sidebar

**Expected:** See "Recruitment & Training" group with: Job Requisitions, Candidates, Offers, Training Catalogue, Training Sessions, Trainers, Training Programs, Training Budgets, Training Nominations, Onboarding, Probation Reviews

### TC-1.2: Training analytics sidebar visible
**Steps:**
1. Check "HR Analytics" group in sidebar

**Expected:** See both "Recruitment Intelligence" and "Training Intelligence"

### TC-1.3: ESS training visible for employees
**Steps:**
1. Login as Employee user
2. Check "My Workspace" group

**Expected:** See "My Training" item

### TC-1.4: System Controls gating works
**Steps:**
1. Login as Company Admin
2. Go to System Controls settings
3. Disable "Recruitment Enabled"
4. Refresh sidebar

**Expected:** All recruitment items (Job Requisitions, Candidates, Offers, Recruitment Intelligence) disappear. Training items remain.

### TC-1.5: Re-enable shows items again
**Steps:**
1. Re-enable "Recruitment Enabled"
2. Refresh sidebar

**Expected:** Recruitment items reappear

---

## 2. Job Requisitions

### TC-2.1: Create requisition
**Steps:**
1. Navigate to Job Requisitions
2. Click "New Requisition" / FAB
3. Fill: Title = "Senior Developer", Department, Openings = 2, Employment Type = FULL_TIME, Priority = HIGH, Location = "Mumbai", Budget Min = 800000, Budget Max = 1200000, Requirements = "5+ years experience"
4. Save

**Expected:** Requisition created with auto-generated number (REC-XXXXX). Status = DRAFT. All fields persisted including employmentType, priority, location, requirements.

### TC-2.2: Status transitions (state machine)
**Steps:**
1. Open a DRAFT requisition
2. Change status to OPEN
3. Try to change back to DRAFT

**Expected:** DRAFT → OPEN succeeds. OPEN → DRAFT fails with "Invalid requisition status transition" error.

### TC-2.3: Valid transition chain
**Steps:**
1. DRAFT → OPEN (success)
2. OPEN → INTERVIEWING (success)
3. INTERVIEWING → OFFERED (success)
4. OFFERED → FILLED (success)

**Expected:** Each transition succeeds. FILLED is terminal — no further transitions allowed.

### TC-2.4: Cancel from any non-terminal state
**Steps:**
1. Create a requisition, move to OPEN
2. Cancel it

**Expected:** OPEN → CANCELLED succeeds. CANCELLED is terminal.

### TC-2.5: Delete only DRAFT
**Steps:**
1. Try to delete a requisition in OPEN status
2. Try to delete a requisition in DRAFT status

**Expected:** OPEN delete fails. DRAFT delete succeeds.

---

## 3. Candidates

### TC-3.1: Create candidate
**Steps:**
1. Open a requisition
2. Switch to Candidates tab
3. Add candidate: Name = "John Doe", Email = "john@test.com", Source = "LinkedIn"
4. Save

**Expected:** Candidate created with stage = APPLIED. Linked to requisition.

### TC-3.2: Stage advancement with state machine
**Steps:**
1. Advance candidate: APPLIED → SHORTLISTED (success)
2. Try: SHORTLISTED → FINAL (should fail — must go through HR_ROUND first)
3. Advance: SHORTLISTED → HR_ROUND → TECHNICAL → FINAL → OFFER_SENT → HIRED

**Expected:** Each valid transition succeeds. Invalid skips fail with state machine error.

### TC-3.3: Rejection requires reason
**Steps:**
1. Try to reject a candidate without providing a reason
2. Try again with reason = "Skills mismatch"

**Expected:** First attempt fails with "Reason is required when rejecting or putting on hold". Second succeeds.

### TC-3.4: ON_HOLD is reversible
**Steps:**
1. Put a candidate ON_HOLD with reason
2. Move back to SHORTLISTED

**Expected:** Both transitions succeed. ON_HOLD allows return to any non-terminal stage.

### TC-3.5: Stage history recorded
**Steps:**
1. Advance a candidate through 3+ stages
2. Open candidate detail screen
3. Check Stage History tab

**Expected:** Timeline shows all transitions with fromStage, toStage, reason, changedBy, timestamps.

### TC-3.6: Delete candidate
**Steps:**
1. Click Delete on a candidate
2. Confirm

**Expected:** Candidate deleted. Linked interviews also removed (cascade).

---

## 4. Interviews

### TC-4.1: Schedule interview
**Steps:**
1. Select a candidate
2. Switch to Interviews tab
3. Schedule: Round = "Technical", DateTime, Duration = 60 min, Meeting Link, Panelists
4. Save

**Expected:** Interview created with status = SCHEDULED.

### TC-4.2: Complete interview with feedback
**Steps:**
1. Click "Complete" on a SCHEDULED interview
2. Enter feedback rating (1-10) and notes
3. Submit

**Expected:** Status changes to COMPLETED. Feedback rating and notes saved.

### TC-4.3: Cancel interview
**Steps:**
1. Click "Cancel" on a SCHEDULED interview
2. Confirm

**Expected:** Status changes to CANCELLED. Cannot complete a cancelled interview.

### TC-4.4: Cannot modify completed interview
**Steps:**
1. Try to edit a COMPLETED interview
2. Try to cancel a COMPLETED interview

**Expected:** Both actions fail — COMPLETED is terminal.

### TC-4.5: Submit structured evaluation
**Steps:**
1. Open candidate detail → Interviews tab
2. Click "Submit Evaluation" on a completed interview
3. Rate 5 dimensions (Technical Skills, Communication, Problem Solving, Cultural Fit, Domain Knowledge) — each 1-5
4. Add comments and recommendation (STRONG_HIRE)
5. Submit

**Expected:** Evaluation saved. Visible in the interview's evaluation section.

---

## 5. Offers

### TC-5.1: Create offer
**Steps:**
1. Switch to Offers tab in Requisitions screen
2. Click "New Offer"
3. Fill: Candidate, Offered CTC = 1000000, Joining Date, Valid Until, Designation, Department
4. Save

**Expected:** Offer created with auto-generated number (OFF-XXXXX). Status = DRAFT.

### TC-5.2: Offer lifecycle
**Steps:**
1. Send offer (DRAFT → SENT)
2. Accept offer (SENT → ACCEPTED)

**Expected:** Each transition succeeds. On ACCEPTED, candidate stage auto-advances to HIRED.

### TC-5.3: Reject offer with reason
**Steps:**
1. Create and send an offer
2. Reject it

**Expected:** Must provide rejection reason. Status = REJECTED. rejectedAt timestamp set.

### TC-5.4: Withdraw offer
**Steps:**
1. Create and send an offer
2. Withdraw it

**Expected:** SENT → WITHDRAWN succeeds. withdrawnAt timestamp set.

### TC-5.5: Offer expiry (lazy)
**Steps:**
1. Create an offer with validUntil = yesterday's date
2. Send it (DRAFT → SENT)
3. Refresh the offers list

**Expected:** Offer status auto-updates to EXPIRED on next list/get query.

### TC-5.6: Delete only DRAFT offers
**Steps:**
1. Try to delete a SENT offer
2. Try to delete a DRAFT offer

**Expected:** SENT delete fails. DRAFT delete succeeds.

---

## 6. Candidate Detail Screen

### TC-6.1: Profile card displays correctly
**Steps:**
1. Click on a candidate name to open detail screen

**Expected:** Profile card shows: name, email, phone, source badge, rating stars, stage badge. Back button works.

### TC-6.2: Add education
**Steps:**
1. Go to Education tab
2. Add: Qualification = "B.Tech", Degree = "Computer Science", Institution = "IIT", Year = 2020, Percentage = 85
3. Save

**Expected:** Education record appears in list.

### TC-6.3: Add experience
**Steps:**
1. Go to Experience tab
2. Add: Company = "TCS", Designation = "Software Engineer", From = 2020-01, To = 2023-06, CTC = 800000
3. Save

**Expected:** Experience record appears in list.

### TC-6.4: Upload document
**Steps:**
1. Go to Documents tab
2. Add: Type = RESUME, File Name = "resume.pdf", File URL = "https://..."
3. Save

**Expected:** Document appears in list with type badge.

### TC-6.5: Convert to Employee
**Steps:**
1. Ensure candidate stage = HIRED with an ACCEPTED offer
2. Click "Convert to Employee"
3. Review pre-filled employee form

**Expected:** Employee created with data from candidate + offer (name, email, designation, department, CTC, joining date). Candidate's employeeId set. Mandatory trainings auto-nominated.

### TC-6.6: Cannot convert non-HIRED candidate
**Steps:**
1. Open a candidate in APPLIED stage
2. Look for "Convert to Employee" button

**Expected:** Button not visible (or disabled) for non-HIRED candidates.

---

## 7. Training Catalogue

### TC-7.1: Create training
**Steps:**
1. Navigate to Training Catalogue
2. Click "New Course"
3. Fill: Name = "React Advanced", Type = Technical, Mode = Online, Duration = 40h, Cost = 5000, Mandatory = true, Certification Name = "React Expert"
4. Save

**Expected:** Training created with auto-generated number (TRN-XXXXX). isActive = true.

### TC-7.2: Edit training
**Steps:**
1. Edit the training, change cost to 7500
2. Save

**Expected:** Cost updated. Other fields unchanged.

### TC-7.3: Delete training (no nominations)
**Steps:**
1. Delete a training with no nominations

**Expected:** Deleted successfully.

### TC-7.4: Cannot delete training with nominations
**Steps:**
1. Create a nomination for a training
2. Try to delete the training

**Expected:** Delete fails — "Cannot delete training with existing nominations."

### TC-7.5: Add training materials
**Steps:**
1. Open a training catalogue item
2. Add material: Name = "Course PDF", Type = PDF, URL = "https://...", Mandatory = true
3. Save

**Expected:** Material appears in materials list with type badge.

---

## 8. Training Nominations

### TC-8.1: Create nomination
**Steps:**
1. Switch to Nominations tab
2. Nominate an employee for a training
3. Save

**Expected:** Nomination created with status = NOMINATED.

### TC-8.2: Nomination status flow
**Steps:**
1. NOMINATED → APPROVED (success)
2. APPROVED → IN_PROGRESS (success)
3. IN_PROGRESS → COMPLETED (success)

**Expected:** Each transition succeeds per state machine.

### TC-8.3: Cancel nomination
**Steps:**
1. Cancel a NOMINATED nomination
2. Try to cancel a COMPLETED nomination

**Expected:** NOMINATED → CANCELLED succeeds. COMPLETED → CANCELLED fails (terminal).

### TC-8.4: Completion with certificate auto-issuance
**Steps:**
1. Create a nomination for a training that has certificationName + certificationValidity
2. Complete the nomination with score = 85

**Expected:** certificateNumber generated, certificateIssuedAt set, certificateExpiryDate calculated (issuedAt + validity years), certificateStatus = EARNED.

### TC-8.5: Skill auto-mapping on completion
**Steps:**
1. Create a training with linkedSkillIds pointing to valid SkillLibrary entries
2. Create and complete a nomination

**Expected:** Employee's SkillMapping records updated with proficiency gain from the training.

---

## 9. Training Sessions

### TC-9.1: Create session
**Steps:**
1. Switch to Sessions tab
2. Create session: Training = "React Advanced", Batch = "Batch 1", Start DateTime, End DateTime, Venue = "Room 101", Max Participants = 20, Trainer (select from list)
3. Save

**Expected:** Session created with auto-generated number (TSN-XXXXX). Status = SCHEDULED.

### TC-9.2: Session date validation
**Steps:**
1. Try to create a session where End DateTime < Start DateTime

**Expected:** Validation error: "End date/time must be after start date/time."

### TC-9.3: Session status transitions
**Steps:**
1. SCHEDULED → IN_PROGRESS (Start)
2. IN_PROGRESS → COMPLETED (Complete)

**Expected:** Both succeed. COMPLETED is terminal.

### TC-9.4: Cancel session with reason
**Steps:**
1. Cancel a SCHEDULED session
2. Must provide cancellation reason

**Expected:** Status = CANCELLED with reason saved.

### TC-9.5: Register attendees
**Steps:**
1. Open a session's attendance
2. Register 5 employees

**Expected:** 5 TrainingAttendance records created with status = REGISTERED.

### TC-9.6: Mark attendance (individual)
**Steps:**
1. Mark one attendee as PRESENT with check-in time
2. Mark another as ABSENT

**Expected:** Statuses updated. hoursAttended calculated for PRESENT attendee.

### TC-9.7: Bulk mark attendance
**Steps:**
1. Click "Mark All Present"

**Expected:** All attendees marked PRESENT in one operation.

### TC-9.8: Session completion auto-advances nominations
**Steps:**
1. Register employees who have IN_PROGRESS nominations for this training
2. Mark them PRESENT
3. Complete the session

**Expected:** Their linked nominations auto-advance to COMPLETED. Certificate fields auto-set if applicable. Trainer's totalSessions incremented.

---

## 10. Trainers

### TC-10.1: Create internal trainer
**Steps:**
1. Switch to Trainers tab
2. Create: Select Employee, Email, Specializations = ["React", "Node.js"], Experience = 5 years
3. Save

**Expected:** Trainer created. isInternal = true. Employee name shown.

### TC-10.2: Create external trainer
**Steps:**
1. Create: External Name = "John Expert", Email = "john@external.com", isInternal = false
2. Save

**Expected:** Trainer created with externalName. isInternal = false.

### TC-10.3: Deactivate trainer (soft delete)
**Steps:**
1. Delete a trainer

**Expected:** isActive set to false. Trainer no longer appears in active list but still visible in session history.

### TC-10.4: Trainer rating auto-update
**Steps:**
1. Create sessions assigned to a trainer
2. Submit PARTICIPANT_FEEDBACK evaluations with trainerEffectiveness ratings
3. Check trainer's averageRating

**Expected:** averageRating recalculated as average of all trainerEffectiveness scores.

---

## 11. Training Evaluations / Feedback

### TC-11.1: Admin submits trainer assessment
**Steps:**
1. Go to a nomination → Submit Evaluation
2. Type = TRAINER_ASSESSMENT
3. Fill: preAssessmentScore = 40, postAssessmentScore = 85, comments

**Expected:** Evaluation created. Knowledge gain visible.

### TC-11.2: Employee submits feedback (ESS)
**Steps:**
1. Login as employee
2. Go to My Training
3. Find a COMPLETED nomination
4. Click "Give Feedback"
5. Rate: Content Relevance = 4, Trainer Effectiveness = 5, Overall Satisfaction = 4, Knowledge Gain = 5, Practical Applicability = 3
6. Add comments

**Expected:** PARTICIPANT_FEEDBACK evaluation created. Trainer's averageRating updated.

### TC-11.3: Cannot submit duplicate feedback
**Steps:**
1. Try to submit feedback again for the same nomination

**Expected:** Error — duplicate submission not allowed.

### TC-11.4: Evaluation summary
**Steps:**
1. Query evaluation summary for a training (API: GET /hr/training-evaluations/summary?trainingId=xxx)

**Expected:** Aggregated averages across all evaluations for that training.

---

## 12. Training Programs / Learning Paths

### TC-12.1: Create program
**Steps:**
1. Switch to Programs tab
2. Create: Name = "Full Stack Developer Track", Category = SKILL_DEVELOPMENT, Level = INTERMEDIATE
3. Save

**Expected:** Program created with auto-generated number (PRG-XXXXX).

### TC-12.2: Add courses to program
**Steps:**
1. Open program detail
2. Add courses: Course 1 (sequence 1, isPrerequisite = true), Course 2 (sequence 2), Course 3 (sequence 3)
3. Save each

**Expected:** Courses appear in order. Sequence and prerequisite flags saved.

### TC-12.3: Enroll employees
**Steps:**
1. Click "Enroll Employees"
2. Select 3 employees
3. Confirm

**Expected:** 3 TrainingProgramEnrollment records created. Status = ENROLLED. progressPercent = 0.

### TC-12.4: Progress tracking
**Steps:**
1. Complete nomination for Course 1 for an enrolled employee
2. Check enrollment progress

**Expected:** progressPercent = 33% (1 of 3 courses). Status = IN_PROGRESS.

### TC-12.5: Prerequisite enforcement
**Steps:**
1. Try to create a nomination for Course 2 without completing Course 1 (which is isPrerequisite)

**Expected:** Error — prerequisite course not completed.

### TC-12.6: Program auto-completion
**Steps:**
1. Complete all 3 courses for an employee

**Expected:** progressPercent = 100%. Status auto-transitions to COMPLETED. completedAt set.

---

## 13. Training Budgets

### TC-13.1: Create budget
**Steps:**
1. Switch to Budgets tab
2. Create: Fiscal Year = "2026-27", Department = "Engineering", Allocated Amount = 500000
3. Save

**Expected:** Budget created. usedAmount = 0.

### TC-13.2: Auto-increment on completion
**Steps:**
1. Complete a training nomination for an employee in Engineering department
2. Check the Engineering budget for current fiscal year

**Expected:** usedAmount incremented by the training's costPerHead.

### TC-13.3: Budget utilization view
**Steps:**
1. View utilization for fiscal year "2026-27"

**Expected:** Per-department breakdown showing allocated, used, remaining, utilization %.

### TC-13.4: Delete unused budget
**Steps:**
1. Delete a budget with usedAmount = 0

**Expected:** Deleted successfully.

### TC-13.5: Cannot delete used budget
**Steps:**
1. Try to delete a budget with usedAmount > 0

**Expected:** Error — cannot delete a budget that has been used.

---

## 14. Expiring Certificates

### TC-14.1: Certificates expiring within 30 days
**Steps:**
1. Query API: GET /hr/training-certificates/expiring?days=30

**Expected:** Returns nominations where certificateStatus = EARNED and certificateExpiryDate is within 30 days.

### TC-14.2: Training dashboard shows expiring count
**Steps:**
1. Open Training Intelligence dashboard

**Expected:** Expiring certificates count visible in KPIs.

---

## 15. Analytics Dashboards

### TC-15.1: Recruitment dashboard
**Steps:**
1. Navigate to Recruitment Intelligence
2. Check all KPI widgets

**Expected:** Shows: pipeline by stage, time-to-hire, upcoming interviews, source effectiveness, funnel conversion rates, offer acceptance rate, requisition aging.

### TC-15.2: Training dashboard
**Steps:**
1. Navigate to Training Intelligence
2. Check all KPI widgets

**Expected:** Shows: total programmes, active nominations, completion rate, mandatory coverage, expiring certificates, top trainers, session stats, budget utilization, program completion rates.

### TC-15.3: Zero-data state
**Steps:**
1. Login as a new company with no recruitment data
2. Open Recruitment Intelligence

**Expected:** Shows "No recruitment data yet" with CTA to create first requisition.

---

## 16. Notifications

### TC-16.1: Notification bell visible
**Steps:**
1. Login as any user
2. Check the app header

**Expected:** Bell icon visible. Shows unread count badge (or no badge if 0).

### TC-16.2: Interview scheduled triggers notification
**Steps:**
1. Schedule an interview with panelists (employee IDs)
2. Check the panelists' notification bell

**Expected:** Each panelist sees "Interview Scheduled" notification in their bell dropdown/sheet.

### TC-16.3: Training nomination triggers notification
**Steps:**
1. Nominate an employee for a training
2. Check the employee's notification bell

**Expected:** Employee sees "Training Nomination" notification.

### TC-16.4: Training completed triggers notification
**Steps:**
1. Complete a training nomination
2. Check the employee's notification bell

**Expected:** Employee sees "Training Completed" notification.

### TC-16.5: Mark notification as read
**Steps:**
1. Click on an unread notification
2. Check styling changes

**Expected:** Notification marked as read. Unread count decremented. Visual indicator changes.

### TC-16.6: Mark all as read
**Steps:**
1. Click "Mark all as read"

**Expected:** All notifications marked as read. Unread count = 0.

### TC-16.7: Notification list (web)
**Steps:**
1. Click "View all notifications" in dropdown

**Expected:** Full notification list page with pagination, type badges, mark-as-read on click.

### TC-16.8: Push notification (requires FCM setup)
**Steps:**
1. Ensure FIREBASE_SERVICE_ACCOUNT_KEY is set (backend) and VITE_FIREBASE_* vars set (web)
2. Allow browser notification permission
3. Trigger an event (schedule interview)

**Expected:** Browser push notification appears. Clicking it navigates to relevant screen.

### TC-16.9: Mobile push notification (requires EAS build)
**Steps:**
1. Build app with EAS (not Expo Go)
2. Allow notification permission
3. Trigger an event

**Expected:** Mobile push notification appears. Tapping navigates to relevant screen via deep-link.

### TC-16.10: Device token lifecycle
**Steps:**
1. Login → verify device registered (POST /notifications/register-device called)
2. Logout → verify device unregistered (DELETE /notifications/register-device called)
3. Login again → new token registered

**Expected:** Clean token lifecycle. No stale tokens after logout.

---

## 17. Audit Trail

### TC-17.1: Status changes are logged
**Steps:**
1. Change a requisition status (DRAFT → OPEN)
2. Query audit log: GET /hr/audit-log?entityType=JobRequisition&entityId=xxx

**Expected:** Audit entry with action = STATUS_CHANGE, changes = `{status: {from: "DRAFT", to: "OPEN"}}`, changedBy = userId.

### TC-17.2: Offer status changes logged
**Steps:**
1. Send an offer (DRAFT → SENT)
2. Accept it (SENT → ACCEPTED)
3. Query audit log for the offer

**Expected:** 2 audit entries showing both transitions.

### TC-17.3: Candidate stage changes logged
**Steps:**
1. Advance a candidate through 3 stages
2. Query audit log

**Expected:** 3 audit entries with stage transitions and changedBy.

### TC-17.4: Audit log has retention date
**Steps:**
1. Check a recent audit log entry

**Expected:** retentionDate = changedAt + 12 months.

---

## 18. Permissions

### TC-18.1: Granular recruitment permissions
**Steps:**
1. Create a role with `recruitment:read` but NOT `recruitment:create`
2. Assign to a user
3. Login as that user
4. Try to view requisitions (should work)
5. Try to create a requisition (should fail)

**Expected:** Read works. Create returns 403 Forbidden.

### TC-18.2: Offer-specific permissions
**Steps:**
1. Create a role with `recruitment:read` but NOT `recruitment-offer:read`
2. Try to view offers

**Expected:** Offers not accessible (403).

### TC-18.3: Training evaluation permission
**Steps:**
1. Create a role with `training-evaluation:create`
2. Try to submit an evaluation (should work)
3. Without that permission, try to submit (should fail)

**Expected:** Permission enforced.

### TC-18.4: Backward compatibility with hr:*
**Steps:**
1. Assign a role with `hr:read` (old style)
2. Try to access recruitment endpoints
3. Try to access training endpoints

**Expected:** Both work — old `hr:*` permissions still accepted alongside new granular ones.

---

## 19. State Machine (Cross-Cutting Validation)

### TC-19.1: All status enums enforce transitions
Test each entity's state machine:

| Entity | Valid Chain | Invalid Transition |
|--------|-----------|-------------------|
| Requisition | DRAFT→OPEN→INTERVIEWING→OFFERED→FILLED | OPEN→DRAFT |
| Candidate | APPLIED→SHORTLISTED→HR_ROUND→...→HIRED | APPLIED→FINAL |
| Interview | SCHEDULED→COMPLETED | COMPLETED→SCHEDULED |
| Offer | DRAFT→SENT→ACCEPTED | ACCEPTED→DRAFT |
| Nomination | NOMINATED→APPROVED→IN_PROGRESS→COMPLETED | COMPLETED→NOMINATED |
| Session | SCHEDULED→IN_PROGRESS→COMPLETED | COMPLETED→SCHEDULED |
| Program Enrollment | ENROLLED→IN_PROGRESS→COMPLETED | COMPLETED→ENROLLED |

**Expected:** Every invalid transition returns "Invalid {entity} transition: cannot move from X to Y."

---

## 20. Cross-Platform Consistency

### TC-20.1: Web and mobile show same data
**Steps:**
1. Create a requisition on web
2. Open mobile app → Job Requisitions

**Expected:** Same requisition visible with all fields matching.

### TC-20.2: Enum values match
**Steps:**
1. Create entities with all enum values on web
2. View them on mobile

**Expected:** All status badges, type badges, and enum displays match between platforms.

### TC-20.3: API function consistency
**Steps:**
1. Perform the same CRUD operation on web and mobile
2. Compare network requests

**Expected:** Same endpoints, same request bodies, same response shapes.

---

## 21. ESS (Employee Self-Service)

### TC-21.1: My Training screen
**Steps:**
1. Login as employee
2. Navigate to My Training

**Expected:** Shows all training nominations for this employee. Read-only (no edit/delete).

### TC-21.2: View training materials
**Steps:**
1. Tap/click on an IN_PROGRESS or COMPLETED training
2. Check materials section

**Expected:** Training materials (if any) visible with name, type, and open/download link.

### TC-21.3: Give feedback on completed training
**Steps:**
1. Find a COMPLETED nomination
2. Click "Give Feedback"
3. Fill all 5 rating dimensions + comments
4. Submit

**Expected:** Feedback saved. Button changes to "Feedback Submitted" (or similar).

---

## 22. Candidate-to-Employee Conversion Flow (End-to-End)

### TC-22.1: Full recruitment-to-onboarding flow
**Steps:**
1. Create requisition
2. Add candidate
3. Schedule and complete interview with evaluation
4. Create and send offer
5. Accept offer (candidate auto-moves to HIRED)
6. Convert candidate to employee
7. Check employee record
8. Check mandatory training nominations auto-created

**Expected:** Complete end-to-end flow. Employee has data from candidate + offer. Mandatory trainings nominated automatically.

---

## Test Summary Checklist

| Section | Test Cases | Status |
|---------|:---------:|:------:|
| Sidebar & Navigation | 5 | |
| Job Requisitions | 5 | |
| Candidates | 6 | |
| Interviews | 5 | |
| Offers | 6 | |
| Candidate Detail | 6 | |
| Training Catalogue | 5 | |
| Training Nominations | 5 | |
| Training Sessions | 8 | |
| Trainers | 4 | |
| Training Evaluations | 4 | |
| Training Programs | 6 | |
| Training Budgets | 5 | |
| Expiring Certificates | 2 | |
| Analytics Dashboards | 3 | |
| Notifications | 10 | |
| Audit Trail | 4 | |
| Permissions | 4 | |
| State Machine | 1 (7 entities) | |
| Cross-Platform | 3 | |
| ESS | 3 | |
| E2E Conversion Flow | 1 | |
| **Total** | **105** | |
