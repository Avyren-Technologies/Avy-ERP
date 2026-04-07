# Super Admin — Make All Company Detail Sections Editable

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up all non-functional "Manage" buttons on the super-admin Company Detail screen so contacts, locations, shifts, number series, IoT reasons, and users can be edited inline via the existing edit modal pattern.

**Architecture:** The backend already supports all sections via `PATCH /platform/companies/:companyId/sections/:sectionKey`. The frontend `CompanyDetailEditModal` handles 8 section forms — we add 6 more for array-type sections (contacts, shifts, noSeries, iotReasons, users, locations). Each array section uses a list+inline-form pattern inside the modal. The "Manage" buttons on `CompanyDetailScreen` are wired to `openEdit()` with the correct section key and data.

**Tech Stack:** React, TypeScript, Tailwind CSS, React Query (mutations via `useUpdateCompanySection`)

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `web-system-app/src/features/super-admin/CompanyDetailEditModal.tsx` | Modify | Add 6 new section form renderers + array helpers + section titles + buildInitialForm/buildPayload cases |
| `web-system-app/src/features/super-admin/CompanyDetailScreen.tsx` | Modify | Wire 6 "Manage" buttons with `onClick={() => openEdit(...)}` |

> **Mobile parity:** After web is complete, replicate to `mobile-app/src/features/super-admin/company-detail-edit-modal.tsx` and `company-detail-screen.tsx` following the same patterns.

---

## Shared Array-Section Pattern

All array sections follow the same UI pattern inside the modal:
1. A scrollable list of existing items, each with an **Edit** (pencil) and **Delete** (trash) icon button
2. When editing an item, it expands inline with form fields and Save/Cancel buttons
3. A sticky **"+ Add Item"** button at the bottom
4. Save sends the full array to the backend (DELETE ALL + RECREATE on server)

Helper state pattern for each array section:
```typescript
const [items, setItems] = useState<Item[]>(initialItems);
const [editingIdx, setEditingIdx] = useState<number | null>(null); // null = not editing, -1 = adding new
const [draft, setDraft] = useState<Partial<Item>>({});
```

---

### Task 1: Add Contacts Section Form

**Files:**
- Modify: `web-system-app/src/features/super-admin/CompanyDetailEditModal.tsx`
- Modify: `web-system-app/src/features/super-admin/CompanyDetailScreen.tsx`

- [ ] **Step 1: Add section title and imports**

In `SECTION_TITLES`, add:
```typescript
contacts: 'Key Contacts',
```

Add `Plus, Trash2, Edit3` to the lucide-react imports (check if already present — `Edit3` may need adding).

- [ ] **Step 2: Add ContactsForm component**

Add before the `flattenAddressData` function:

