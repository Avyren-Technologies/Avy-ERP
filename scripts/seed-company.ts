#!/usr/bin/env npx tsx
// ============================================================
// Seed Company Script — Creates test companies via the onboard API
//
// Mirrors the full 17-step Tenant Onboarding Wizard payload
// exactly as defined in tenant.validators.ts / tenant.types.ts.
//
// Usage:
//   npx tsx scripts/seed-company.ts
//   npx tsx scripts/seed-company.ts --count 3
//   npx tsx scripts/seed-company.ts --multi-location
//   npx tsx scripts/seed-company.ts --count 5 --multi-location
//
// Environment variables (or use flags):
//   API_URL          — default http://localhost:3030/api/v1
//   ADMIN_EMAIL      — super admin email
//   ADMIN_PASSWORD   — super admin password
// ============================================================

// ── CLI Argument Parsing ──────────────────────────────────────

const args = process.argv.slice(2);

function getArg(name: string, fallback: string): string {
  const idx = args.indexOf(`--${name}`);
  if (idx !== -1 && args[idx + 1]) return args[idx + 1];
  return fallback;
}

function hasFlag(name: string): boolean {
  return args.includes(`--${name}`);
}

if (hasFlag('help') || hasFlag('h')) {
  console.log(`
  Seed Company — Create test companies via the onboard API

  Usage:
    npx tsx scripts/seed-company.ts [options]

  Options:
    --count N          Number of companies to create (default: 1)
    --multi-location   Create 3 locations per company instead of 1
    --api-url URL      API base URL (default: http://localhost:3030/api/v1)
    --email EMAIL      Super admin email (or set ADMIN_EMAIL env var)
    --password PASS    Super admin password (or set ADMIN_PASSWORD env var)
    --help, -h         Show this help
  `);
  process.exit(0);
}

const API_URL = getArg('api-url', process.env.API_URL || 'http://localhost:3030/api/v1');
const ADMIN_EMAIL = getArg('email', process.env.ADMIN_EMAIL || 'admin@avyerp.com');
const ADMIN_PASSWORD = getArg('password', process.env.ADMIN_PASSWORD || 'admin123');
const COUNT = parseInt(getArg('count', '1'), 10);
const MULTI_LOCATION = hasFlag('multi-location');

// ── Unique ID & Fake Data Generators ──────────────────────────

let counter = 0;

function uid(): string {
  counter++;
  const ts = Date.now().toString(36);
  const rnd = Math.random().toString(36).slice(2, 5);
  return `${ts}${rnd}${counter}`;
}

function pickRandom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomDigits(len: number): string {
  let s = '';
  for (let i = 0; i < len; i++) s += Math.floor(Math.random() * 10);
  return s;
}

function randomLetter(): string {
  return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)];
}

function randomPhone(): string {
  return `98${randomDigits(8)}`;
}

function randomPin(): string {
  return `${Math.floor(100000 + Math.random() * 899999)}`;
}

/** Indian PAN format: AAAPX9999X */
function fakePAN(): string {
  return `${randomLetter()}${randomLetter()}${randomLetter()}P${randomLetter()}${randomDigits(4)}${randomLetter()}`;
}

/** Indian TAN format: AAAA99999A */
function fakeTAN(): string {
  return `${randomLetter()}${randomLetter()}${randomLetter()}${randomLetter()}${randomDigits(5)}${randomLetter()}`;
}

/** Indian GSTIN format: 2-digit state code + PAN + 1Z + digit */
function fakeGSTIN(pan: string, stateCode: string): string {
  return `${stateCode.padStart(2, '0')}${pan}1Z${randomDigits(1)}`;
}

/** Fake CIN: U99999MH2020PTC999999 */
function fakeCIN(): string {
  return `U${randomDigits(5)}MH${2015 + Math.floor(Math.random() * 10)}PTC${randomDigits(6)}`;
}

/** PF registration: MH/PNE/99999/999 */
function fakePFReg(): string {
  return `MH/PNE/${randomDigits(5)}/${randomDigits(3)}`;
}

