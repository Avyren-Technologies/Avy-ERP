# Avy ERP — Master Product Requirements Document
## Part 5: Module Specifications — Production, Machine Maintenance, Calibration, Quality Management, EHSS, CRM & Project Management

> **Product:** Avy ERP
> **Company:** Avyren Technologies
> **Document Series:** PRD-005 of 5
> **Version:** 2.0
> **Date:** April 2026
> **Status:** Final Draft · Confidential
> **Scope:** Full module definitions for Production (Shop Floor), Machine Maintenance, Calibration Management, Quality Management, Environmental Health Safety & Sustainability (EHSS), Customer Relationship Management (CRM), and Project Management

---

## Table of Contents

1. [Module 8 — Production (Shop Floor)](#1-module-8--production-shop-floor)
   - 1.1 [Module Overview](#11-module-overview)
   - 1.2 [OEE — Overall Equipment Effectiveness](#12-oee--overall-equipment-effectiveness)
   - 1.3 [Production Input Logging](#13-production-input-logging)
   - 1.4 [Scrap & Non-Conformance Recording](#14-scrap--non-conformance-recording)
   - 1.5 [Shift Performance Summary](#15-shift-performance-summary)
   - 1.6 [Incentive Computation](#16-incentive-computation)
   - 1.7 [Production Reports](#17-production-reports)
2. [Module 6 — Machine Maintenance](#2-module-6--machine-maintenance)
   - 2.1 [Module Overview](#21-module-overview)
   - 2.2 [Preventive Maintenance (PM)](#22-preventive-maintenance-pm)
   - 2.3 [Breakdown Management](#23-breakdown-management)
   - 2.4 [Spare Parts Management](#24-spare-parts-management)
   - 2.5 [OEE Contribution — Availability Factor](#25-oee-contribution--availability-factor)
   - 2.6 [Maintenance Reports](#26-maintenance-reports)
3. [Sub-Module — Calibration Management](#3-sub-module--calibration-management)
   - 3.1 [Module Overview](#31-module-overview)
   - 3.2 [Instrument / Equipment Master](#32-instrument--equipment-master)
   - 3.3 [Calibration Schedule & Auto-Generation](#33-calibration-schedule--auto-generation)
   - 3.4 [Calibration Execution & Results Recording](#34-calibration-execution--results-recording)
   - 3.5 [Pass / Fail / Conditional Disposition](#35-pass--fail--conditional-disposition)
   - 3.6 [Out-of-Tolerance Handling](#36-out-of-tolerance-handling)
   - 3.7 [Audit Trail & Electronic Signatures](#37-audit-trail--electronic-signatures)
   - 3.8 [Calibration Reports](#38-calibration-reports)
4. [Quality Management Module](#4-quality-management-module)
   - 4.1 [Module Overview](#41-module-overview)
   - 4.2 [Incoming Quality Control (IQC)](#42-incoming-quality-control-iqc)
   - 4.3 [In-Process Quality Control (IPQC)](#43-in-process-quality-control-ipqc)
   - 4.4 [Final / Outgoing Quality Control (FQC)](#44-final--outgoing-quality-control-fqc)
   - 4.5 [Non-Conformance Management (NCR)](#45-non-conformance-management-ncr)
   - 4.6 [Corrective & Preventive Action (CAPA)](#46-corrective--preventive-action-capa)
   - 4.7 [Document Control](#47-document-control)
   - 4.8 [Quality Reports & Metrics](#48-quality-reports--metrics)
5. [EHSS Module — Environmental Health, Safety & Sustainability](#5-ehss-module--environmental-health-safety--sustainability)
   - 5.1 [Module Overview](#51-module-overview)
   - 5.2 [Incident Management](#52-incident-management)
   - 5.3 [Risk Assessment](#53-risk-assessment)
   - 5.4 [Safety Observations & Near-Miss Reporting](#54-safety-observations--near-miss-reporting)
   - 5.5 [PPE & Safety Equipment Management](#55-ppe--safety-equipment-management)
   - 5.6 [Environmental Monitoring](#56-environmental-monitoring)
   - 5.7 [Safety Training & Compliance Tracking](#57-safety-training--compliance-tracking)
   - 5.8 [EHSS Reports & Dashboards](#58-ehss-reports--dashboards)
6. [CRM Module — Customer Relationship Management](#6-crm-module--customer-relationship-management)
   - 6.1 [Module Overview](#61-module-overview)
   - 6.2 [Contact & Account Management](#62-contact--account-management)
   - 6.3 [Lead Management](#63-lead-management)
   - 6.4 [Opportunity Pipeline](#64-opportunity-pipeline)
   - 6.5 [Activity & Communication Tracking](#65-activity--communication-tracking)
   - 6.6 [Quotation Integration](#66-quotation-integration)
   - 6.7 [CRM Reports & Dashboards](#67-crm-reports--dashboards)
7. [Project Management Module](#7-project-management-module)
   - 7.1 [Module Overview](#71-module-overview)
   - 7.2 [Project Setup & Structure](#72-project-setup--structure)
   - 7.3 [Task & Work Package Management](#73-task--work-package-management)
   - 7.4 [Resource Management](#74-resource-management)
   - 7.5 [Milestone & Timeline Tracking](#75-milestone--timeline-tracking)
   - 7.6 [Project Cost Tracking](#76-project-cost-tracking)
   - 7.7 [Project Reports & Dashboards](#77-project-reports--dashboards)
8. [Cross-Module Integration Summary](#8-cross-module-integration-summary)

---

## 1. Module 8 — Production (Shop Floor)

### 1.1 Module Overview

The Production module is the shop-floor management layer of Avy ERP. It provides real-time visibility into manufacturing operations through OEE (Overall Equipment Effectiveness) monitoring, shift-wise production logging, scrap and non-conformance recording, and automatic incentive computation.

The Production module depends on the Machine Maintenance module (for machine availability and downtime data) and the Masters module (Item Master, Operation Master, Machine Master). It feeds incentive data back to the HR module's payroll engine.

**Key Capabilities:**
- Real-time OEE dashboard with per-machine, per-shift, and aggregate views
- Shift-wise production slip entry (mobile-optimised for shop-floor operators)
- Scrap and NC (non-conformance) logging with reason codes
- Automatic incentive calculation linked to production output
- Daily, weekly, and monthly performance summaries

### 1.2 OEE — Overall Equipment Effectiveness

**OEE Formula:**
> **OEE = Availability × Performance × Quality**

**OEE Components:**

| Component | Formula | Data Source |
|---|---|---|
| **Availability** | (Planned Time − Downtime) ÷ Planned Time | Machine Maintenance module (breakdown durations + PM stoppages) |
| **Performance** | (Actual Output × Ideal Cycle Time) ÷ (Planned Time − Downtime) | Production input logs (actual quantities produced) |
| **Quality** | (Accepted Output) ÷ (Total Output) | Production slips (good qty vs good qty + scrap qty) |

**OEE Colour Coding:**

| OEE Range | Status | Colour |
|---|---|---|
| ≥ 85% | World Class | Green |
| 60% – 84% | Acceptable | Amber |
| < 60% | Needs Attention | Red |

**OEE Dashboard:**
The OEE Dashboard is the primary production visibility screen. It shows:
- Individual OEE gauge per machine (real-time or last-shift)
- Availability, Performance, and Quality % for each machine separately
- Aggregate plant-level OEE
- Trend chart: OEE over the last 7 shifts / 30 days / 12 months
- Top 3 downtime reasons (from Machine Maintenance IOT Reason breakdown)
- Shift comparison: current shift vs prior shift

### 1.3 Production Input Logging

**Production Slip:**
The primary data entry document of the Production module. A production slip records what was made in a given shift.

**Production Slip Fields:**

| Field | Notes |
|---|---|
| Slip Number | Auto-generated from No Series |
| Date | Production date |
| Shift | Morning / Afternoon / Night — selected from Shift Master |
| Machine | From Machine Master |
| Operation | From Operation Master (what process was done on this machine) |
| Part / Product | From Part Master |
| Employee | Shop-floor operator who performed the work |
| Target Quantity | Expected production for this shift/machine/operation combination |
| Good Quantity | Units that passed quality check |
| Scrap Quantity | Units rejected during production (see Scrap entry below) |
| Start Time / End Time | Actual production window |

**Mobile Entry:**
Production slips are designed for mobile entry on the shop floor. Each shift, the supervisor or operator selects their machine, operation, and part, enters quantities, and submits. The form uses large touch targets and minimal required fields for speed.

**Batch Entry:**
For facilities running the same operation repeatedly, batch entry mode allows multiple machine/operator/part combinations to be entered on a single screen with a single submit.

### 1.4 Scrap & Non-Conformance Recording

**Scrap Entry:**
Scrap is production output that cannot be used or repaired. Scrap is recorded as part of the production slip (as Scrap Quantity) or independently.

**NC (Non-Conformance) Entry:**
NCs are units that fail a quality checkpoint during production. Unlike scrap, NCs may be reworkable.

**Scrap / NC Record Fields:**
- Linked production slip (or standalone)
- Part / Product
- Machine, Operation
- Quantity
- Rejection Reason (from a configurable rejection reason master: dimensional non-conformance, surface defect, material defect, operator error, machine fault, etc.)
- Disposition: Scrap / Rework / Return to Vendor / Hold for Review
- Rework status tracking (if disposition is Rework)

**Impact on OEE:**
All scrap and NC quantities are fed into the Quality component of the OEE calculation for the relevant machine and shift.

### 1.5 Shift Performance Summary

At the end of each shift (or on demand), the Production module generates a shift performance summary:
- Total good production vs target (by machine, by part, by operation)
- OEE components for the shift
- Total scrap quantity and scrap rate %
- Top rejection reasons
- Employee-wise production totals (used for incentive calculation)
- Downtime incidents and durations

Summaries aggregate to daily, weekly, and monthly performance reports.

### 1.6 Incentive Computation

Production-based incentives are calculated automatically from the production slip data and fed into the payroll engine.

**Incentive Configuration:**
The Company Admin configures tiered incentive rules in the HR module (connected to the Production module). Rules are defined at the intersection of: Part + Operation + Machine + Quantity Threshold.

**Example Rule:** For Part A, Operation = Drilling, Machine = M001, produce 100 units = ₹50 incentive; produce 120 units = ₹75 incentive.

**Incentive Calculation:**
At payroll processing time:
1. The system reads all production slips for the employee for the payroll period
2. Applies the applicable incentive rules
3. Sums up the total incentive amount
4. Passes it to the payroll engine as an earnings component

Incentive amounts are visible in the payslip and in the Incentive Report per employee.

### 1.7 Production Reports

| Report | Description |
|---|---|
| OEE Report | Availability, Performance, Quality, and OEE% by machine, shift, and period |
| Production Summary | Units produced vs target by shift, machine, employee, and date |
| Scrap & NC Report | Rejection quantities by reason, part, machine, and period |
| Incentive Report | Incentive payouts per employee for the payroll period |
| Downtime Analysis | Downtime by machine, reason, and duration |
| Shift Comparison Report | Side-by-side shift performance |
| Employee Productivity Report | Good units per employee per shift/period |

---

## 2. Module 6 — Machine Maintenance

### 2.1 Module Overview

The Machine Maintenance module ensures maximum equipment uptime through systematic preventive maintenance scheduling, rapid breakdown response, and spare parts management. It is the primary contributor to the OEE Availability factor in the Production module.

The module depends on the Masters module (Machine Master, Shift Master) and integrates bidirectionally with the Production module (downtime durations flow to OEE) and the Vendor Management module (low spare parts stock triggers purchase requests).

### 2.2 Preventive Maintenance (PM)

**PM Schedule Configuration:**
Each machine is assigned a preventive maintenance schedule that defines:

| Field | Notes |
|---|---|
| PM Type | Periodic / Meter-Based / Calendar-Based |
| Frequency | Daily / Weekly / Fortnightly / Monthly / Quarterly / Annual |
| Meter Trigger | For meter-based PM: hours, cycles, or km threshold |
| Estimated Duration | How long the PM task is expected to take (used in OEE planned downtime) |
| Assigned Technician / Team | Default responsible party |
| Checklist | Ordered list of tasks to be performed (check oil level, clean filters, tighten bolts, etc.) |
| Spare Parts Required | Items from Inventory needed for this PM |
| Next Due Date | Auto-calculated based on frequency and last completion date |

**Auto-Generation of PM Tasks:**
When the "Auto-generate PM tasks" system control is enabled, the system automatically creates PM task records as their due dates approach (configurable lead time, e.g., 7 days before due). These tasks appear in the maintenance dashboard for the assigned technician.

**PM Execution Workflow:**
1. Technician receives notification of upcoming PM task
2. Opens the task on mobile
3. Executes checklist step by step; marks each step complete
4. Records spare parts consumed (deducted from inventory automatically)
5. Uploads completion evidence (photo, report)
6. Marks task as complete; actual duration recorded
7. Next PM date auto-updated

**PM Task States:** Upcoming → Due → In Progress → Completed → Overdue

### 2.3 Breakdown Management

**Breakdown Report:**
Any person (operator, supervisor, technician) can report a machine breakdown from the mobile app. When a breakdown is reported:

1. Breakdown record created with: machine, reported by, start time, description, IOT reason code (from IOT Reason Master)
2. **Downtime counter starts immediately** — this duration is the Availability loss recorded in OEE
3. Maintenance supervisor notified via push notification
4. Technician assigned to the breakdown

**Breakdown Resolution Workflow:**
1. **Start** — Technician acknowledges and begins work; actual start time recorded
2. **Observe & Diagnose** — Technician records observations; root cause identified
3. **Log Parts** — Spare parts consumed recorded (deducted from inventory)
4. **Resolve** — Machine repaired; technician marks as resolved
5. **Complete** — Supervisor verifies and closes the breakdown; **downtime counter stops**

**Breakdown Metrics Tracked:**
- Total downtime per machine (cumulative)
- MTTR (Mean Time To Repair): average time from breakdown report to resolution
- MTBF (Mean Time Between Failures): average running time between breakdowns
- Breakdown frequency by machine, IOT reason, department, and time period

**Escalation:**
If a breakdown is not acknowledged within a configurable time window, it escalates to the maintenance manager. If not resolved within another window, it escalates to the plant manager.

### 2.4 Spare Parts Management

**Spare Parts Inventory:**
Spare parts are a subset of the Item Master (type = Spare Part) and are tracked in the Inventory module. The Machine Maintenance module provides the contextual view: which spare parts are linked to which machines, and which parts are consumed in PM and breakdown activities.

**Spare Parts Reorder Alerts:**
When a spare part's stock falls below its reorder point (configured in the Item Master), the system generates:
- A low-stock alert to the maintenance and stores managers
- Optionally: an automatic draft Purchase Requisition in the Vendor Management module

**Machine-Spare Part Mapping:**
Each machine record in the Machine Master links to its required spare parts, with recommended quantities to keep in stock. This drives the stores manager to maintain appropriate spare part inventory levels.

### 2.5 OEE Contribution — Availability Factor

The Machine Maintenance module is the sole source of data for the Availability component of OEE:

**Downtime Sources:**
1. **Unplanned Breakdown:** Reported and recorded in Breakdown Management; duration automatically measured
2. **Planned PM Downtime:** The PM schedule's estimated duration is counted as planned downtime (not penalised in OEE Availability since it is planned — this is configurable)
3. **Shift Planned Downtime:** Breaks and planned stoppages configured in the Shift Master

**Availability Calculation:**
> Availability = (Scheduled Time − Total Unplanned Downtime) ÷ Scheduled Time

The Production module reads this value per machine per shift when computing OEE.

### 2.6 Maintenance Reports

| Report | Description |
|---|---|
| PM Completion Report | Completed, pending, and overdue PM tasks by machine and period |
| Breakdown Report | All breakdowns with duration, reason, and resolution time |
| MTTR Report | Mean Time To Repair by machine and period |
| MTBF Report | Mean Time Between Failures by machine |
| Downtime Analysis | Total downtime by machine, IOT reason, and department |
| Spare Parts Consumption Report | Parts used in PM and breakdown activities |
| Machine Health Report | Overall health score per machine (based on breakdown frequency and PM compliance) |

---

## 3. Sub-Module — Calibration Management

### 3.1 Module Overview

The Calibration Management sub-module is an extension of Machine Maintenance designed for facilities that require instrument and equipment calibration compliance — particularly those certified to ISO 9001, 21 CFR Part 11, IATF 16949, or other quality standards that mandate traceable measurement system accuracy.

Calibration management ensures that all measuring instruments and test equipment used in production and quality control are maintained within their specified accuracy limits, with a complete, immutable audit trail of every calibration event.

### 3.2 Instrument / Equipment Master

Each instrument or piece of equipment requiring calibration is registered in the Calibration Equipment Master:

| Field | Notes |
|---|---|
| Equipment ID | Unique identifier |
| Equipment Name | Common name (e.g., Vernier Calliper, Pressure Gauge, Hardness Tester) |
| Make & Model | Manufacturer name and model |
| Serial Number | Instrument serial number |
| Location | Where this instrument is physically used/stored |
| Range | Measurement range (e.g., 0–150 mm) |
| Least Count / Resolution | Minimum measurable increment |
| Accuracy Required | Required accuracy level (as per drawing or standard) |
| Calibration Frequency | Monthly / Quarterly / Semi-Annual / Annual |
| Last Calibration Date | |
| Next Calibration Due Date | Auto-calculated from frequency and last calibration |
| Calibration Standard | Reference standard used (internal or external agency) |
| Calibration Agency | External lab name if applicable |
| Acceptance Criteria | Pass/fail tolerance limits |

### 3.3 Calibration Schedule & Auto-Generation

The system automatically generates calibration tasks based on each instrument's configured frequency:

- Tasks are created a configurable number of days before the due date (default: 14 days)
- Overdue escalation alerts are sent at configurable intervals: 7 days overdue, 14 days overdue, 30 days overdue
- The calibration due report shows all instruments sorted by urgency (overdue first, then due soon)

### 3.4 Calibration Execution & Results Recording

**Calibration Record Fields:**
- Calibration Number (from No Series), date
- Instrument reference
- Calibrator (person conducting calibration)
- Reference standard used and its traceability number
- Environmental conditions at time of calibration (temperature, humidity)

**Measurement Points:**
For each calibration, multiple measurement points are recorded:

| Column | Notes |
|---|---|
| Nominal (Reference) | Expected reading at this measurement point |
| As-Found Reading | Actual reading before any adjustment |
| As-Found Error | Difference between nominal and as-found |
| Adjustment Made | Description of any correction applied |
| As-Left Reading | Actual reading after adjustment |
| As-Left Error | Final error after correction |
| Within Tolerance? | Pass / Fail at this point |

The system computes whether each measurement point is within the configured acceptance criteria and flags failures automatically.

### 3.5 Pass / Fail / Conditional Disposition

After all measurement points are recorded, the overall calibration result is determined:

| Result | Meaning | Action |
|---|---|---|
| **Pass** | All measurement points within tolerance | Instrument is cleared for use; calibration sticker due date updated |
| **Conditional Pass** | Measurement points within tolerance but degrading trend observed | Instrument cleared but flagged for early review; shortened recalibration interval applied |
| **Fail** | One or more measurement points outside tolerance | Instrument is placed on hold; out-of-tolerance process triggered |

### 3.6 Out-of-Tolerance Handling

When a calibration result is Fail:

1. The instrument is automatically flagged as **"Out of Tolerance — Hold"**
2. All production and quality records that used this instrument since the last valid calibration are flagged for review (retrospective impact assessment)
3. A non-conformance report (NCR) is auto-generated and linked to the calibration record
4. The instrument is sent for repair or replacement
5. Retrospective review determines whether any product made with this instrument must be re-inspected or recalled

This retrospective impact assessment process is a key compliance requirement for regulated industries (pharma, medical devices, automotive).

### 3.7 Audit Trail & Electronic Signatures

**Immutable Audit Trail:**
Every action on a calibration record — creation, reading entry, result determination, approval, recall — is logged with timestamp and user identity. No entry can be deleted or modified after posting.

**Electronic Signatures (21 CFR Part 11):**
For regulated industries, calibration records require electronic signature by the calibrator and the reviewing quality manager. The system supports:
- Signature capture (typed name + password re-entry for authentication)
- Signed record is locked and cannot be modified
- Signature manifest: who signed, what they signed, when

### 3.8 Calibration Reports

| Report | Description |
|---|---|
| Calibration Due Report | All instruments sorted by next due date; overdue highlighted |
| Calibration History Report | All calibration events for selected instruments and period |
| Calibration Certificate | Formatted certificate for each completed calibration (PDF) |
| Out-of-Tolerance Report | All failed calibrations with impact assessment status |
| Instrument Status Dashboard | At-a-glance status of all instruments: Valid / Due / Overdue / On Hold |

---

## 4. Quality Management Module

### 4.1 Module Overview

The Quality Management module provides structured quality control across the inbound, in-process, and outbound stages of manufacturing. It supports non-conformance management, corrective and preventive actions (CAPA), and document control — the core pillars of ISO 9001 compliance.

The Quality module integrates with Inventory (GRN triggers incoming inspection), Production (in-process inspections linked to production orders), Vendor Management (quality rejections feed vendor performance scores), and Calibration Management (instruments used for inspection are tracked).

### 4.2 Incoming Quality Control (IQC)

**IQC Trigger:**
When a GRN is created in Inventory and the Quality module is active, the system automatically creates an inspection request for the received goods.

**IQC Inspection Process:**
1. Inspector assigned to the inspection request
2. Inspection plan selected (a pre-configured sampling plan for this item category)
3. Inspector records results: sample size, accepted units, rejected units, rejection reasons
4. Overall lot disposition: Accept / Reject / Conditional Accept (use with deviation)
5. Accepted units released to store; rejected units placed in quarantine

**Inspection Plan:**
Each item or item category has a configured inspection plan defining:
- Sampling method: 100% inspection or statistical sampling (AQL-based)
- Critical, major, and minor defect criteria
- Acceptance Quality Level (AQL) percentages

**IQC Rejection:**
Rejected lots trigger a vendor return process in Vendor Management and are counted against the vendor's quality performance score.

### 4.3 In-Process Quality Control (IPQC)

In-process inspections are triggered at defined stages of the production process.

**IPQC Configuration:**
- Control points are defined per part, per operation, or per machine
- Inspection frequency: every N units, every hour, or at operator's discretion
- Inspection parameters: dimensions, surface quality, visual characteristics, functional tests
- Acceptance criteria per parameter

**IPQC Record:**
- Machine, operator, part, shift
- Sample size and sample readings
- Pass/fail per parameter
- Disposition: Accept / Rework / Scrap
- Linked to production slip

### 4.4 Final / Outgoing Quality Control (FQC)

FQC is the last quality gate before finished goods are shipped to customers.

**FQC Inspection:**
- Triggered when finished goods are completed and ready for dispatch
- Linked to a sales order or shipment plan
- Comprehensive inspection against customer specifications
- Certificate of conformance generated on passing

**Customer-Specific Inspection Plans:**
For key customers, dedicated inspection plans with customer-specific criteria are configured and applied when their orders are being shipped.

### 4.5 Non-Conformance Management (NCR)

**NCR Creation:**
A Non-Conformance Report (NCR) is raised whenever a product, process, or material fails to meet a specified requirement. NCRs can be raised from IQC, IPQC, FQC, production operators, or independently.

**NCR Fields:**
- NCR Number, date
- Detection point: Incoming / In-Process / Final / Customer complaint
- Item/part and quantity affected
- Defect description with photo attachments
- Severity: Critical / Major / Minor
- Root cause (filled during investigation)
- Immediate containment action taken
- Disposition: Reject / Rework / Use As Is (with deviation approval)

**NCR Workflow:**
1. NCR raised → assigned to quality engineer
2. Immediate containment: quarantine affected goods
3. Root cause analysis completed
4. Disposition determined and approved
5. CAPA initiated if root cause indicates systemic issue
6. NCR closed with outcome documented

### 4.6 Corrective & Preventive Action (CAPA)

**CAPA** is initiated when an NCR's root cause reveals a systemic or recurring problem requiring a permanent fix.

**CAPA Record:**
- CAPA Number, linked NCR(s)
- Problem statement
- Root cause analysis method (5-Why, Fishbone, Fault Tree — selectable)
- Root cause conclusion
- Corrective action plan: actions, responsible persons, due dates
- Preventive action plan: changes to prevent recurrence
- Effectiveness verification: follow-up date and criteria for verifying the fix worked
- CAPA closure: verified as effective → closed; not effective → re-opened with new actions

**CAPA Tracking Dashboard:**
Open CAPAs with status, responsible person, and days overdue, visible to the quality manager.

### 4.7 Document Control

**Document Register:**
The Quality module includes a controlled document register for quality-related documents: SOPs (Standard Operating Procedures), Work Instructions, Control Plans, Inspection Plans, Forms.

**Document Control Features:**
- Version management: each document has a version number and effective date
- Review and approval workflow before a new version is released
- Obsolete versions are archived but accessible for audit trail
- Documents accessible to all relevant employees (read-only) from the ESS portal

### 4.8 Quality Reports & Metrics

| Report / Metric | Description |
|---|---|
| IQC Summary Report | Lot acceptance rate by vendor, item, and period |
| IPQC Defect Report | In-process defects by machine, operation, and shift |
| NCR Trend Report | NCR count by defect type, detection point, and period |
| CAPA Status Report | Open CAPAs by status, responsible person, and overdue count |
| Quality Cost Report | Cost of poor quality: scrap, rework, warranty, returns |
| First Pass Yield (FPY) | % of units produced that pass QC on the first attempt |
| Defect Density | Defects per unit by part and period |
| Vendor Quality Report | IQC rejection rates by vendor |

---

## 5. EHSS Module — Environmental Health, Safety & Sustainability

### 5.1 Module Overview

The Environmental Health, Safety & Sustainability (EHSS) module provides a structured framework for managing workplace safety, environmental compliance, and sustainability reporting in manufacturing facilities. It is designed to support compliance with OSHA, Factories Act, ISO 45001 (occupational health & safety), and ISO 14001 (environmental management).

### 5.2 Incident Management

**Incident Register:**
All workplace incidents — injuries, near-misses, property damage, environmental spills — are recorded in the Incident Register.

**Incident Types:** Injury (minor/major/fatality), Near-Miss, Unsafe Condition, Property Damage, Environmental Incident, First Aid Case.

**Incident Record Fields:**
- Incident Number, date, time, location (plant, department, specific area)
- Incident type and severity
- Description of what happened
- Persons involved (employees, contractors, visitors)
- Immediate first aid or emergency response taken
- Root cause investigation (5-Why or Fishbone)
- Corrective actions and responsible persons
- Lost Time Injury (LTI) flag and days lost
- Closure and review date

**Incident Investigation Workflow:**
Serious incidents trigger a formal investigation workflow with assigned investigators, interview records, and a written investigation report requiring management sign-off.

### 5.3 Risk Assessment

**Risk Register:**
A catalogue of all identified hazards in the facility with their assessed risk levels and controls.

**Risk Assessment Method:** Likelihood × Severity = Risk Rating (on configurable 5×5 matrix).

**Risk Record:**
- Hazard description and location
- Activity / process where hazard exists
- Existing controls in place
- Residual risk rating after controls
- Required additional controls
- Review date

**Job Safety Analysis (JSA):**
Step-by-step analysis of each task performed in the facility: task step → associated hazard → existing control → additional recommended control. JSAs are linked to work permit approvals.

### 5.4 Safety Observations & Near-Miss Reporting

**Safety Observation Cards (SOC):**
Any employee can submit a safety observation from the mobile app — a report of an unsafe condition or unsafe behaviour they noticed in the workplace.

**Near-Miss Reporting:**
Any employee can report a near-miss event (an incident that almost happened). Near-miss data is analysed to prevent future incidents.

**Safety Observation Dashboard:**
- Total observations by type (unsafe act vs unsafe condition)
- Top observation locations
- Trend over time
- % closed vs open observations

### 5.5 PPE & Safety Equipment Management

**PPE Inventory:**
The module tracks all PPE (hard hats, safety shoes, gloves, safety glasses, harnesses) issued to employees and visitors.

**PPE Issuance:**
- PPE issued to employee or visitor; linked to their record
- Quantity on hand tracked
- PPE condition tracked (New / Good / Worn / Condemned)

**PPE Compliance Tracking:**
- Required PPE per work area is configured
- System tracks whether each employee assigned to a work area has been issued the required PPE

**Safety Equipment Inspection:**
Fire extinguishers, first aid kits, emergency showers, and other safety equipment are registered with inspection frequencies. Inspection records are maintained in the module.

### 5.6 Environmental Monitoring

**Environmental Parameters:**
Air quality (particulate matter, VOC levels), water discharge quality, noise levels, and waste generation are tracked against regulatory limits.

**Monitoring Records:**
Each parameter has a configured monitoring frequency. Readings are entered periodically and the system flags any readings that exceed regulatory thresholds.

**Waste Management:**
- Types of waste generated (hazardous, non-hazardous, recyclable) tracked by quantity
- Disposal method and authorised disposal agency recorded
- Waste manifest records maintained for audits

### 5.7 Safety Training & Compliance Tracking

**Safety Training Register:**
All safety-related training (fire safety, first aid, chemical handling, working at heights, electrical safety) is tracked in the EHSS module alongside the general Training module.

**Training Compliance Matrix:**
For each role or work area, required safety training is configured. The matrix shows which employees are compliant (training current) and which are overdue.

**Contractor Safety Compliance:**
Contractors are required to have specific safety certificates before commencing work. The module tracks certificate validity and blocks work permit approval if certificates are expired.

### 5.8 EHSS Reports & Dashboards

**Safety Dashboard:**
- LTI (Lost Time Injury) frequency rate
- Near-miss count (month vs prior month)
- Open safety observations
- Overdue incident investigations
- Safety training compliance %

**Key Reports:**

| Report | Description |
|---|---|
| Incident Register | All incidents with status and severity |
| LTI Rate Report | Lost Time Injury rate by period |
| Near-Miss Analysis | Near-miss trends by location and type |
| Risk Register Report | All hazards with current risk ratings |
| PPE Compliance Report | PPE issuance and compliance by department |
| Safety Training Compliance | Overdue training by employee and category |
| Environmental Monitoring Report | Parameter readings vs limits |
| Waste Generation Report | Waste by type and disposal method |

---

## 6. CRM Module — Customer Relationship Management

### 6.1 Module Overview

The CRM module manages the sales pipeline from the initial contact with a prospect through lead qualification, opportunity development, quotation, and deal closure. It integrates with the Sales & Invoicing module so that a closed deal flows directly into an invoice without re-entering data.

The CRM module is designed for B2B sales in manufacturing — focused on managing relationships with industrial buyers, distributors, and procurement managers.

### 6.2 Contact & Account Management

**Account (Company):**
A company (potential customer or existing customer) in the CRM. Fields: Company name, industry, size, location, website, category (Prospect / Customer / Partner), primary contact.

**Contact (Individual):**
A person at a company. Fields: Name, designation, phone, email, relationship (decision-maker / influencer / technical / finance). Multiple contacts per account.

**Account 360° View:**
From the account record: all contacts, all interactions, all opportunities, linked quotations, linked invoices, and outstanding balance (from Finance module). A complete history of the relationship in one screen.

### 6.3 Lead Management

**Lead:**
An initial enquiry or potential opportunity that has not yet been qualified.

**Lead Fields:**
- Lead Number, creation date
- Source: Website enquiry / Trade show / Referral / Cold outreach / Inbound call
- Lead owner (assigned sales executive)
- Company name, contact person, phone, email
- Product / service of interest
- Estimated value
- Lead status: New / Contacted / Qualified / Disqualified

**Lead Qualification:**
A lead is evaluated and either converted to an Opportunity (if qualified) or marked as Disqualified (with reason). On conversion, an Account and Contact are created if they don't already exist.

### 6.4 Opportunity Pipeline

**Opportunity:**
A qualified business possibility with a defined scope, value, and decision timeline.

**Opportunity Fields:**
- Opportunity Number, linked Account and Contact
- Opportunity Name (descriptive)
- Product / service scope
- Expected Close Date
- Estimated Value
- Probability (%)
- Stage: Prospecting → Needs Analysis → Proposal → Negotiation → Closed Won / Closed Lost
- Competitor(s) identified
- Win/Loss reason (on closure)

**Pipeline Dashboard:**
A visual Kanban-style or funnel view of all open opportunities by stage. Shows total pipeline value per stage and weighted pipeline (probability-adjusted value).

**Forecasting:**
Monthly and quarterly sales forecast derived from opportunity probability × estimated value, aggregated by sales executive and team.

### 6.5 Activity & Communication Tracking

**Activity Types:** Call log, Email, Meeting, Site visit, Demo, Follow-up task.

Each activity is logged against an Account, Contact, Lead, or Opportunity:
- Date and time
- Duration (for calls and meetings)
- Participants
- Notes / outcome
- Next action and due date

**Activity Feed:**
A chronological activity feed on each account and opportunity record showing all interactions, notes, and communication history.

**Task & Reminder:**
Sales executives can create follow-up tasks with due dates. Overdue tasks surface in the CRM dashboard and send push notifications.

### 6.6 Quotation Integration

When an opportunity reaches the Proposal stage, a quotation is created in the Sales & Invoicing module and linked to the opportunity. The quotation number is visible on the opportunity record.

When the quotation is accepted and converted to a sales invoice, the CRM opportunity is automatically updated to "Closed Won" and the linked Account is promoted to "Customer" status in both CRM and the Customer Master in Sales & Invoicing.

### 6.7 CRM Reports & Dashboards

| Report / View | Description |
|---|---|
| Pipeline Summary | Opportunities by stage with total values |
| Sales Forecast | Weighted pipeline by month / quarter |
| Lead Conversion Report | Lead source analysis and conversion rates |
| Win/Loss Report | Closed opportunities by outcome and reason |
| Activity Report | Number of calls, meetings, emails per sales executive |
| Account Engagement Report | Last interaction date per account; dormant accounts flagged |
| Quota vs Actual | Sales executive performance vs target |

---

## 7. Project Management Module

### 7.1 Module Overview

The Project Management module enables manufacturing companies to manage engineering projects, expansion projects, customer project deliveries, and internal improvement initiatives. It provides structured phase/milestone tracking, task management, resource allocation, and cost tracking.

The module integrates with HR (resource availability and utilisation), Finance (project costs and billing), Vendor Management (procurement for project materials), and Inventory (material requisitions for project needs).

### 7.2 Project Setup & Structure

**Project Record:**

| Field | Notes |
|---|---|
| Project Code | Unique identifier |
| Project Name | Descriptive title |
| Project Type | Customer Delivery / Internal / Capex / R&D |
| Customer | Linked from Customer Master (for customer projects) |
| Project Manager | Assigned from Employee Master |
| Start Date / End Date | Planned duration |
| Budget | Approved project budget |
| Priority | High / Medium / Low |
| Status | Planning / Active / On Hold / Completed / Cancelled |
| Description / Scope | Free-text scope statement |

**Project Structure — WBS (Work Breakdown Structure):**
Projects are broken down into Phases → Work Packages → Tasks. The hierarchy can be as flat or as deep as the project requires.

### 7.3 Task & Work Package Management

**Work Package:**
A grouping of related tasks within a project phase. Each work package has a responsible person, estimated effort, and budget allocation.

**Task:**
The lowest-level unit of work:

| Field | Notes |
|---|---|
| Task Name | Short description |
| Work Package / Phase | Parent grouping |
| Assigned To | Employee(s) responsible |
| Start Date / Due Date | |
| Estimated Hours | |
| Actual Hours Logged | Via timesheet entry |
| Priority | High / Medium / Low |
| Status | Not Started / In Progress / Review / Completed / Blocked |
| Blockers | Free-text description of what is blocking progress |
| Attachments | Drawings, specifications, reference documents |
| Dependencies | Which tasks must be completed before this one can start |

**Kanban Board:**
Tasks can be viewed in a Kanban board grouped by status: Not Started / In Progress / Review / Completed. Drag-and-drop status updates are supported.

**Gantt View:**
Tasks and milestones are displayed on a Gantt chart with dependency lines. The critical path is highlighted.

### 7.4 Resource Management

**Resource Allocation:**
Each task assigns an employee. The system checks the employee's availability (based on their allocation on other tasks and their standard working hours from HR) and warns if they are over-allocated.

**Timesheet:**
Employees log hours against project tasks daily. Timesheets feed actual cost calculations (hours × loaded cost rate) and project progress calculations.

**Resource Utilisation Report:**
Shows each employee's allocation across projects for a selected period: allocated hours, actual hours logged, utilisation %.

### 7.5 Milestone & Timeline Tracking

**Milestones:**
Key decision points or deliverables in the project (e.g., Design Freeze, First Article Approval, Customer Sign-Off). Milestones have a defined due date, responsible owner, and completion criteria.

**Milestone Dashboard:**
- Upcoming milestones (next 30 days)
- Overdue milestones
- % of milestones completed on time (for all active projects)

**Schedule Health:**
The system computes schedule variance for each active project: Planned Progress vs Actual Progress. Projects falling behind schedule are flagged on the project dashboard.

### 7.6 Project Cost Tracking

**Budget vs Actual:**
For each project, the system tracks:
- Approved budget (by work package or category)
- Committed costs (approved POs and resource allocations)
- Actual costs incurred (invoiced vendor costs + timesheet-derived labour costs)
- Remaining budget

**Cost Categories:**
Labour (from timesheets), Materials (from inventory issues and vendor POs), Subcontractor costs (from vendor invoices), Other expenses.

**Cost Overrun Alerts:**
When actual + committed costs exceed a configurable % of the budget (e.g., 80% consumed), the project manager and finance controller are notified.

### 7.7 Project Reports & Dashboards

**Project Dashboard:**
- Total active projects and their health status (On Track / At Risk / Delayed)
- Upcoming milestones
- Budget utilisation across all projects
- Resource utilisation heat map

| Report | Description |
|---|---|
| Project Status Report | Phase-wise progress, milestone status, budget summary |
| Gantt Chart Export | Printable Gantt chart with all tasks and milestones |
| Resource Utilisation Report | Employee allocation and actual hours by project |
| Budget vs Actual Report | Cost breakdown by category and work package |
| Timesheet Summary | Hours logged by employee and project |
| Project Portfolio View | All projects with health, % complete, and budget status |

---

## 8. Cross-Module Integration Summary

This section provides a consolidated view of all significant data flows between modules across the entire Avy ERP platform.

| Data Flow | Source Module | Destination Module | Trigger |
|---|---|---|---|
| Gate punch timestamps → attendance records | Security | HR — Attendance | Employee gate scan |
| Production good quantities → incentive amounts | Production | HR — Payroll | Payroll run |
| Salary payable entries → GL | HR — Payroll | Finance | Payroll disbursement |
| Machine downtime durations → Availability % | Machine Maintenance | Production — OEE | Breakdown close |
| PM planned stoppages → planned downtime | Machine Maintenance | Production — OEE | PM schedule |
| Spare part low stock → draft PO | Machine Maintenance | Vendor Management | Stock below reorder |
| Pre-registrations → expected visitor list | Visitor Management | Security | Day start |
| ASN data → gate verification manifest | Vendor Management | Security | ASN creation |
| GRN confirmed → stock level update | Vendor Management (GRN) | Inventory | GRN posting |
| GRN confirmed → payable entry | Vendor Management (GRN) | Finance | GRN posting |
| Sales invoice created → receivable entry | Sales & Invoicing | Finance | Invoice confirmation |
| Invoice line item → stock outward | Sales & Invoicing | Inventory | Invoice dispatch |
| Shift timing → planned production time window | Masters | Machine Maintenance | OEE calculation |
| Item data → PO / Invoice / Stock | Masters | Inventory + Vendor + Sales | Item selection |
| IQC rejection → vendor performance score | Quality Management | Vendor Management | Inspection close |
| IQC release → stock available | Quality Management | Inventory | Inspection pass |
| Calibration fail → retrospective product review | Calibration | Quality Management | Fail disposition |
| Incident reports → CAPA | EHSS | Quality Management | Serious incident |
| CRM won opportunity → customer record | CRM | Sales & Invoicing | Deal closure |
| Project material request → inventory | Project Management | Inventory | Task material need |
| Project labour cost → budget actual | HR Timesheet | Project Management | Timesheet approval |
| Production order requirements → material request | Production | Inventory | Order release |
| Quality NCR → vendor return | Quality Management | Vendor Management | NCR disposition: Reject |

---

*This is Part 5 of 5 — the final document in the Avy ERP Master PRD series.*

---

**Document Control**

| Field | Value |
|---|---|
| Product | Avy ERP |
| Company | Avyren Technologies |
| Part | 5 of 5 — Production, Maintenance, Calibration, Quality, EHSS, CRM & Project Management |
| Version | 2.0 |
| Date | April 2026 |
| Status | Final Draft |
| Classification | Confidential — Internal Use Only |

---

## PRD Series Summary

| Part | Title | Key Content |
|---|---|---|
| **PRD-001** | Platform Foundation, Vision & Architecture | Vision, target market, system architecture, multi-tenancy, authentication (MFA, JWT), tenant onboarding, company configuration |
| **PRD-002** | Platform Capabilities | RBAC, Feature Toggles, subscription model, offline-first architecture, analytics & reporting, platform interfaces, integration strategy, NFRs |
| **PRD-003** | HR, Security & Visitor Management | Full HRMS (recruitment to F&F), Security (gate attendance, goods verification), Visitor Management (lifecycle, safety, evacuation) |
| **PRD-004** | Sales, Inventory, Vendor & Finance | Sales & Invoicing (GST engine), Inventory Management, Vendor Management & Procurement, Finance & Accounting, Masters |
| **PRD-005** | Production, Maintenance, Quality & More | Production (OEE, incentives), Machine Maintenance, Calibration, Quality Management (CAPA), EHSS, CRM, Project Management |