```typescript
function ContactsForm({
    form,
    setField,
}: {
    form: Record<string, any>;
    setField: (key: string, value: any) => void;
}) {
    const items: any[] = form._items ?? [];
    const [editIdx, setEditIdx] = useState<number | null>(null);
    const [draft, setDraft] = useState<Record<string, any>>({});

    const emptyContact = { name: '', type: 'Primary', email: '', mobile: '', countryCode: '+91', designation: '', department: '', linkedin: '' };

    const startEdit = (idx: number) => {
        setEditIdx(idx);
        setDraft(idx === -1 ? { ...emptyContact } : { ...items[idx] });
    };

    const cancelEdit = () => { setEditIdx(null); setDraft({}); };

    const saveItem = () => {
        if (!draft.name || !draft.email || !draft.mobile) return;
        const next = [...items];
        if (editIdx === -1) next.push({ ...draft });
        else if (editIdx !== null) next[editIdx] = { ...draft };
        setField('_items', next);
        cancelEdit();
    };

    const removeItem = (idx: number) => {
        setField('_items', items.filter((_, i) => i !== idx));
    };

    return (
        <div className="space-y-3">
            {items.map((c, i) => (
                <div key={i} className="p-3 rounded-xl border border-neutral-100 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-800/50">
                    {editIdx === i ? (
                        <div className="space-y-3">
                            <TwoCol>
                                <FormInput label="Name" value={draft.name ?? ''} onChange={(v) => setDraft(p => ({ ...p, name: v }))} required />
                                <FormSelect label="Type" value={draft.type ?? ''} onChange={(v) => setDraft(p => ({ ...p, type: v }))} options={['Primary', 'Secondary', 'Technical', 'Billing', 'HR', 'Other']} />
                            </TwoCol>
                            <TwoCol>
                                <FormInput label="Email" value={draft.email ?? ''} onChange={(v) => setDraft(p => ({ ...p, email: v }))} required />
                                <FormInput label="Mobile" value={draft.mobile ?? ''} onChange={(v) => setDraft(p => ({ ...p, mobile: v }))} required placeholder="10-15 digits" />
                            </TwoCol>
                            <TwoCol>
                                <FormInput label="Designation" value={draft.designation ?? ''} onChange={(v) => setDraft(p => ({ ...p, designation: v }))} />
                                <FormInput label="Department" value={draft.department ?? ''} onChange={(v) => setDraft(p => ({ ...p, department: v }))} />
                            </TwoCol>
                            <FormInput label="LinkedIn" value={draft.linkedin ?? ''} onChange={(v) => setDraft(p => ({ ...p, linkedin: v }))} placeholder="https://linkedin.com/in/..." />
                            <div className="flex gap-2 pt-1">
                                <button type="button" onClick={saveItem} className="px-4 py-2 rounded-lg bg-primary-600 text-white text-xs font-bold hover:bg-primary-700 transition-colors">Save</button>
                                <button type="button" onClick={cancelEdit} className="px-4 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 text-xs font-bold text-neutral-600 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">Cancel</button>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center justify-between">
                            <div className="min-w-0">
                                <p className="text-sm font-bold text-primary-950 dark:text-white truncate">{c.name}</p>
                                <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">{c.email} · {c.mobile}</p>
                            </div>
                            <div className="flex items-center gap-1 flex-shrink-0">
                                <button type="button" onClick={() => startEdit(i)} className="p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-400 transition-colors"><Edit3 size={13} /></button>
                                <button type="button" onClick={() => removeItem(i)} className="p-1.5 rounded-lg hover:bg-danger-50 dark:hover:bg-danger-900/30 text-neutral-400 hover:text-danger-600 transition-colors"><Trash2 size={13} /></button>
                            </div>
                        </div>
                    )}
                </div>
            ))}
            {editIdx === -1 ? (
                <div className="p-3 rounded-xl border border-primary-200 dark:border-primary-800 bg-primary-50/50 dark:bg-primary-900/20 space-y-3">
                    <TwoCol>
                        <FormInput label="Name" value={draft.name ?? ''} onChange={(v) => setDraft(p => ({ ...p, name: v }))} required />
                        <FormSelect label="Type" value={draft.type ?? ''} onChange={(v) => setDraft(p => ({ ...p, type: v }))} options={['Primary', 'Secondary', 'Technical', 'Billing', 'HR', 'Other']} />
                    </TwoCol>
                    <TwoCol>
                        <FormInput label="Email" value={draft.email ?? ''} onChange={(v) => setDraft(p => ({ ...p, email: v }))} required />
                        <FormInput label="Mobile" value={draft.mobile ?? ''} onChange={(v) => setDraft(p => ({ ...p, mobile: v }))} required placeholder="10-15 digits" />
                    </TwoCol>
                    <TwoCol>
                        <FormInput label="Designation" value={draft.designation ?? ''} onChange={(v) => setDraft(p => ({ ...p, designation: v }))} />
                        <FormInput label="Department" value={draft.department ?? ''} onChange={(v) => setDraft(p => ({ ...p, department: v }))} />
                    </TwoCol>
                    <FormInput label="LinkedIn" value={draft.linkedin ?? ''} onChange={(v) => setDraft(p => ({ ...p, linkedin: v }))} placeholder="https://linkedin.com/in/..." />
                    <div className="flex gap-2 pt-1">
                        <button type="button" onClick={saveItem} className="px-4 py-2 rounded-lg bg-primary-600 text-white text-xs font-bold hover:bg-primary-700 transition-colors">Add Contact</button>
                        <button type="button" onClick={cancelEdit} className="px-4 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 text-xs font-bold text-neutral-600 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">Cancel</button>
                    </div>
                </div>
            ) : (
                <button type="button" onClick={() => startEdit(-1)} className="w-full py-2.5 rounded-xl border-2 border-dashed border-neutral-200 dark:border-neutral-700 text-xs font-bold text-neutral-500 hover:border-primary-300 hover:text-primary-600 transition-colors flex items-center justify-center gap-1.5">
                    <Plus size={14} /> Add Contact
                </button>
            )}
        </div>
    );
}
```