/** ESI code: 31-00-999999-999-9999 */
function fakeESI(): string {
  return `31-00-${randomDigits(6)}-${randomDigits(3)}-${randomDigits(4)}`;
}

/** PT registration */
function fakePTReg(): string {
  return `PTEC/${randomDigits(8)}`;
}

/** LWFR number */
function fakeLWFR(): string {
  return `LWF/${randomDigits(6)}`;
}

// ── API Helpers ───────────────────────────────────────────────

async function login(): Promise<string> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Login failed (${res.status}): ${body}`);
  }

  const json = await res.json() as any;
  const token =
    json.data?.tokens?.accessToken ||
    json.data?.accessToken ||
    json.data?.token ||
    json.accessToken ||
    json.token;
  if (!token) throw new Error(`No token in login response: ${JSON.stringify(json)}`);
  return token;
}

async function onboard(token: string, payload: any): Promise<any> {
  const res = await fetch(`${API_URL}/platform/tenants/onboard`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  const json = await res.json() as any;
  if (!res.ok) {
    throw new Error(`Onboard failed (${res.status}): ${json.error || json.message || JSON.stringify(json)}`);
  }
  return json;
}

// ── Reference Data ────────────────────────────────────────────

const INDIAN_STATES_WITH_CODES = [
  { name: 'Maharashtra', code: '27', stdCode: '022' },
  { name: 'Karnataka', code: '29', stdCode: '080' },
  { name: 'Tamil Nadu', code: '33', stdCode: '044' },
  { name: 'Gujarat', code: '24', stdCode: '079' },
  { name: 'Delhi', code: '07', stdCode: '011' },
  { name: 'Uttar Pradesh', code: '09', stdCode: '0522' },
  { name: 'Rajasthan', code: '08', stdCode: '0141' },
  { name: 'West Bengal', code: '19', stdCode: '033' },
];

const CITIES: Record<string, { city: string; district: string }[]> = {
  Maharashtra: [
    { city: 'Mumbai', district: 'Mumbai Suburban' },
    { city: 'Pune', district: 'Pune' },
    { city: 'Nagpur', district: 'Nagpur' },
    { city: 'Nashik', district: 'Nashik' },
  ],
  Karnataka: [
    { city: 'Bengaluru', district: 'Bengaluru Urban' },
    { city: 'Mysuru', district: 'Mysuru' },
    { city: 'Hubli', district: 'Dharwad' },
    { city: 'Mangaluru', district: 'Dakshina Kannada' },
  ],
  'Tamil Nadu': [
    { city: 'Chennai', district: 'Chennai' },
    { city: 'Coimbatore', district: 'Coimbatore' },
    { city: 'Madurai', district: 'Madurai' },
    { city: 'Salem', district: 'Salem' },
  ],
  Gujarat: [
    { city: 'Ahmedabad', district: 'Ahmedabad' },
    { city: 'Surat', district: 'Surat' },
    { city: 'Vadodara', district: 'Vadodara' },
    { city: 'Rajkot', district: 'Rajkot' },
  ],
  Delhi: [
    { city: 'New Delhi', district: 'New Delhi' },
    { city: 'Dwarka', district: 'South West Delhi' },
    { city: 'Rohini', district: 'North West Delhi' },
    { city: 'Saket', district: 'South Delhi' },
  ],
  'Uttar Pradesh': [
    { city: 'Noida', district: 'Gautam Buddh Nagar' },
    { city: 'Lucknow', district: 'Lucknow' },
    { city: 'Agra', district: 'Agra' },
    { city: 'Varanasi', district: 'Varanasi' },
  ],
  Rajasthan: [
    { city: 'Jaipur', district: 'Jaipur' },
    { city: 'Jodhpur', district: 'Jodhpur' },
    { city: 'Udaipur', district: 'Udaipur' },
    { city: 'Kota', district: 'Kota' },
  ],
  'West Bengal': [
    { city: 'Kolkata', district: 'Kolkata' },
    { city: 'Howrah', district: 'Howrah' },
    { city: 'Durgapur', district: 'Paschim Bardhaman' },
    { city: 'Siliguri', district: 'Darjeeling' },
  ],
};

const INDUSTRIES = [
  'Manufacturing', 'IT', 'Automotive', 'Pharma', 'Textiles',
  'Electronics', 'Food Processing', 'Heavy Engineering', 'Steel & Metal',
  'Chemicals', 'CNC Machining', 'Plastics', 'Logistics',
];

const FACILITY_TYPES = [
  'Manufacturing Plant', 'Assembly Unit', 'Warehouse / Distribution',
  'R&D Centre', 'Factory', 'Service Centre',
];

const DESIGNATIONS = [
  'Plant Head', 'Production Manager', 'Quality Manager',
  'Maintenance Head', 'HR Manager', 'Shift Supervisor',
];

const DEPARTMENTS = [
  'Production', 'Quality', 'Maintenance', 'Human Resources',
  'Finance', 'IT', 'Operations', 'Logistics',
];

// ── Location Builder ──────────────────────────────────────────

function buildLocation(
  index: number,
  isHQ: boolean,
  pan: string,
  companyUid: string,
) {
  const stateInfo = INDIAN_STATES_WITH_CODES[index % INDIAN_STATES_WITH_CODES.length];
  const cityInfo = pickRandom(CITIES[stateInfo.name] || CITIES['Maharashtra']);
  const gstin = fakeGSTIN(pan, stateInfo.code);

  return {
    // Required
    name: isHQ ? 'Head Office' : `Plant ${index} — ${cityInfo.city}`,
    code: isHQ ? 'HQ' : `PLT-${index}`,
    facilityType: isHQ ? 'Head Office' : pickRandom(FACILITY_TYPES),
    status: 'Active',
    isHQ,
    // Address
    addressLine1: `${Math.floor(100 + Math.random() * 900)} Industrial Area, Sector ${Math.floor(1 + Math.random() * 50)}`,
    addressLine2: `Near ${pickRandom(['NH Highway', 'Railway Station', 'MIDC', 'SEZ Gate', 'IT Park'])}`,
    city: cityInfo.city,
    district: cityInfo.district,
    state: stateInfo.name,
    pin: randomPin(),
    country: 'India',
    stdCode: stateInfo.stdCode,
    // GST
    gstin,
    stateGST: stateInfo.code,
    // Contact person
    contactName: isHQ ? 'Rajesh Kumar' : `${pickRandom(['Anil', 'Suresh', 'Priya', 'Meera', 'Vikram'])} ${pickRandom(['Sharma', 'Patel', 'Singh', 'Reddy', 'Nair'])}`,
    contactDesignation: isHQ ? 'Operations Head' : pickRandom(DESIGNATIONS),
    contactEmail: `loc-${index}-${companyUid}@test.local`,
    contactCountryCode: '+91',
    contactPhone: randomPhone(),
    // Geo-fencing
    geoEnabled: index === 0, // enable for HQ only
    geoLocationName: index === 0 ? `${cityInfo.city} HQ Campus` : undefined,
    geoLat: index === 0 ? `${18 + Math.random() * 10}` : undefined,
    geoLng: index === 0 ? `${72 + Math.random() * 8}` : undefined,
    geoRadius: 200,
    geoShape: 'circle',
  };
}

// ── Payload Builder (all 17 wizard steps) ─────────────────────

function buildPayload(multiLocation: boolean) {
  const id = uid();
  const companyCode = `TEST-${id}`.toUpperCase();
  const displayName = `Test Corp ${id}`;
  const industry = pickRandom(INDUSTRIES);

  // Statutory identifiers (all unique per run)
  const pan = fakePAN();
  const tan = fakeTAN();
  const companyStateInfo = pickRandom(INDIAN_STATES_WITH_CODES);
  const companyCityInfo = pickRandom(CITIES[companyStateInfo.name] || CITIES['Maharashtra']);
  const gstin = fakeGSTIN(pan, companyStateInfo.code);

  // Admin user
  const adminEmail = `admin-${id}@test.local`;
  const adminUsername = `admin_${id}`;

  // Locations
  const locations = multiLocation
    ? [
        buildLocation(0, true, pan, id),
        buildLocation(1, false, pan, id),
        buildLocation(2, false, pan, id),
      ]
    : [buildLocation(0, true, pan, id)];

  const payload = {
    // ── Step 1: Company Identity ────────────────────────────
    identity: {
      displayName,
      legalName: `${displayName} Private Limited`,
      businessType: 'Private Limited (Pvt. Ltd.)',
      industry,
      companyCode,
      shortName: `TC${id.slice(-6).toUpperCase()}`,
      incorporationDate: `${2015 + Math.floor(Math.random() * 10)}-${String(1 + Math.floor(Math.random() * 12)).padStart(2, '0')}-${String(1 + Math.floor(Math.random() * 28)).padStart(2, '0')}`,
      employeeCount: pickRandom(['1-50', '50-100', '100-200', '200-500']),
      cin: fakeCIN(),
      website: `https://www.${companyCode.toLowerCase().replace(/[^a-z0-9]/g, '')}.test`,
      emailDomain: `${companyCode.toLowerCase().replace(/[^a-z0-9]/g, '')}.test`,
      logoUrl: '',
      wizardStatus: 'Active',
    },

    // ── Step 2: Statutory & Tax ─────────────────────────────
    statutory: {
      pan,
      tan,
      gstin,
      pfRegNo: fakePFReg(),
      esiCode: fakeESI(),
      ptReg: fakePTReg(),
      lwfrNo: fakeLWFR(),
      rocState: companyStateInfo.name,
    },

    // ── Step 3: Address ─────────────────────────────────────
    address: {
      registered: {
        line1: `${Math.floor(100 + Math.random() * 900)}, ${pickRandom(['MG Road', 'Station Road', 'Industrial Lane', 'Commerce Avenue', 'Corporate Park'])}`,
        line2: `${pickRandom(['Sector', 'Block', 'Wing', 'Tower'])} ${Math.floor(1 + Math.random() * 20)}`,
        city: companyCityInfo.city,
        district: companyCityInfo.district,
        state: companyStateInfo.name,
        pin: randomPin(),
        country: 'India',
        stdCode: companyStateInfo.stdCode,
      },
      sameAsRegistered: !multiLocation,
      corporate: multiLocation
        ? {
            line1: `${Math.floor(100 + Math.random() * 900)}, Corporate Hub`,
            line2: `Floor ${Math.floor(1 + Math.random() * 20)}, Tower ${pickRandom(['A', 'B', 'C'])}`,
            city: companyCityInfo.city,
            district: companyCityInfo.district,
            state: companyStateInfo.name,
            pin: randomPin(),
            country: 'India',
            stdCode: companyStateInfo.stdCode,
          }
        : undefined,
    },

    // ── Step 4: Fiscal & Calendar ───────────────────────────
    fiscal: {
      fyType: 'apr-mar',
      fyCustomStartMonth: '',
      fyCustomEndMonth: '',
      payrollFreq: 'Monthly',
      cutoffDay: 'Last Working Day',
      disbursementDay: '1st',
      weekStart: 'Monday',
      timezone: 'IST UTC+5:30',
      workingDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    },

    // ── Step 5: Preferences ─────────────────────────────────
    preferences: {
      currency: 'INR — ₹',
      language: 'English',
      dateFormat: 'DD/MM/YYYY',
      numberFormat: 'Indian (2,00,000)',
      timeFormat: '12-hour (AM/PM)',
      indiaCompliance: true,
      multiCurrency: false,
      ess: true,
      mobileApp: true,
      webApp: true,
      systemApp: false,
      aiChatbot: false,
      eSign: false,
      biometric: false,
      bankIntegration: false,
      razorpayEnabled: false,
      razorpayKeyId: '',
      razorpayKeySecret: '',
      razorpayWebhookSecret: '',
      razorpayAccountNumber: '',
      razorpayAutoDisbursement: false,
      razorpayTestMode: true,
      emailNotif: true,
      whatsapp: false,
    },

    // ── Step 6: Backend Endpoint ────────────────────────────
    endpoint: {
      endpointType: 'default' as const,
      customBaseUrl: '',
    },

    // ── Step 7: Configuration Strategy ──────────────────────
    strategy: {
      multiLocationMode: multiLocation,
      locationConfig: 'common' as const,
    },

    // ── Step 8: Locations Master ────────────────────────────
    locations,

    // ── Step 9-10: Commercial (common mode) ─────────────────
    commercial: {
      selectedModuleIds: ['hr', 'security', 'masters'],
      customModulePricing: {} as Record<string, number>,
      userTier: 'starter',
      customUserLimit: '',
      customTierPrice: '',
      billingType: 'monthly',
      trialDays: 14,
    },

    // ── Step 11: Key Contacts ───────────────────────────────
    contacts: [
      {
        name: `Anand Verma`,
        designation: 'HR Director',
        department: 'Human Resources',
        type: 'Primary',
        email: `hr-${id}@test.local`,
        countryCode: '+91',
        mobile: randomPhone(),
        linkedin: `https://linkedin.com/in/anand-verma-${id}`,
      },
      {
        name: `Priya Mehta`,
        designation: 'Finance Controller',
        department: 'Finance',
        type: 'Finance Contact',
        email: `finance-${id}@test.local`,
        countryCode: '+91',
        mobile: randomPhone(),
        linkedin: '',
      },
      {
        name: `Ravi Shankar`,
        designation: 'IT Manager',
        department: 'IT',
        type: 'IT Contact',
        email: `it-${id}@test.local`,
        countryCode: '+91',
        mobile: randomPhone(),
        linkedin: '',
      },
    ],

    // ── Step 12: Shifts & Time ──────────────────────────────
    shifts: {
      dayStartTime: '06:00',
      dayEndTime: '22:00',
      weeklyOffs: ['Sunday'],
      items: [
        {
          name: 'General Shift',
          fromTime: '09:00',
          toTime: '18:00',
          noShuffle: true,
          downtimeSlots: [
            { type: 'Lunch Break', duration: '60' },
            { type: 'Tea Break', duration: '15' },
          ],
        },
        {
          name: 'Morning Shift',
          fromTime: '06:00',
          toTime: '14:00',
          noShuffle: false,
          downtimeSlots: [
            { type: 'Lunch Break', duration: '30' },
            { type: 'Tea Break', duration: '15' },
          ],
        },
        {
          name: 'Afternoon Shift',
          fromTime: '14:00',
          toTime: '22:00',
          noShuffle: false,
          downtimeSlots: [
            { type: 'Lunch Break', duration: '30' },
            { type: 'Tea Break', duration: '15' },
          ],
        },
      ],
    },

    // ── Step 13: Number Series ──────────────────────────────
    noSeries: [
      { code: 'EMP', linkedScreen: 'Employee Onboarding', description: 'Employee ID sequence', prefix: 'EMP-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'ATT', linkedScreen: 'Attendance', description: 'Attendance record numbering', prefix: 'ATT-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'LV', linkedScreen: 'Leave Management', description: 'Leave request numbering', prefix: 'LV-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'PAY', linkedScreen: 'Payroll', description: 'Payroll run numbering', prefix: 'PAY-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'WO', linkedScreen: 'Work Order', description: 'Work order numbering', prefix: 'WO-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'MR', linkedScreen: 'Material Request', description: 'Material request numbering', prefix: 'MR-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'GRN', linkedScreen: 'GRN', description: 'Goods receipt note numbering', prefix: 'GRN-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'NC', linkedScreen: 'Non-Conformance', description: 'Non-conformance numbering', prefix: 'NC-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'MT', linkedScreen: 'Maintenance Ticket', description: 'Maintenance ticket numbering', prefix: 'MT-', suffix: '', numberCount: 6, startNumber: 1 },
      { code: 'GP', linkedScreen: 'Gate Pass', description: 'Gate pass numbering', prefix: 'GP-', suffix: '', numberCount: 6, startNumber: 1 },
    ],

    // ── Step 14: IOT Reasons ────────────────────────────────
    iotReasons: [
      { reasonType: 'Machine Idle', reason: 'No Operator', description: 'Operator not available at station', department: 'Production', planned: false, duration: '' },
      { reasonType: 'Machine Idle', reason: 'Material Shortage', description: 'Raw material not available', department: 'Logistics', planned: false, duration: '' },
      { reasonType: 'Machine Idle', reason: 'Power Failure', description: 'Unplanned power outage', department: 'Maintenance', planned: false, duration: '' },
      { reasonType: 'Machine Idle', reason: 'Tool Change', description: 'Scheduled tool change', department: 'Production', planned: true, duration: '30' },
      { reasonType: 'Machine Alarm', reason: 'Scheduled Maintenance', description: 'Preventive maintenance activity', department: 'Maintenance', planned: true, duration: '120' },
      { reasonType: 'Machine Alarm', reason: 'Breakdown', description: 'Unexpected machine failure', department: 'Maintenance', planned: false, duration: '' },
      { reasonType: 'Machine Idle', reason: 'Quality Hold', description: 'Quality issue, awaiting inspection', department: 'Quality', planned: false, duration: '' },
      { reasonType: 'Machine Idle', reason: 'Changeover', description: 'Product or mould changeover', department: 'Production', planned: true, duration: '45' },
    ],

    // ── Step 15: System Controls ────────────────────────────
    controls: {
      ncEditMode: false,
      loadUnload: true,
      cycleTime: true,
      payrollLock: true,
      leaveCarryForward: true,
      overtimeApproval: true,
      mfa: false,
    },

    // ── Step 16: Users & Access ─────────────────────────────
    users: [
      {
        fullName: `Admin ${id}`,
        username: adminUsername,
        password: 'Test@12345',
        role: 'Company Admin',
        email: adminEmail,
        mobile: randomPhone(),
        department: 'Management',
      },
    ],
  };

  return {
    payload,
    meta: { companyCode, displayName, adminEmail, adminUsername, password: 'Test@12345' },
  };
}