- [ ] **Step 3: Add buildInitialForm and buildPayload cases for contacts**

In `buildInitialForm`, add before `default`:
```typescript
case 'contacts':
    return { _items: (data.contacts ?? data._items ?? []).map((c: any) => ({
        name: c.name ?? '', type: c.type ?? 'Primary', email: c.email ?? '',
        mobile: c.mobile ?? '', countryCode: c.countryCode ?? '+91',
        designation: c.designation ?? '', department: c.department ?? '',
        linkedin: c.linkedin ?? '',
    })) };
```

In `buildPayload`, add before `default`:
```typescript
case 'contacts':
    return (form._items ?? []).map((c: any) => ({
        name: c.name, type: c.type, email: c.email, mobile: c.mobile,
        countryCode: c.countryCode || '+91', designation: c.designation || undefined,
        department: c.department || undefined, linkedin: c.linkedin || undefined,
    }));
```

- [ ] **Step 4: Add renderForm case for contacts**

In the `renderForm` switch, add before `default`:
```typescript
case 'contacts':
    return <ContactsForm form={form} setField={setField} />;
```

- [ ] **Step 5: Wire the Manage button in CompanyDetailScreen**

Find the Key Contacts section's `<EditButton label="Manage" />` and change to:
```typescript
<EditButton label="Manage" onClick={() => openEdit('contacts', { contacts })} />
```

- [ ] **Step 6: Type-check and verify**

```bash
cd web-system-app && npx tsc --noEmit
```

---

### Task 2: Add Shifts Section Form

**Files:**
- Modify: `web-system-app/src/features/super-admin/CompanyDetailEditModal.tsx`
- Modify: `web-system-app/src/features/super-admin/CompanyDetailScreen.tsx`

- [ ] **Step 1: Add section title**

In `SECTION_TITLES`:
```typescript
shifts: 'Shifts & Time',
```

- [ ] **Step 2: Add ShiftsForm component**

Uses the same array-editing pattern but with company-level fields (dayStartTime, dayEndTime, weeklyOffs) plus a shift items array.

```typescript
function ShiftsForm({
    form,
    setField,
}: {
    form: Record<string, any>;
    setField: (key: string, value: any) => void;
}) {
    const items: any[] = form._items ?? [];
    const [editIdx, setEditIdx] = useState<number | null>(null);
    const [draft, setDraft] = useState<Record<string, any>>({});
    const weeklyOffs: string[] = form.weeklyOffs ?? [];

    const emptyShift = { name: '', fromTime: '', toTime: '', noShuffle: false };

    const startEdit = (idx: number) => {
        setEditIdx(idx);
        setDraft(idx === -1 ? { ...emptyShift } : { ...items[idx] });
    };
    const cancelEdit = () => { setEditIdx(null); setDraft({}); };
    const saveItem = () => {
        if (!draft.name || !draft.fromTime || !draft.toTime) return;
        const next = [...items];
        if (editIdx === -1) next.push({ ...draft });
        else if (editIdx !== null) next[editIdx] = { ...draft };
        setField('_items', next);
        cancelEdit();
    };
    const removeItem = (idx: number) => setField('_items', items.filter((_, i) => i !== idx));
    const toggleOff = (day: string) => {
        setField('weeklyOffs', weeklyOffs.includes(day) ? weeklyOffs.filter(d => d !== day) : [...weeklyOffs, day]);
    };

    return (
        <div className="space-y-4">
            <TwoCol>
                <FormInput label="Day Start Time" value={form.dayStartTime ?? ''} onChange={(v) => setField('dayStartTime', v)} placeholder="HH:mm e.g. 06:00" />
                <FormInput label="Day End Time" value={form.dayEndTime ?? ''} onChange={(v) => setField('dayEndTime', v)} placeholder="HH:mm e.g. 22:00" />
            </TwoCol>
            <div>
                <p className="text-xs font-bold text-primary-900 dark:text-white mb-2">Weekly Offs</p>
                <div className="flex flex-wrap gap-2">
                    {ALL_DAYS.map(day => (
                        <button key={day} type="button" onClick={() => toggleOff(day)} className={cn(
                            'px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all select-none',
                            weeklyOffs.includes(day)
                                ? 'bg-primary-600 text-white border-primary-600 shadow-sm shadow-primary-500/20'
                                : 'bg-white dark:bg-neutral-900 text-neutral-700 dark:text-neutral-300 border-neutral-200 dark:border-neutral-700 hover:border-primary-300'
                        )}>{day.slice(0, 3)}</button>
                    ))}
                </div>
            </div>
            <div className="border-t border-neutral-100 dark:border-neutral-800 pt-4">
                <p className="text-xs font-bold text-primary-900 dark:text-white mb-3">Shift Definitions</p>
                <div className="space-y-3">
                    {items.map((sh, i) => (
                        <div key={i} className="p-3 rounded-xl border border-neutral-100 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-800/50">
                            {editIdx === i ? (
                                <div className="space-y-3">
                                    <FormInput label="Shift Name" value={draft.name ?? ''} onChange={(v) => setDraft(p => ({ ...p, name: v }))} required />
                                    <TwoCol>
                                        <FormInput label="From Time" value={draft.fromTime ?? ''} onChange={(v) => setDraft(p => ({ ...p, fromTime: v }))} placeholder="HH:mm" required />
                                        <FormInput label="To Time" value={draft.toTime ?? ''} onChange={(v) => setDraft(p => ({ ...p, toTime: v }))} placeholder="HH:mm" required />
                                    </TwoCol>
                                    <ToggleRow label="No Shuffle" value={draft.noShuffle ?? false} onToggle={(v) => setDraft(p => ({ ...p, noShuffle: v }))} />
                                    <div className="flex gap-2 pt-1">
                                        <button type="button" onClick={saveItem} className="px-4 py-2 rounded-lg bg-primary-600 text-white text-xs font-bold hover:bg-primary-700 transition-colors">Save</button>
                                        <button type="button" onClick={cancelEdit} className="px-4 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 text-xs font-bold text-neutral-600 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">Cancel</button>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-bold text-primary-950 dark:text-white">{sh.name}</p>
                                        <p className="text-xs text-neutral-500 font-mono">{sh.fromTime} – {sh.toTime}</p>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <button type="button" onClick={() => startEdit(i)} className="p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-400 transition-colors"><Edit3 size={13} /></button>
                                        <button type="button" onClick={() => removeItem(i)} className="p-1.5 rounded-lg hover:bg-danger-50 dark:hover:bg-danger-900/30 text-neutral-400 hover:text-danger-600 transition-colors"><Trash2 size={13} /></button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                    {editIdx === -1 ? (
                        <div className="p-3 rounded-xl border border-primary-200 dark:border-primary-800 bg-primary-50/50 dark:bg-primary-900/20 space-y-3">
                            <FormInput label="Shift Name" value={draft.name ?? ''} onChange={(v) => setDraft(p => ({ ...p, name: v }))} required />
                            <TwoCol>
                                <FormInput label="From Time" value={draft.fromTime ?? ''} onChange={(v) => setDraft(p => ({ ...p, fromTime: v }))} placeholder="HH:mm" required />
                                <FormInput label="To Time" value={draft.toTime ?? ''} onChange={(v) => setDraft(p => ({ ...p, toTime: v }))} placeholder="HH:mm" required />
                            </TwoCol>
                            <ToggleRow label="No Shuffle" value={draft.noShuffle ?? false} onToggle={(v) => setDraft(p => ({ ...p, noShuffle: v }))} />
                            <div className="flex gap-2 pt-1">
                                <button type="button" onClick={saveItem} className="px-4 py-2 rounded-lg bg-primary-600 text-white text-xs font-bold hover:bg-primary-700 transition-colors">Add Shift</button>
                                <button type="button" onClick={cancelEdit} className="px-4 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 text-xs font-bold text-neutral-600 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">Cancel</button>
                            </div>
                        </div>
                    ) : (
                        <button type="button" onClick={() => startEdit(-1)} className="w-full py-2.5 rounded-xl border-2 border-dashed border-neutral-200 dark:border-neutral-700 text-xs font-bold text-neutral-500 hover:border-primary-300 hover:text-primary-600 transition-colors flex items-center justify-center gap-1.5">
                            <Plus size={14} /> Add Shift
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
```

- [ ] **Step 3: Add buildInitialForm and buildPayload cases for shifts**