// ── Main ──────────────────────────────────────────────────────

async function main() {
  console.log('\n=== Seed Company Script ===');
  console.log(`  API:            ${API_URL}`);
  console.log(`  Admin:          ${ADMIN_EMAIL}`);
  console.log(`  Count:          ${COUNT}`);
  console.log(`  Multi-location: ${MULTI_LOCATION}\n`);

  // 1. Login
  console.log('Logging in as super admin...');
  const token = await login();
  console.log('Authenticated.\n');

  // 2. Create companies
  const results: { companyCode: string; displayName: string; adminEmail: string; password: string }[] = [];

  for (let i = 0; i < COUNT; i++) {
    const { payload, meta } = buildPayload(MULTI_LOCATION);
    const label = `[${i + 1}/${COUNT}]`;

    try {
      console.log(`${label} Creating "${meta.displayName}" (${meta.companyCode})...`);
      const res = await onboard(token, payload);
      const companyId = res.data?.id || res.data?.company?.id || '—';
      console.log(`${label} Created! ID: ${companyId}`);
      results.push(meta);
    } catch (err: any) {
      console.error(`${label} FAILED: ${err.message}`);
    }
  }

  // 3. Summary
  if (results.length > 0) {
    console.log('\n=== Summary ===\n');
    console.log(
      'Company Code'.padEnd(24) + '| ' +
      'Display Name'.padEnd(31) + '| ' +
      'Admin Email'.padEnd(35) + '| ' +
      'Password'
    );
    console.log('-'.repeat(120));
    for (const r of results) {
      console.log(
        `${r.companyCode.padEnd(24)}| ${r.displayName.padEnd(31)}| ${r.adminEmail.padEnd(35)}| ${r.password}`
      );
    }
    console.log(`\nTotal created: ${results.length}/${COUNT}`);
  }
}

main().catch((err) => {
  console.error('\nFatal error:', err.message);
  process.exit(1);
});