`buildInitialForm`:
```typescript
case 'shifts':
    return {
        dayStartTime: data.dayStartTime ?? '',
        dayEndTime: data.dayEndTime ?? '',
        weeklyOffs: data.weeklyOffs ?? [],
        _items: (data.shifts ?? data._items ?? []).map((s: any) => ({
            name: s.name ?? '', fromTime: s.fromTime ?? s.startTime ?? '',
            toTime: s.toTime ?? s.endTime ?? '', noShuffle: s.noShuffle ?? false,
        })),
    };
```

`buildPayload`:
```typescript
case 'shifts':
    return {
        dayStartTime: form.dayStartTime || undefined,
        dayEndTime: form.dayEndTime || undefined,
        weeklyOffs: form.weeklyOffs ?? [],
        items: (form._items ?? []).map((s: any) => ({
            name: s.name, fromTime: s.fromTime, toTime: s.toTime,
            noShuffle: s.noShuffle ?? false,
        })),
    };
```

- [ ] **Step 4: Add renderForm case and wire Manage button**

renderForm switch:
```typescript
case 'shifts':
    return <ShiftsForm form={form} setField={setField} />;
```

In CompanyDetailScreen, find Shifts & Time `<EditButton label="Manage" />` and change to:
```typescript
<EditButton label="Manage" onClick={() => openEdit('shifts', { dayStartTime: TENANT.dayStartTime, dayEndTime: TENANT.dayEndTime, weeklyOffs: TENANT.weeklyOffs ?? [], shifts })} />
```

- [ ] **Step 5: Type-check**

---

### Task 3: Add Number Series Section Form

**Files:** Same as above.

- [ ] **Step 1: Add section title**

```typescript
noSeries: 'Number Series',
```

- [ ] **Step 2: Add NoSeriesForm component**

Same array-edit pattern. Fields: code, linkedScreen, prefix, suffix, numberCount, startNumber, description.

- [ ] **Step 3: Add buildInitialForm and buildPayload**

`buildInitialForm`:
```typescript
case 'noSeries':
    return { _items: (data.noSeries ?? data._items ?? []).map((ns: any) => ({
        code: ns.code ?? '', linkedScreen: ns.linkedScreen ?? '', prefix: ns.prefix ?? '',
        suffix: ns.suffix ?? '', numberCount: ns.numberCount ?? 5, startNumber: ns.startNumber ?? 1,
        description: ns.description ?? '',
    })) };
```

`buildPayload`:
```typescript
case 'noSeries':
    return (form._items ?? []).map((ns: any) => ({
        code: ns.code, linkedScreen: ns.linkedScreen, prefix: ns.prefix,
        suffix: ns.suffix || undefined, numberCount: Number(ns.numberCount) || 5,
        startNumber: Number(ns.startNumber) || 1, description: ns.description || undefined,
    }));
```

- [ ] **Step 4: Wire renderForm + Manage button**

Find Number Series `<EditButton label="Manage" />` → `onClick={() => openEdit('noSeries', { noSeries })}`.

---

### Task 4: Add IoT Reasons Section Form

- [ ] **Step 1: Add section title**

```typescript
iotReasons: 'IOT Reasons',
```

- [ ] **Step 2: Add IotReasonsForm component**

Fields: reasonType (select: Machine Idle/Machine Alarm), reason, description, department, planned (toggle), duration.

- [ ] **Step 3: Add buildInitialForm and buildPayload**

- [ ] **Step 4: Wire renderForm + Manage button**

Find IOT Reasons `<EditButton label="Manage" />` → `onClick={() => openEdit('iotReasons', { iotReasons })}`.

---

### Task 5: Add Users Section Form (Additive Only)

- [ ] **Step 1: Add section title**

```typescript
users: 'Add Users',
```

- [ ] **Step 2: Add UsersForm component**

Unlike other sections, users are **additive only** (backend never deletes existing users). The form shows existing users as read-only and has an "Add User" form for new users only.

Fields for new user: fullName, username, email, password, role (select: COMPANY_ADMIN), mobile, department.

- [ ] **Step 3: Add buildInitialForm and buildPayload**

`buildInitialForm`:
```typescript
case 'users':
    return { _existingUsers: data.users ?? [], _newUsers: [] };
```

`buildPayload` — only sends new users:
```typescript
case 'users':
    return (form._newUsers ?? []).map((u: any) => ({
        fullName: u.fullName, username: u.username, email: u.email,
        password: u.password, role: u.role || 'COMPANY_ADMIN',
        mobile: u.mobile || undefined, department: u.department || undefined,
    }));
```

- [ ] **Step 4: Wire renderForm + Manage button**

Find Users & Access `<EditButton label="Manage" />` → `onClick={() => openEdit('users', { users })}`.

---

### Task 6: Add Locations Section Form

- [ ] **Step 1: Add section title**

```typescript
locations: 'Plants & Locations',
```

- [ ] **Step 2: Add LocationsForm component**

Most complex section. Each location has: name (req), code (req), facilityType (req), status, isHQ, address fields (line1, line2, city, district, state, pin, country, stdCode), gstin, contact fields (name, designation, email, phone), geo fields (enabled, lat, lng, radius).

Uses the same list+inline-edit pattern but the inline form is larger (collapsible sub-sections for address, contact, geo).

- [ ] **Step 3: Add buildInitialForm and buildPayload**

`buildInitialForm`:
```typescript
case 'locations':
    return { _items: (data.locations ?? data._items ?? []).map((loc: any) => ({
        name: loc.name ?? '', code: loc.code ?? '', facilityType: loc.facilityType ?? '',
        status: loc.status ?? 'Active', isHQ: loc.isHQ ?? false,
        addressLine1: loc.addressLine1 ?? '', addressLine2: loc.addressLine2 ?? '',
        city: loc.city ?? '', district: loc.district ?? '', state: loc.state ?? '',
        pin: loc.pin ?? '', country: loc.country ?? '', stdCode: loc.stdCode ?? '',
        gstin: loc.gstin ?? '', contactName: loc.contactName ?? '',
        contactDesignation: loc.contactDesignation ?? '', contactEmail: loc.contactEmail ?? '',
        contactPhone: loc.contactPhone ?? '', geoEnabled: loc.geoEnabled ?? false,
        geoLocationName: loc.geoLocationName ?? '', geoLat: loc.geoLat ?? '',
        geoLng: loc.geoLng ?? '', geoRadius: loc.geoRadius ?? 50,
    })) };
```

`buildPayload`:
```typescript
case 'locations':
    return (form._items ?? []).map((loc: any) => ({
        name: loc.name, code: loc.code, facilityType: loc.facilityType,
        status: loc.status || 'Active', isHQ: loc.isHQ ?? false,
        addressLine1: loc.addressLine1 || undefined, addressLine2: loc.addressLine2 || undefined,
        city: loc.city || undefined, district: loc.district || undefined,
        state: loc.state || undefined, pin: loc.pin || undefined,
        country: loc.country || undefined, stdCode: loc.stdCode || undefined,
        gstin: loc.gstin || undefined, contactName: loc.contactName || undefined,
        contactDesignation: loc.contactDesignation || undefined,
        contactEmail: loc.contactEmail || undefined, contactPhone: loc.contactPhone || undefined,
        geoEnabled: loc.geoEnabled ?? false, geoLocationName: loc.geoLocationName || undefined,
        geoLat: loc.geoLat || undefined, geoLng: loc.geoLng || undefined,
        geoRadius: loc.geoRadius ? Number(loc.geoRadius) : undefined,
    }));
```

- [ ] **Step 4: Wire renderForm + Manage button**

Find Plants & Locations `<EditButton label="Manage" />` → `onClick={() => openEdit('locations', { locations })}`.

---

### Task 7: Final Type-Check, Lint, and Test

- [ ] **Step 1: Type-check web app**
```bash
cd web-system-app && npx tsc --noEmit
```

- [ ] **Step 2: Lint**
```bash
cd web-system-app && pnpm lint
```

- [ ] **Step 3: Manual smoke test checklist**
- Open Company Detail for any company
- Click each "Manage" button — modal should open with correct data
- Add/edit/delete an item in each array section
- Save — should succeed and refresh data
- Verify contacts, shifts, number series, IoT reasons, locations all save correctly

---

### Task 8: Mobile App Parity

After web is validated, replicate changes to:
- `mobile-app/src/features/super-admin/company-detail-edit-modal.tsx` — add section forms
- `mobile-app/src/features/super-admin/company-detail-screen.tsx` — wire Manage buttons

Follow the exact same patterns but adapted for React Native (Pressable, View, Text, ScrollView, StyleSheet).
