/* eslint-disable better-tailwindcss/no-unknown-classes */
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import * as React from 'react';
import {
    KeyboardAvoidingView,
    Platform,
    Pressable,
    ScrollView,
    StyleSheet,
    Switch,
    TextInput,
    View,
} from 'react-native';
import Animated, {
    FadeIn,
    FadeInDown,
    FadeInUp,
    SlideInRight,
    SlideOutLeft,
} from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ChevronLeft, ChevronRight } from 'lucide-react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

import { Text } from '@/components/ui';
import colors from '@/components/ui/colors';
import { ConfirmModal, useConfirmModal } from '@/components/ui/confirm-modal';

// ============ CONSTANTS ============

const TOTAL_STEPS = 14;

const BUSINESS_TYPES = [
    'Private Limited (Pvt. Ltd.)',
    'Public Limited',
    'LLP',
    'Partnership',
    'Proprietorship',
    'Others',
];

const INDUSTRIES = [
    'IT', 'Manufacturing', 'BFSI', 'Healthcare', 'Retail',
    'Automotive', 'Pharma', 'Education', 'Steel & Metal',
    'Textiles', 'Plastics', 'Electronics', 'Food Processing',
    'Heavy Engineering', 'CNC Machining', 'Chemicals', 'Other',
];

const COMPANY_STATUSES = ['Draft', 'Pilot', 'Active', 'Inactive'];

const INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
    'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim',
    'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
    'West Bengal', 'Delhi', 'Jammu & Kashmir', 'Ladakh', 'Puducherry',
    'Chandigarh', 'Others',
];

const FY_OPTIONS = [
    { key: 'apr-mar', label: 'April – March', subtitle: 'Standard India FY' },
    { key: 'jan-dec', label: 'January – December', subtitle: 'Calendar year (global)' },
    { key: 'jul-jun', label: 'July – June', subtitle: 'Australia / NZ style' },
    { key: 'oct-sep', label: 'October – September', subtitle: 'Middle East / custom' },
];

const PAYROLL_FREQ = ['Monthly', 'Bi-Monthly', 'Weekly'];
const CUTOFF_DAY = ['Last Working Day', '25th', '1st of Next Month'];
const DISBURSEMENT_DAY = ['1st of Next Month', 'Last Day', '28th'];
const WEEK_STARTS = ['Monday', 'Sunday'];

const TIMEZONES = [
    'IST UTC+5:30', 'UTC+0', 'EST UTC-5', 'PST UTC-8',
    'GST UTC+4', 'SGT UTC+8', 'AEST UTC+10',
];

const CURRENCIES = ['INR — ₹', 'USD — $', 'GBP — £', 'EUR — €', 'AED — د.إ'];
const LANGUAGES = ['English', 'Hindi', 'Tamil', 'Kannada', 'Telugu', 'Malayalam'];
const DATE_FORMATS = ['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'];
const NUMBER_FORMATS = ['Indian (2,00,000)', 'International (200,000)'];
const TIME_FORMATS = ['12-hour (AM/PM)', '24-hour'];

const BRANCH_TYPES = [
    'Head Office', 'Regional Office', 'Satellite Office', 'Warehouse', 'Service Centre',
];

const CONTACT_TYPES = [
    'Primary', 'HR Contact', 'Finance Contact', 'IT Contact', 'Legal Contact', 'Operations Contact',
];

const PLANT_TYPES = [
    'Manufacturing Plant', 'Assembly Unit', 'Warehouse/Distribution',
    'R&D Centre', 'Head Office', 'Regional Office', 'Service Centre',
];

const PLANT_STATUSES = ['Active', 'Inactive', 'Under Construction'];

const NO_SERIES_SCREENS = [
    'Employee Onboarding', 'Attendance', 'Leave Management', 'Payroll',
    'Work Order', 'Production Order', 'Andon Ticket', 'Quality Check',
    'Non-Conformance', 'Maintenance Ticket', 'Preventive Maintenance',
    'GRN', 'Material Request', 'Gate Pass', 'Stock Transfer',
    'Sales Invoice', 'Purchase Order', 'Delivery Challan', 'Goods Return',
];

const IOT_REASON_TYPES = ['Machine Idle', 'Machine Alarm'];

const DOWNTIME_TYPES = [
    'Scheduled Maintenance', 'Lunch Break', 'Changeover', 'Training',
    'Cleaning', 'Tea Break', 'Other',
];

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

// ============ FORM STATE TYPES ============

interface Branch {
    id: string;
    name: string;
    code: string;
    type: string;
    addressLine1: string;
    city: string;
    state: string;
    pin: string;
    contact: string;
    geoRadius: string;
}

interface Contact {
    id: string;
    name: string;
    designation: string;
    department: string;
    mobile: string;
    email: string;
    type: string;
    linkedin: string;
}

interface Plant {
    id: string;
    name: string;
    code: string;
    type: string;
    status: string;
    isHQ: boolean;
    gstin: string;
    stateGST: string;
    addressLine1: string;
    addressLine2: string;
    city: string;
    district: string;
    state: string;
    pin: string;
}

interface DowntimeSlot {
    id: string;
    type: string;
    duration: string;
}

interface Shift {
    id: string;
    name: string;
    fromTime: string;
    toTime: string;
    noShuffle: boolean;
    downtimeSlots: DowntimeSlot[];
}

interface NoSeriesItem {
    id: string;
    code: string;
    description: string;
    linkedScreen: string;
    prefix: string;
    suffix: string;
    numberCount: string;
    startNumber: string;
}

interface IOTReason {
    id: string;
    reasonType: string;
    reason: string;
    description: string;
    department: string;
    planned: boolean;
    duration: string;
}

interface UserItem {
    id: string;
    fullName: string;
    username: string;
    password: string;
    role: string;
    email: string;
    mobile: string;
    department: string;
}

// ============ REUSABLE FORM ATOMS ============

function FormLabel({ text, required }: { text: string; required?: boolean }) {
    return (
        <Text className="mb-1.5 font-inter text-xs font-bold text-primary-900 dark:text-primary-200">
            {text}
            {required && <Text className="text-danger-500"> *</Text>}
        </Text>
    );
}

function FormInput({
    label,
    placeholder,
    value,
    onChangeText,
    required,
    keyboardType = 'default',
    autoCapitalize = 'sentences',
    multiline = false,
    hint,
}: {
    label: string;
    placeholder: string;
    value: string;
    onChangeText: (t: string) => void;
    required?: boolean;
    keyboardType?: 'default' | 'email-address' | 'phone-pad' | 'number-pad' | 'url' | 'numeric';
    autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
    multiline?: boolean;
    hint?: string;
}) {
    return (
        <View style={styles.fieldWrap}>
            <FormLabel text={label} required={required} />
            <View style={[styles.fieldInput, multiline && { height: 80, alignItems: 'flex-start' }]}>
                <TextInput
                    style={[styles.textInput, multiline && { height: 70, textAlignVertical: 'top' }]}
                    placeholder={placeholder}
                    placeholderTextColor={colors.neutral[400]}
                    value={value}
                    onChangeText={onChangeText}
                    keyboardType={keyboardType}
                    autoCapitalize={autoCapitalize}
                    autoCorrect={false}
                    multiline={multiline}
                />
            </View>
            {hint && (
                <Text className="mt-1 font-inter text-[10px] text-neutral-400">{hint}</Text>
            )}
        </View>
    );
}

function ChipSelector({
    label,
    options,
    selected,
    onSelect,
    required,
    hint,
}: {
    label: string;
    options: string[];
    selected: string;
    onSelect: (v: string) => void;
    required?: boolean;
    hint?: string;
}) {
    return (
        <View style={styles.fieldWrap}>
            <FormLabel text={label} required={required} />
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                <View style={styles.chipRow}>
                    {options.map((opt) => (
                        <Pressable
                            key={opt}
                            onPress={() => onSelect(opt)}
                            style={[styles.chip, selected === opt && styles.chipActive]}
                        >
                            <Text
                                className={`font-inter text-xs font-semibold ${selected === opt ? 'text-white' : 'text-neutral-600'}`}
                            >
                                {opt}
                            </Text>
                        </Pressable>
                    ))}
                </View>
            </ScrollView>
            {hint && (
                <Text className="mt-1 font-inter text-[10px] text-neutral-400">{hint}</Text>
            )}
        </View>
    );
}

function MultiChipSelector({
    label,
    options,
    selected,
    onToggle,
}: {
    label: string;
    options: string[];
    selected: string[];
    onToggle: (v: string) => void;
}) {
    return (
        <View style={styles.fieldWrap}>
            <FormLabel text={label} />
            <View style={styles.chipGrid}>
                {options.map((opt) => {
                    const isSelected = selected.includes(opt);
                    return (
                        <Pressable
                            key={opt}
                            onPress={() => onToggle(opt)}
                            style={[styles.chip, isSelected && styles.chipActive]}
                        >
                            <Text
                                className={`font-inter text-xs font-semibold ${isSelected ? 'text-white' : 'text-neutral-600'}`}
                            >
                                {opt}
                            </Text>
                        </Pressable>
                    );
                })}
            </View>
        </View>
    );
}

function ToggleRow({
    label,
    subtitle,
    value,
    onToggle,
}: {
    label: string;
    subtitle?: string;
    value: boolean;
    onToggle: (v: boolean) => void;
}) {
    return (
        <View style={styles.toggleRow}>
            <View style={{ flex: 1, marginRight: 12 }}>
                <Text className="font-inter text-sm font-semibold text-primary-950">
                    {label}
                </Text>
                {subtitle && (
                    <Text className="mt-0.5 font-inter text-xs text-neutral-500" numberOfLines={2}>
                        {subtitle}
                    </Text>
                )}
            </View>
            <Switch
                value={value}
                onValueChange={onToggle}
                trackColor={{ false: colors.neutral[200], true: colors.primary[400] }}
                thumbColor={value ? colors.primary[600] : colors.neutral[300]}
            />
        </View>
    );
}

function SectionCard({ children, title }: { children: React.ReactNode; title?: string }) {
    return (
        <View style={styles.sectionCard}>
            {title && (
                <Text className="mb-3 font-inter text-xs font-bold uppercase tracking-wider text-neutral-400">
                    {title}
                </Text>
            )}
            {children}
        </View>
    );
}

function RadioOption({
    label,
    subtitle,
    selected,
    onSelect,
    badge,
}: {
    label: string;
    subtitle?: string;
    selected: boolean;
    onSelect: () => void;
    badge?: string;
}) {
    return (
        <Pressable
            onPress={onSelect}
            style={[styles.radioOption, selected && styles.radioOptionActive]}
        >
            <View style={[styles.radioCircle, selected && styles.radioCircleActive]}>
                {selected && <View style={styles.radioInner} />}
            </View>
            <View style={{ flex: 1 }}>
                <Text
                    className={`font-inter text-sm font-semibold ${selected ? 'text-primary-700' : 'text-primary-950'}`}
                >
                    {label}
                </Text>
                {subtitle && (
                    <Text className="font-inter text-xs text-neutral-500">{subtitle}</Text>
                )}
            </View>
            {badge && (
                <View style={styles.recommendedBadge}>
                    <Text className="font-inter text-[10px] font-bold text-success-700">{badge}</Text>
                </View>
            )}
        </Pressable>
    );
}

function AddButton({ onPress, label }: { onPress: () => void; label: string }) {
    return (
        <Pressable onPress={onPress} style={styles.addButton}>
            <Svg width={16} height={16} viewBox="0 0 24 24">
                <Path d="M12 5v14M5 12h14" stroke={colors.primary[600]} strokeWidth="2.5" strokeLinecap="round" />
            </Svg>
            <Text className="font-inter text-sm font-semibold text-primary-600">{label}</Text>
        </Pressable>
    );
}

function DeleteButton({ onPress }: { onPress: () => void }) {
    return (
        <Pressable onPress={onPress} style={styles.deleteIconBtn}>
            <Svg width={16} height={16} viewBox="0 0 24 24">
                <Path
                    d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"
                    stroke={colors.danger[500]}
                    strokeWidth="1.8"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </Svg>
        </Pressable>
    );
}

// ============ STEP INDICATOR ============

function StepIndicator({
    currentStep,
    totalSteps,
}: {
    currentStep: number;
    totalSteps: number;
}) {
    const scrollRef = React.useRef<ScrollView>(null);

    React.useEffect(() => {
        // Scroll to keep active step visible
        const offset = Math.max(0, (currentStep - 3) * 40);
        scrollRef.current?.scrollTo({ x: offset, animated: true });
    }, [currentStep]);

    return (
        <View style={styles.stepIndicatorWrap}>
            <ScrollView
                ref={scrollRef}
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.stepIndicatorContent}
            >
                {Array.from({ length: totalSteps }, (_, i) => {
                    const stepNum = i + 1;
                    const isActive = stepNum === currentStep;
                    const isCompleted = stepNum < currentStep;
                    return (
                        <React.Fragment key={i}>
                            <View
                                style={[
                                    styles.stepDot,
                                    isActive && styles.stepDotActive,
                                    isCompleted && styles.stepDotCompleted,
                                ]}
                            >
                                {isCompleted ? (
                                    <Svg width={10} height={10} viewBox="0 0 24 24">
                                        <Path
                                            d="M5 12l5 5L20 7"
                                            stroke="#fff"
                                            strokeWidth="3"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </Svg>
                                ) : (
                                    <Text
                                        className={`font-inter text-[10px] font-bold ${isActive ? 'text-white' : 'text-neutral-400'}`}
                                    >
                                        {stepNum}
                                    </Text>
                                )}
                            </View>
                            {i < totalSteps - 1 && (
                                <View
                                    style={[styles.stepLine, isCompleted && styles.stepLineCompleted]}
                                />
                            )}
                        </React.Fragment>
                    );
                })}
            </ScrollView>
            <View style={styles.stepProgress}>
                <View
                    style={[
                        styles.stepProgressFill,
                        { width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` },
                    ]}
                />
            </View>
        </View>
    );
}

// ============ STEP 1 — COMPANY IDENTITY ============

function Step1Identity({
    form,
    setForm,
}: {
    form: Step1Form;
    setForm: (f: Partial<Step1Form>) => void;
}) {
    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <SectionCard title="Company Logo">
                <Pressable style={styles.logoUpload}>
                    <View style={styles.logoPlaceholder}>
                        <Svg width={28} height={28} viewBox="0 0 24 24">
                            <Path
                                d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"
                                stroke={colors.primary[400]}
                                strokeWidth="1.8"
                                fill="none"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </Svg>
                    </View>
                    <View style={styles.logoUploadText}>
                        <Text className="font-inter text-sm font-semibold text-primary-600">
                            Upload Company Logo
                        </Text>
                        <Text className="mt-0.5 font-inter text-xs text-neutral-400">
                            PNG, JPG or SVG · Max 2MB · 200×200px Recommended
                        </Text>
                    </View>
                </Pressable>
            </SectionCard>

            <SectionCard title="Core Identity">
                <FormInput
                    label="Display Name"
                    placeholder="e.g. Apex Manufacturing"
                    value={form.displayName}
                    onChangeText={(v) => setForm({ displayName: v })}
                    required
                />
                <FormInput
                    label="Legal / Registered Name"
                    placeholder="Full name as per incorporation documents"
                    value={form.legalName}
                    onChangeText={(v) => setForm({ legalName: v })}
                    required
                />
                <ChipSelector
                    label="Business Type"
                    options={BUSINESS_TYPES}
                    selected={form.businessType}
                    onSelect={(v) => setForm({ businessType: v })}
                    required
                />
                <ChipSelector
                    label="Nature of Industry"
                    options={INDUSTRIES}
                    selected={form.industry}
                    onSelect={(v) => setForm({ industry: v })}
                    required
                />
                <FormInput
                    label="Company Code"
                    placeholder="e.g. ABC-IN-001 (auto-generated)"
                    value={form.companyCode}
                    onChangeText={(v) => setForm({ companyCode: v })}
                    required
                    autoCapitalize="none"
                    hint="Auto-generated based on company name. Override if needed."
                />
                <FormInput
                    label="Short Name"
                    placeholder="Abbreviated name for headers"
                    value={form.shortName}
                    onChangeText={(v) => setForm({ shortName: v })}
                />
                <FormInput
                    label="Date of Incorporation"
                    placeholder="DD/MM/YYYY"
                    value={form.incorporationDate}
                    onChangeText={(v) => setForm({ incorporationDate: v })}
                    required
                />
                <FormInput
                    label="Number of Employees (approx.)"
                    placeholder="e.g. 250"
                    value={form.employees}
                    onChangeText={(v) => setForm({ employees: v })}
                    keyboardType="number-pad"
                    hint="Used for PF, ESI, PT compliance threshold checks."
                />
                <FormInput
                    label="CIN Number"
                    placeholder="U72900KA2019PTC312847"
                    value={form.cin}
                    onChangeText={(v) => setForm({ cin: v })}
                    autoCapitalize="none"
                />
                <FormInput
                    label="Official Website"
                    placeholder="https://company.com"
                    value={form.website}
                    onChangeText={(v) => setForm({ website: v })}
                    keyboardType="url"
                    autoCapitalize="none"
                />
                <FormInput
                    label="Corporate Email Domain"
                    placeholder="company.com"
                    value={form.emailDomain}
                    onChangeText={(v) => setForm({ emailDomain: v })}
                    required
                    keyboardType="email-address"
                    autoCapitalize="none"
                    hint="Used for auto-provisioning employee email IDs."
                />
            </SectionCard>

            <SectionCard title="Company Status">
                {COMPANY_STATUSES.map((s) => (
                    <RadioOption
                        key={s}
                        label={s}
                        selected={form.status === s}
                        onSelect={() => setForm({ status: s })}
                        badge={s === 'Draft' ? 'DEFAULT' : undefined}
                    />
                ))}
            </SectionCard>
        </Animated.View>
    );
}

// ============ STEP 2 — STATUTORY & TAX ============

function Step2Statutory({
    form,
    setForm,
}: {
    form: Step2Form;
    setForm: (f: Partial<Step2Form>) => void;
}) {
    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <View style={styles.warningBanner}>
                <Svg width={16} height={16} viewBox="0 0 24 24">
                    <Path
                        d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01"
                        stroke={colors.warning[700]}
                        strokeWidth="1.8"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                </Svg>
                <Text className="ml-2 flex-1 font-inter text-xs leading-4 text-warning-700">
                    Critical: These identifiers drive payroll, TDS, and statutory filings. Ensure 100% accuracy.
                </Text>
            </View>

            <SectionCard title="India Statutory Identifiers">
                <FormInput
                    label="PAN"
                    placeholder="AARCA5678F"
                    value={form.pan}
                    onChangeText={(v) => setForm({ pan: v.toUpperCase() })}
                    required
                    autoCapitalize="none"
                    hint="Required for TDS, Form 16, Form 24Q"
                />
                <FormInput
                    label="TAN"
                    placeholder="BLRA98765T"
                    value={form.tan}
                    onChangeText={(v) => setForm({ tan: v.toUpperCase() })}
                    required
                    autoCapitalize="none"
                    hint="Required for TDS deduction and quarterly returns"
                />
                <FormInput
                    label="GSTIN"
                    placeholder="29AARCA5678F1Z3"
                    value={form.gstin}
                    onChangeText={(v) => setForm({ gstin: v.toUpperCase() })}
                    autoCapitalize="none"
                    hint="Required if GST-registered. State code auto-prefixed."
                />
                <FormInput
                    label="PF Registration No."
                    placeholder="KA/BLR/0112345/000/0001"
                    value={form.pfRegNo}
                    onChangeText={(v) => setForm({ pfRegNo: v })}
                    required
                    autoCapitalize="none"
                    hint="Required for PF deductions and ECR uploads"
                />
                <FormInput
                    label="ESI Employer Code"
                    placeholder="53-00-123456-000-0001"
                    value={form.esiCode}
                    onChangeText={(v) => setForm({ esiCode: v })}
                    autoCapitalize="none"
                    hint="Required if any employee earns ≤ ₹21,000/month gross"
                />
                <FormInput
                    label="PT Registration No."
                    placeholder="State-specific format"
                    value={form.ptReg}
                    onChangeText={(v) => setForm({ ptReg: v })}
                    autoCapitalize="none"
                    hint="Required in PT-applicable states (Karnataka, Maharashtra, etc.)"
                />
                <FormInput
                    label="LWFR Number"
                    placeholder="Labour Welfare Fund Registration"
                    value={form.lwfrNo}
                    onChangeText={(v) => setForm({ lwfrNo: v })}
                    autoCapitalize="none"
                />
                <ChipSelector
                    label="ROC Filing State"
                    options={INDIAN_STATES}
                    selected={form.rocState}
                    onSelect={(v) => setForm({ rocState: v })}
                    required
                />
            </SectionCard>
        </Animated.View>
    );
}

// ============ STEP 3 — ADDRESS ============

function Step3Address({
    form,
    setForm,
}: {
    form: Step3Form;
    setForm: (f: Partial<Step3Form>) => void;
}) {
    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <SectionCard title="Registered Address">
                <FormInput
                    label="Address Line 1"
                    placeholder="Street, building, floor"
                    value={form.regLine1}
                    onChangeText={(v) => setForm({ regLine1: v })}
                    required
                />
                <FormInput
                    label="Address Line 2"
                    placeholder="Area, landmark, locality"
                    value={form.regLine2}
                    onChangeText={(v) => setForm({ regLine2: v })}
                />
                <FormInput
                    label="City"
                    placeholder="e.g. Bengaluru"
                    value={form.regCity}
                    onChangeText={(v) => setForm({ regCity: v })}
                    required
                    autoCapitalize="words"
                />
                <FormInput
                    label="District"
                    placeholder="e.g. Bengaluru Urban"
                    value={form.regDistrict}
                    onChangeText={(v) => setForm({ regDistrict: v })}
                    autoCapitalize="words"
                />
                <ChipSelector
                    label="State"
                    options={INDIAN_STATES}
                    selected={form.regState}
                    onSelect={(v) => setForm({ regState: v })}
                    required
                />
                <FormInput
                    label="PIN Code"
                    placeholder="560001"
                    value={form.regPin}
                    onChangeText={(v) => setForm({ regPin: v })}
                    required
                    keyboardType="number-pad"
                />
                <FormInput
                    label="STD Code"
                    placeholder="080"
                    value={form.regStdCode}
                    onChangeText={(v) => setForm({ regStdCode: v })}
                    keyboardType="phone-pad"
                />
            </SectionCard>

            <SectionCard title="Corporate / HQ Address">
                <Pressable
                    onPress={() =>
                        setForm({
                            sameAsRegistered: !form.sameAsRegistered,
                            ...(form.sameAsRegistered
                                ? {}
                                : {
                                      corpLine1: form.regLine1,
                                      corpCity: form.regCity,
                                      corpState: form.regState,
                                      corpPin: form.regPin,
                                  }),
                        })
                    }
                    style={styles.checkboxRow}
                >
                    <View style={[styles.checkbox, form.sameAsRegistered && styles.checkboxActive]}>
                        {form.sameAsRegistered && (
                            <Svg width={12} height={12} viewBox="0 0 24 24">
                                <Path
                                    d="M5 12l5 5L20 7"
                                    stroke="#fff"
                                    strokeWidth="3"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            </Svg>
                        )}
                    </View>
                    <Text className="font-inter text-sm font-medium text-neutral-600">
                        Same as Registered Address
                    </Text>
                </Pressable>

                {!form.sameAsRegistered && (
                    <Animated.View entering={FadeIn.duration(200)}>
                        <FormInput
                            label="Address Line 1"
                            placeholder="Corporate office address"
                            value={form.corpLine1}
                            onChangeText={(v) => setForm({ corpLine1: v })}
                        />
                        <FormInput
                            label="City"
                            placeholder="City"
                            value={form.corpCity}
                            onChangeText={(v) => setForm({ corpCity: v })}
                            autoCapitalize="words"
                        />
                        <ChipSelector
                            label="State"
                            options={INDIAN_STATES}
                            selected={form.corpState}
                            onSelect={(v) => setForm({ corpState: v })}
                        />
                        <FormInput
                            label="PIN Code"
                            placeholder="560001"
                            value={form.corpPin}
                            onChangeText={(v) => setForm({ corpPin: v })}
                            keyboardType="number-pad"
                        />
                    </Animated.View>
                )}
            </SectionCard>
        </Animated.View>
    );
}

// ============ STEP 4 — FISCAL & CALENDAR ============

function Step4Fiscal({
    form,
    setForm,
}: {
    form: Step4Form;
    setForm: (f: Partial<Step4Form>) => void;
}) {
    const toggleWorkingDay = (day: string) => {
        const updated = form.workingDays.includes(day)
            ? form.workingDays.filter((d) => d !== day)
            : [...form.workingDays, day];
        setForm({ workingDays: updated });
    };

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <SectionCard title="Financial Year">
                {FY_OPTIONS.map((opt) => (
                    <RadioOption
                        key={opt.key}
                        label={opt.label}
                        subtitle={opt.subtitle}
                        selected={form.fyStart === opt.key}
                        onSelect={() => setForm({ fyStart: opt.key })}
                        badge={opt.key === 'apr-mar' ? 'INDIA DEFAULT' : undefined}
                    />
                ))}
            </SectionCard>

            <SectionCard title="Payroll Cycle">
                <ChipSelector
                    label="Frequency"
                    options={PAYROLL_FREQ}
                    selected={form.payrollFreq}
                    onSelect={(v) => setForm({ payrollFreq: v })}
                />
                <ChipSelector
                    label="Cut-off Day"
                    options={CUTOFF_DAY}
                    selected={form.cutoffDay}
                    onSelect={(v) => setForm({ cutoffDay: v })}
                    hint="Day when attendance/leaves are frozen for payroll"
                />
                <ChipSelector
                    label="Disbursement Day"
                    options={DISBURSEMENT_DAY}
                    selected={form.disbursementDay}
                    onSelect={(v) => setForm({ disbursementDay: v })}
                />
            </SectionCard>

            <SectionCard title="Week & Timezone">
                <ChipSelector
                    label="Week Start"
                    options={WEEK_STARTS}
                    selected={form.weekStart}
                    onSelect={(v) => setForm({ weekStart: v })}
                />
                <ChipSelector
                    label="Timezone"
                    options={TIMEZONES}
                    selected={form.timezone}
                    onSelect={(v) => setForm({ timezone: v })}
                    required
                />
            </SectionCard>

            <SectionCard title="Working Days">
                <Text className="mb-3 font-inter text-xs text-neutral-500">
                    Toggle each day as working or weekly off
                </Text>
                {DAYS_OF_WEEK.map((day) => {
                    const isWorking = form.workingDays.includes(day);
                    return (
                        <Pressable
                            key={day}
                            onPress={() => toggleWorkingDay(day)}
                            style={[styles.dayToggleRow, isWorking && styles.dayToggleRowActive]}
                        >
                            <Text
                                className={`font-inter text-sm font-semibold ${isWorking ? 'text-primary-700' : 'text-neutral-400'}`}
                            >
                                {day}
                            </Text>
                            <View
                                style={[
                                    styles.dayBadge,
                                    { backgroundColor: isWorking ? colors.success[100] : colors.neutral[100] },
                                ]}
                            >
                                <Text
                                    className={`font-inter text-[10px] font-bold ${isWorking ? 'text-success-700' : 'text-neutral-400'}`}
                                >
                                    {isWorking ? 'Working' : 'Off'}
                                </Text>
                            </View>
                        </Pressable>
                    );
                })}
            </SectionCard>
        </Animated.View>
    );
}

// ============ STEP 5 — PREFERENCES & FEATURE FLAGS ============

function Step5Preferences({
    form,
    setForm,
}: {
    form: Step5Form;
    setForm: (f: Partial<Step5Form>) => void;
}) {
    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <SectionCard title="Locale & Format">
                <ChipSelector label="Currency" options={CURRENCIES} selected={form.currency} onSelect={(v) => setForm({ currency: v })} required />
                <ChipSelector label="Language" options={LANGUAGES} selected={form.language} onSelect={(v) => setForm({ language: v })} />
                <ChipSelector label="Date Format" options={DATE_FORMATS} selected={form.dateFormat} onSelect={(v) => setForm({ dateFormat: v })} />
                <ChipSelector label="Number Format" options={NUMBER_FORMATS} selected={form.numberFormat} onSelect={(v) => setForm({ numberFormat: v })} />
                <ChipSelector label="Time Format" options={TIME_FORMATS} selected={form.timeFormat} onSelect={(v) => setForm({ timeFormat: v })} />
            </SectionCard>

            <SectionCard title="Compliance Toggles">
                <ToggleRow
                    label="India Statutory Compliance"
                    subtitle="PF, ESI, PT, TDS, Form 16, Gratuity, Bonus Act"
                    value={form.indiaCompliance}
                    onToggle={(v) => setForm({ indiaCompliance: v })}
                />
                <ToggleRow
                    label="Multi-Currency Payroll"
                    subtitle="International employees in multiple currencies"
                    value={form.multiCurrency}
                    onToggle={(v) => setForm({ multiCurrency: v })}
                />
            </SectionCard>

            <SectionCard title="Employee Portal & App">
                <ToggleRow
                    label="Employee Self-Service (ESS) Portal"
                    subtitle="Employee login for leaves, payslips, IT declarations"
                    value={form.ess}
                    onToggle={(v) => setForm({ ess: v })}
                />
                <ToggleRow
                    label="Mobile App (iOS & Android)"
                    subtitle="Avy ERP mobile app access for all employees"
                    value={form.mobileApp}
                    onToggle={(v) => setForm({ mobileApp: v })}
                />
                <ToggleRow
                    label="AI HR Assistant Chatbot"
                    subtitle="NLP chatbot for leave, policy FAQs"
                    value={form.aiChatbot}
                    onToggle={(v) => setForm({ aiChatbot: v })}
                />
                <ToggleRow
                    label="e-Sign Integration"
                    subtitle="Digital signatures for offer letters and F&F"
                    value={form.eSign}
                    onToggle={(v) => setForm({ eSign: v })}
                />
            </SectionCard>

            <SectionCard title="Integrations & Devices">
                <ToggleRow
                    label="Biometric / Device Sync"
                    subtitle="Auto-sync attendance from ZKTeco, ESSL devices"
                    value={form.biometric}
                    onToggle={(v) => setForm({ biometric: v })}
                />
                <ToggleRow
                    label="Payroll Bank Integration"
                    subtitle="NEFT/RTGS bank file generation for salary disbursement"
                    value={form.bankIntegration}
                    onToggle={(v) => setForm({ bankIntegration: v })}
                />
                <ToggleRow
                    label="Email Notifications"
                    subtitle="Automated emails for payslips, leave approvals, alerts"
                    value={form.emailNotif}
                    onToggle={(v) => setForm({ emailNotif: v })}
                />
                <ToggleRow
                    label="WhatsApp Notifications"
                    subtitle="Salary alerts, leave status via WhatsApp Business API"
                    value={form.whatsapp}
                    onToggle={(v) => setForm({ whatsapp: v })}
                />
            </SectionCard>
        </Animated.View>
    );
}

// ============ STEP 6 — BRANCHES ============

function Step6Branches({
    branches,
    setBranches,
}: {
    branches: Branch[];
    setBranches: (b: Branch[]) => void;
}) {
    const addBranch = () => {
        const newBranch: Branch = {
            id: Date.now().toString(),
            name: '',
            code: '',
            type: '',
            addressLine1: '',
            city: '',
            state: '',
            pin: '',
            contact: '',
            geoRadius: '',
        };
        setBranches([...branches, newBranch]);
    };

    const updateBranch = (id: string, updates: Partial<Branch>) => {
        setBranches(branches.map((b) => (b.id === id ? { ...b, ...updates } : b)));
    };

    const removeBranch = (id: string) => {
        setBranches(branches.filter((b) => b.id !== id));
    };

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <View style={styles.infoCard}>
                <Text className="font-inter text-sm text-neutral-600">
                    Branches are sub-units at different geographic locations. They share the same legal entity but may have separate addresses and compliance registrations.
                </Text>
            </View>

            {branches.map((branch, idx) => (
                <Animated.View
                    key={branch.id}
                    entering={FadeIn.duration(250)}
                    style={styles.itemCard}
                >
                    <View style={styles.itemCardHeader}>
                        <View style={styles.itemCardBadge}>
                            <Text className="font-inter text-xs font-bold text-primary-700">
                                Branch {idx + 1}
                            </Text>
                        </View>
                        <DeleteButton onPress={() => removeBranch(branch.id)} />
                    </View>
                    <FormInput
                        label="Branch Name"
                        placeholder='e.g. "Bengaluru HQ"'
                        value={branch.name}
                        onChangeText={(v) => updateBranch(branch.id, { name: v })}
                        required
                        autoCapitalize="words"
                    />
                    <FormInput
                        label="Branch Code"
                        placeholder="BLR-HQ-001"
                        value={branch.code}
                        onChangeText={(v) => updateBranch(branch.id, { code: v })}
                        required
                        autoCapitalize="none"
                    />
                    <ChipSelector
                        label="Branch Type"
                        options={BRANCH_TYPES}
                        selected={branch.type}
                        onSelect={(v) => updateBranch(branch.id, { type: v })}
                    />
                    <FormInput
                        label="Address"
                        placeholder="Street, area, locality"
                        value={branch.addressLine1}
                        onChangeText={(v) => updateBranch(branch.id, { addressLine1: v })}
                    />
                    <View style={styles.twoColumn}>
                        <View style={{ flex: 1 }}>
                            <FormInput
                                label="City"
                                placeholder="City"
                                value={branch.city}
                                onChangeText={(v) => updateBranch(branch.id, { city: v })}
                                autoCapitalize="words"
                            />
                        </View>
                        <View style={{ flex: 1 }}>
                            <FormInput
                                label="PIN Code"
                                placeholder="560001"
                                value={branch.pin}
                                onChangeText={(v) => updateBranch(branch.id, { pin: v })}
                                keyboardType="number-pad"
                            />
                        </View>
                    </View>
                    <FormInput
                        label="Contact Number"
                        placeholder="+91 98765 43210"
                        value={branch.contact}
                        onChangeText={(v) => updateBranch(branch.id, { contact: v })}
                        keyboardType="phone-pad"
                    />
                    <FormInput
                        label="Geo-Fencing Radius (metres)"
                        placeholder="200"
                        value={branch.geoRadius}
                        onChangeText={(v) => updateBranch(branch.id, { geoRadius: v })}
                        keyboardType="number-pad"
                        hint="GPS radius for attendance punch-in restriction"
                    />
                </Animated.View>
            ))}

            <AddButton onPress={addBranch} label="Add Branch" />
        </Animated.View>
    );
}

// ============ STEP 7 — KEY CONTACTS ============

function Step7Contacts({
    contacts,
    setContacts,
}: {
    contacts: Contact[];
    setContacts: (c: Contact[]) => void;
}) {
    const addContact = () => {
        setContacts([
            ...contacts,
            {
                id: Date.now().toString(),
                name: '',
                designation: '',
                department: '',
                mobile: '',
                email: '',
                type: 'Primary',
                linkedin: '',
            },
        ]);
    };

    const updateContact = (id: string, updates: Partial<Contact>) => {
        setContacts(contacts.map((c) => (c.id === id ? { ...c, ...updates } : c)));
    };

    const removeContact = (id: string) => {
        setContacts(contacts.filter((c) => c.id !== id));
    };

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            {contacts.map((contact, idx) => (
                <Animated.View
                    key={contact.id}
                    entering={FadeIn.duration(250)}
                    style={styles.itemCard}
                >
                    <View style={styles.itemCardHeader}>
                        <View style={styles.itemCardBadge}>
                            <Text className="font-inter text-xs font-bold text-primary-700">
                                Contact {idx + 1}
                            </Text>
                        </View>
                        <DeleteButton onPress={() => removeContact(contact.id)} />
                    </View>
                    <FormInput
                        label="Contact Name"
                        placeholder="Full name"
                        value={contact.name}
                        onChangeText={(v) => updateContact(contact.id, { name: v })}
                        required
                        autoCapitalize="words"
                    />
                    <View style={styles.twoColumn}>
                        <View style={{ flex: 1 }}>
                            <FormInput
                                label="Designation"
                                placeholder="CEO, CHRO, CFO"
                                value={contact.designation}
                                onChangeText={(v) => updateContact(contact.id, { designation: v })}
                                autoCapitalize="words"
                            />
                        </View>
                        <View style={{ flex: 1 }}>
                            <FormInput
                                label="Department"
                                placeholder="HR, Finance, IT"
                                value={contact.department}
                                onChangeText={(v) => updateContact(contact.id, { department: v })}
                                autoCapitalize="words"
                            />
                        </View>
                    </View>
                    <FormInput
                        label="Mobile Number"
                        placeholder="+91 98765 43210"
                        value={contact.mobile}
                        onChangeText={(v) => updateContact(contact.id, { mobile: v })}
                        required
                        keyboardType="phone-pad"
                    />
                    <FormInput
                        label="Email Address"
                        placeholder="contact@company.com"
                        value={contact.email}
                        onChangeText={(v) => updateContact(contact.id, { email: v })}
                        required
                        keyboardType="email-address"
                        autoCapitalize="none"
                    />
                    <ChipSelector
                        label="Contact Type"
                        options={CONTACT_TYPES}
                        selected={contact.type}
                        onSelect={(v) => updateContact(contact.id, { type: v })}
                    />
                    <FormInput
                        label="LinkedIn Profile"
                        placeholder="https://linkedin.com/in/username"
                        value={contact.linkedin}
                        onChangeText={(v) => updateContact(contact.id, { linkedin: v })}
                        keyboardType="url"
                        autoCapitalize="none"
                    />
                </Animated.View>
            ))}

            <AddButton onPress={addContact} label="Add Contact" />
        </Animated.View>
    );
}

// ============ STEP 8 — PLANTS ============

function Step8Plants({
    form,
    setForm,
    plants,
    setPlants,
}: {
    form: Step8Form;
    setForm: (f: Partial<Step8Form>) => void;
    plants: Plant[];
    setPlants: (p: Plant[]) => void;
}) {
    const addPlant = () => {
        setPlants([
            ...plants,
            {
                id: Date.now().toString(),
                name: '',
                code: '',
                type: '',
                status: 'Active',
                isHQ: plants.length === 0,
                gstin: '',
                stateGST: '',
                addressLine1: '',
                addressLine2: '',
                city: '',
                district: '',
                state: '',
                pin: '',
            },
        ]);
    };

    const updatePlant = (id: string, updates: Partial<Plant>) => {
        setPlants(
            plants.map((p) => {
                if (p.id !== id) return p;
                const updated = { ...p, ...updates };
                // Enforce single HQ
                if (updates.isHQ) {
                    return updated;
                }
                return updated;
            })
        );
    };

    const setHQ = (id: string) => {
        setPlants(plants.map((p) => ({ ...p, isHQ: p.id === id })));
    };

    const removePlant = (id: string) => {
        setPlants(plants.filter((p) => p.id !== id));
    };

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <SectionCard title="Multi-Plant Configuration">
                <ToggleRow
                    label="Multi-Plant Mode"
                    subtitle="Enable if the company operates from multiple plants or locations"
                    value={form.multiPlantMode}
                    onToggle={(v) => setForm({ multiPlantMode: v })}
                />
                {form.multiPlantMode && (
                    <Animated.View entering={FadeIn.duration(200)}>
                        <Text className="mb-2 mt-3 font-inter text-xs font-bold text-neutral-500">
                            Data Management Strategy
                        </Text>
                        <RadioOption
                            label="Common Configuration"
                            subtitle="All plants share same shift schedules, No Series, and IOT Reason lists"
                            selected={form.plantConfig === 'common'}
                            onSelect={() => setForm({ plantConfig: 'common' })}
                        />
                        <RadioOption
                            label="Per-Plant Configuration"
                            subtitle="Each plant has its own independent schedules and serial tracking"
                            selected={form.plantConfig === 'per-plant'}
                            onSelect={() => setForm({ plantConfig: 'per-plant' })}
                        />
                    </Animated.View>
                )}
            </SectionCard>

            {plants.map((plant, idx) => (
                <Animated.View
                    key={plant.id}
                    entering={FadeIn.duration(250)}
                    style={[styles.itemCard, plant.isHQ && styles.hqCard]}
                >
                    <View style={styles.itemCardHeader}>
                        <View style={styles.itemCardBadge}>
                            <Text className="font-inter text-xs font-bold text-primary-700">
                                Plant {idx + 1}
                                {plant.isHQ && ' — HQ'}
                            </Text>
                        </View>
                        <View style={styles.rowCenter}>
                            <Pressable
                                onPress={() => setHQ(plant.id)}
                                style={[styles.hqToggleBtn, plant.isHQ && styles.hqToggleBtnActive]}
                            >
                                <Text
                                    className={`font-inter text-[10px] font-bold ${plant.isHQ ? 'text-primary-700' : 'text-neutral-500'}`}
                                >
                                    {plant.isHQ ? 'HQ' : 'Set HQ'}
                                </Text>
                            </Pressable>
                            <DeleteButton onPress={() => removePlant(plant.id)} />
                        </View>
                    </View>

                    <FormInput label="Plant Name" placeholder="e.g. Pune Plant" value={plant.name} onChangeText={(v) => updatePlant(plant.id, { name: v })} required autoCapitalize="words" />
                    <FormInput label="Plant Code" placeholder="PLT-PUN-01" value={plant.code} onChangeText={(v) => updatePlant(plant.id, { code: v })} required autoCapitalize="none" />
                    <ChipSelector label="Plant Type" options={PLANT_TYPES} selected={plant.type} onSelect={(v) => updatePlant(plant.id, { type: v })} />
                    <ChipSelector label="Status" options={PLANT_STATUSES} selected={plant.status} onSelect={(v) => updatePlant(plant.id, { status: v })} />

                    <Text className="mb-2 mt-2 font-inter text-xs font-bold uppercase tracking-wider text-neutral-400">
                        GST Details
                    </Text>
                    <FormInput label="Plant GSTIN" placeholder="29AARCA5678F1Z3" value={plant.gstin} onChangeText={(v) => updatePlant(plant.id, { gstin: v.toUpperCase() })} autoCapitalize="none" hint="Separate GSTIN required for each state" />

                    <Text className="mb-2 mt-2 font-inter text-xs font-bold uppercase tracking-wider text-neutral-400">
                        Plant Address
                    </Text>
                    <FormInput label="Address Line 1" placeholder="Street, plot, building" value={plant.addressLine1} onChangeText={(v) => updatePlant(plant.id, { addressLine1: v })} required />
                    <FormInput label="Address Line 2" placeholder="Area, landmark" value={plant.addressLine2} onChangeText={(v) => updatePlant(plant.id, { addressLine2: v })} />
                    <View style={styles.twoColumn}>
                        <View style={{ flex: 1 }}>
                            <FormInput label="City" placeholder="City" value={plant.city} onChangeText={(v) => updatePlant(plant.id, { city: v })} required autoCapitalize="words" />
                        </View>
                        <View style={{ flex: 1 }}>
                            <FormInput label="PIN Code" placeholder="411001" value={plant.pin} onChangeText={(v) => updatePlant(plant.id, { pin: v })} keyboardType="number-pad" />
                        </View>
                    </View>
                </Animated.View>
            ))}

            <AddButton onPress={addPlant} label="Add Plant" />
        </Animated.View>
    );
}

// ============ STEP 9 — SHIFTS & TIME MANAGEMENT ============

function Step9Shifts({
    form,
    setForm,
    shifts,
    setShifts,
}: {
    form: Step9Form;
    setForm: (f: Partial<Step9Form>) => void;
    shifts: Shift[];
    setShifts: (s: Shift[]) => void;
}) {
    const toggleWeeklyOff = (day: string) => {
        const updated = form.weeklyOffs.includes(day)
            ? form.weeklyOffs.filter((d) => d !== day)
            : [...form.weeklyOffs, day];
        setForm({ weeklyOffs: updated });
    };

    const addShift = () => {
        setShifts([
            ...shifts,
            {
                id: Date.now().toString(),
                name: '',
                fromTime: '',
                toTime: '',
                noShuffle: false,
                downtimeSlots: [],
            },
        ]);
    };

    const updateShift = (id: string, updates: Partial<Shift>) => {
        setShifts(shifts.map((s) => (s.id === id ? { ...s, ...updates } : s)));
    };

    const removeShift = (id: string) => {
        setShifts(shifts.filter((s) => s.id !== id));
    };

    const addDowntimeSlot = (shiftId: string) => {
        const slot: DowntimeSlot = {
            id: Date.now().toString(),
            type: '',
            duration: '',
        };
        setShifts(
            shifts.map((s) =>
                s.id === shiftId
                    ? { ...s, downtimeSlots: [...s.downtimeSlots, slot] }
                    : s
            )
        );
    };

    const updateSlot = (shiftId: string, slotId: string, updates: Partial<DowntimeSlot>) => {
        setShifts(
            shifts.map((s) =>
                s.id === shiftId
                    ? {
                          ...s,
                          downtimeSlots: s.downtimeSlots.map((d) =>
                              d.id === slotId ? { ...d, ...updates } : d
                          ),
                      }
                    : s
            )
        );
    };

    const removeSlot = (shiftId: string, slotId: string) => {
        setShifts(
            shifts.map((s) =>
                s.id === shiftId
                    ? { ...s, downtimeSlots: s.downtimeSlots.filter((d) => d.id !== slotId) }
                    : s
            )
        );
    };

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <SectionCard title="Production Day Boundary">
                <View style={styles.twoColumn}>
                    <View style={{ flex: 1 }}>
                        <FormInput
                            label="Day Start Time"
                            placeholder="06:00 AM"
                            value={form.dayStartTime}
                            onChangeText={(v) => setForm({ dayStartTime: v })}
                            required
                        />
                    </View>
                    <View style={{ flex: 1 }}>
                        <FormInput
                            label="Day End Time"
                            placeholder="10:00 PM"
                            value={form.dayEndTime}
                            onChangeText={(v) => setForm({ dayEndTime: v })}
                            required
                        />
                    </View>
                </View>
            </SectionCard>

            <SectionCard title="Weekly Off Days">
                <View style={styles.chipGrid}>
                    {DAYS_OF_WEEK.map((day) => {
                        const isOff = form.weeklyOffs.includes(day);
                        return (
                            <Pressable
                                key={day}
                                onPress={() => toggleWeeklyOff(day)}
                                style={[styles.chip, isOff && styles.chipActive]}
                            >
                                <Text className={`font-inter text-xs font-semibold ${isOff ? 'text-white' : 'text-neutral-600'}`}>
                                    {day.substring(0, 3)}
                                </Text>
                            </Pressable>
                        );
                    })}
                </View>
            </SectionCard>

            <Text className="mb-3 font-inter text-sm font-bold text-primary-900">
                Shift Master
            </Text>

            {shifts.map((shift, idx) => (
                <Animated.View
                    key={shift.id}
                    entering={FadeIn.duration(250)}
                    style={styles.itemCard}
                >
                    <View style={styles.itemCardHeader}>
                        <View style={styles.itemCardBadge}>
                            <Text className="font-inter text-xs font-bold text-primary-700">
                                Shift {idx + 1}
                            </Text>
                        </View>
                        <DeleteButton onPress={() => removeShift(shift.id)} />
                    </View>

                    <FormInput
                        label="Shift Name"
                        placeholder='e.g. "Morning Shift", "General Shift"'
                        value={shift.name}
                        onChangeText={(v) => updateShift(shift.id, { name: v })}
                        required
                        autoCapitalize="words"
                    />
                    <View style={styles.twoColumn}>
                        <View style={{ flex: 1 }}>
                            <FormInput label="From Time" placeholder="07:00 AM" value={shift.fromTime} onChangeText={(v) => updateShift(shift.id, { fromTime: v })} required />
                        </View>
                        <View style={{ flex: 1 }}>
                            <FormInput label="To Time" placeholder="03:00 PM" value={shift.toTime} onChangeText={(v) => updateShift(shift.id, { toTime: v })} required />
                        </View>
                    </View>

                    <Pressable
                        onPress={() => updateShift(shift.id, { noShuffle: !shift.noShuffle })}
                        style={styles.checkboxRow}
                    >
                        <View style={[styles.checkbox, shift.noShuffle && styles.checkboxActive]}>
                            {shift.noShuffle && (
                                <Svg width={12} height={12} viewBox="0 0 24 24">
                                    <Path d="M5 12l5 5L20 7" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                                </Svg>
                            )}
                        </View>
                        <Text className="font-inter text-sm text-neutral-600">
                            No Shuffle (exclude from shift rotation)
                        </Text>
                    </Pressable>

                    {/* Downtime Slots */}
                    <Text className="mb-2 mt-3 font-inter text-xs font-bold text-neutral-500">
                        Planned Downtime Slots
                    </Text>
                    {shift.downtimeSlots.map((slot) => (
                        <View key={slot.id} style={styles.slotRow}>
                            <View style={{ flex: 2 }}>
                                <ChipSelector
                                    label="Type"
                                    options={DOWNTIME_TYPES}
                                    selected={slot.type}
                                    onSelect={(v) => updateSlot(shift.id, slot.id, { type: v })}
                                />
                            </View>
                            <View style={{ flex: 1 }}>
                                <FormInput
                                    label="Duration (min)"
                                    placeholder="30"
                                    value={slot.duration}
                                    onChangeText={(v) => updateSlot(shift.id, slot.id, { duration: v })}
                                    keyboardType="number-pad"
                                />
                            </View>
                            <DeleteButton onPress={() => removeSlot(shift.id, slot.id)} />
                        </View>
                    ))}
                    <Pressable
                        onPress={() => addDowntimeSlot(shift.id)}
                        style={styles.smallAddButton}
                    >
                        <Text className="font-inter text-xs font-semibold text-primary-500">
                            + Add Downtime Slot
                        </Text>
                    </Pressable>
                </Animated.View>
            ))}

            <AddButton onPress={addShift} label="Add Shift" />
        </Animated.View>
    );
}

// ============ STEP 10 — NO SERIES ============

function Step10NoSeries({
    noSeries,
    setNoSeries,
}: {
    noSeries: NoSeriesItem[];
    setNoSeries: (ns: NoSeriesItem[]) => void;
}) {
    const addSeries = () => {
        setNoSeries([
            ...noSeries,
            {
                id: Date.now().toString(),
                code: '',
                description: '',
                linkedScreen: '',
                prefix: '',
                suffix: '',
                numberCount: '5',
                startNumber: '1',
            },
        ]);
    };

    const update = (id: string, updates: Partial<NoSeriesItem>) => {
        setNoSeries(noSeries.map((ns) => (ns.id === id ? { ...ns, ...updates } : ns)));
    };

    const remove = (id: string) => {
        setNoSeries(noSeries.filter((ns) => ns.id !== id));
    };

    const getPreview = (item: NoSeriesItem) => {
        const count = parseInt(item.numberCount || '5', 10);
        const start = parseInt(item.startNumber || '1', 10);
        const num = String(start).padStart(count, '0');
        return `${item.prefix}${num}${item.suffix}`;
    };

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <View style={styles.infoCard}>
                <Text className="font-inter text-sm text-neutral-600">
                    Number Series defines auto-numbering formats for all transactional documents. Each series generates unique, traceable document numbers.
                </Text>
            </View>

            {noSeries.map((item, idx) => (
                <Animated.View key={item.id} entering={FadeIn.duration(250)} style={styles.itemCard}>
                    <View style={styles.itemCardHeader}>
                        <View style={styles.itemCardBadge}>
                            <Text className="font-inter text-xs font-bold text-primary-700">
                                Series {idx + 1}
                            </Text>
                        </View>
                        <DeleteButton onPress={() => remove(item.id)} />
                    </View>

                    <View style={styles.twoColumn}>
                        <View style={{ flex: 1 }}>
                            <FormInput label="Code" placeholder="EMP" value={item.code} onChangeText={(v) => update(item.id, { code: v.toUpperCase() })} required autoCapitalize="none" />
                        </View>
                        <View style={{ flex: 1 }}>
                            <FormInput label="Starting Number" placeholder="1" value={item.startNumber} onChangeText={(v) => update(item.id, { startNumber: v })} keyboardType="number-pad" />
                        </View>
                    </View>

                    <FormInput label="Description" placeholder="Employee ID" value={item.description} onChangeText={(v) => update(item.id, { description: v })} />
                    <ChipSelector label="Linked Screen" options={NO_SERIES_SCREENS} selected={item.linkedScreen} onSelect={(v) => update(item.id, { linkedScreen: v })} required />

                    <View style={styles.twoColumn}>
                        <View style={{ flex: 1 }}>
                            <FormInput label="Prefix" placeholder="EMP-" value={item.prefix} onChangeText={(v) => update(item.id, { prefix: v })} autoCapitalize="none" />
                        </View>
                        <View style={{ flex: 1 }}>
                            <FormInput label="Suffix" placeholder="-2026" value={item.suffix} onChangeText={(v) => update(item.id, { suffix: v })} autoCapitalize="none" />
                        </View>
                    </View>

                    <FormInput
                        label="Number of Digits"
                        placeholder="5"
                        value={item.numberCount}
                        onChangeText={(v) => update(item.id, { numberCount: v })}
                        keyboardType="number-pad"
                    />

                    {/* Preview */}
                    <View style={styles.previewBox}>
                        <Text className="font-inter text-[10px] font-bold text-neutral-400">
                            PREVIEW
                        </Text>
                        <Text className="mt-1 font-inter text-lg font-bold text-primary-600">
                            {getPreview(item)}
                        </Text>
                    </View>
                </Animated.View>
            ))}

            <AddButton onPress={addSeries} label="Add No. Series" />
        </Animated.View>
    );
}

// ============ STEP 11 — IOT REASONS ============

function Step11IOTReasons({
    reasons,
    setReasons,
}: {
    reasons: IOTReason[];
    setReasons: (r: IOTReason[]) => void;
}) {
    const addReason = () => {
        setReasons([
            ...reasons,
            {
                id: Date.now().toString(),
                reasonType: 'Machine Idle',
                reason: '',
                description: '',
                department: '',
                planned: false,
                duration: '',
            },
        ]);
    };

    const update = (id: string, updates: Partial<IOTReason>) => {
        setReasons(reasons.map((r) => (r.id === id ? { ...r, ...updates } : r)));
    };

    const remove = (id: string) => {
        setReasons(reasons.filter((r) => r.id !== id));
    };

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <View style={styles.infoCard}>
                <Text className="font-inter text-sm text-neutral-600">
                    IOT Reason Master classifies machine downtime events for OEE monitoring. These reasons are logged when machines go idle or raise alarms on the shop floor.
                </Text>
            </View>

            {reasons.map((item, idx) => (
                <Animated.View key={item.id} entering={FadeIn.duration(250)} style={styles.itemCard}>
                    <View style={styles.itemCardHeader}>
                        <View style={styles.itemCardBadge}>
                            <Text className="font-inter text-xs font-bold text-primary-700">
                                Reason {idx + 1}
                            </Text>
                        </View>
                        <DeleteButton onPress={() => remove(item.id)} />
                    </View>

                    <ChipSelector
                        label="Reason Type"
                        options={IOT_REASON_TYPES}
                        selected={item.reasonType}
                        onSelect={(v) => update(item.id, { reasonType: v, planned: false })}
                        required
                    />
                    <FormInput
                        label="Reason"
                        placeholder='e.g. "PREVENTIVE MAINTENANCE"'
                        value={item.reason}
                        onChangeText={(v) => update(item.id, { reason: v.toUpperCase() })}
                        required
                        autoCapitalize="characters"
                    />
                    <FormInput
                        label="Description"
                        placeholder="Detailed explanation"
                        value={item.description}
                        onChangeText={(v) => update(item.id, { description: v })}
                        multiline
                    />
                    <FormInput
                        label="Department"
                        placeholder="e.g. Maintenance, Production"
                        value={item.department}
                        onChangeText={(v) => update(item.id, { department: v })}
                        autoCapitalize="words"
                    />

                    {item.reasonType === 'Machine Idle' && (
                        <Animated.View entering={FadeIn.duration(200)}>
                            <Pressable
                                onPress={() => update(item.id, { planned: !item.planned })}
                                style={styles.checkboxRow}
                            >
                                <View style={[styles.checkbox, item.planned && styles.checkboxActive]}>
                                    {item.planned && (
                                        <Svg width={12} height={12} viewBox="0 0 24 24">
                                            <Path d="M5 12l5 5L20 7" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                                        </Svg>
                                    )}
                                </View>
                                <Text className="font-inter text-sm text-neutral-600">
                                    Planned Downtime
                                </Text>
                            </Pressable>

                            {item.planned && (
                                <FormInput
                                    label="Max Planned Duration (minutes)"
                                    placeholder="60"
                                    value={item.duration}
                                    onChangeText={(v) => update(item.id, { duration: v })}
                                    keyboardType="number-pad"
                                    hint="Excess beyond this is treated as unplanned downtime"
                                />
                            )}
                        </Animated.View>
                    )}
                </Animated.View>
            ))}

            <AddButton onPress={addReason} label="Add IOT Reason" />
        </Animated.View>
    );
}

// ============ STEP 12 — SYSTEM CONTROLS ============

function Step12Controls({
    form,
    setForm,
}: {
    form: Step12Form;
    setForm: (f: Partial<Step12Form>) => void;
}) {
    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <View style={styles.infoCard}>
                <Text className="font-inter text-sm text-neutral-600">
                    System controls are always company-level — they apply to all plants regardless of Multi-Plant configuration.
                </Text>
            </View>

            <SectionCard title="NC Reason Assignment">
                <ToggleRow
                    label="Enable Edit Mode"
                    subtitle="Allows operators to edit or delete existing Non-Conformance (NC) entries in the NC Reason Assignment screen"
                    value={form.ncEditMode}
                    onToggle={(v) => setForm({ ncEditMode: v })}
                />
            </SectionCard>

            <SectionCard title="Load & Unload Assignment">
                <ToggleRow
                    label="Load / Unload Tracking"
                    subtitle="When enabled, Load & Unload time is tracked and assigned to a category"
                    value={form.loadUnload}
                    onToggle={(v) => setForm({ loadUnload: v })}
                />
                <ToggleRow
                    label="Cycle Time Capture"
                    subtitle="When enabled, cycle time data is captured and included in production analytics"
                    value={form.cycleTime}
                    onToggle={(v) => setForm({ cycleTime: v })}
                />
            </SectionCard>

            <SectionCard title="Payroll & Attendance">
                <ToggleRow
                    label="Payroll Lock Control"
                    subtitle="Prevent payroll modifications after lock date"
                    value={form.payrollLock}
                    onToggle={(v) => setForm({ payrollLock: v })}
                />
                <ToggleRow
                    label="Leave Carry Forward"
                    subtitle="Enable automatic carry forward at year end"
                    value={form.leaveCarryForward}
                    onToggle={(v) => setForm({ leaveCarryForward: v })}
                />
                <ToggleRow
                    label="Overtime Approval"
                    subtitle="Require manager approval before overtime is paid"
                    value={form.overtimeApproval}
                    onToggle={(v) => setForm({ overtimeApproval: v })}
                />
            </SectionCard>

            <SectionCard title="Security">
                <ToggleRow
                    label="Multi-Factor Authentication (MFA)"
                    subtitle="Require OTP / Authenticator app for login"
                    value={form.mfa}
                    onToggle={(v) => setForm({ mfa: v })}
                />
                <ToggleRow
                    label="Backdated Entry Control"
                    subtitle="Restrict creation of records with past dates beyond defined window"
                    value={form.backdatedEntry}
                    onToggle={(v) => setForm({ backdatedEntry: v })}
                />
                <ToggleRow
                    label="Document Number Edit Lock"
                    subtitle="Prevent manual editing of auto-generated document numbers"
                    value={form.docNumberLock}
                    onToggle={(v) => setForm({ docNumberLock: v })}
                />
            </SectionCard>
        </Animated.View>
    );
}

// ============ STEP 13 — USER MANAGEMENT ============

function Step13Users({
    users,
    setUsers,
}: {
    users: UserItem[];
    setUsers: (u: UserItem[]) => void;
}) {
    const ROLES = [
        'Company Admin', 'HR Manager', 'Finance Manager', 'Operations Manager',
        'HR Executive', 'Payroll Executive', 'Plant Supervisor', 'Attendance Operator',
        'Quality Inspector', 'Auditor',
    ];

    const addUser = () => {
        setUsers([
            ...users,
            {
                id: Date.now().toString(),
                fullName: '',
                username: '',
                password: '',
                role: 'Company Admin',
                email: '',
                mobile: '',
                department: '',
            },
        ]);
    };

    const update = (id: string, updates: Partial<UserItem>) => {
        setUsers(users.map((u) => (u.id === id ? { ...u, ...updates } : u)));
    };

    const remove = (id: string) => {
        setUsers(users.filter((u) => u.id !== id));
    };

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <View style={styles.infoCard}>
                <Text className="font-inter text-sm text-neutral-600">
                    Create the initial set of users for this tenant. The Company Admin user is required to allow the tenant to log in and complete their own configuration.
                </Text>
            </View>

            {users.map((user, idx) => (
                <Animated.View key={user.id} entering={FadeIn.duration(250)} style={styles.itemCard}>
                    <View style={styles.itemCardHeader}>
                        <View style={styles.itemCardBadge}>
                            <Text className="font-inter text-xs font-bold text-primary-700">
                                User {idx + 1}
                                {user.role === 'Company Admin' && ' — Admin'}
                            </Text>
                        </View>
                        <DeleteButton onPress={() => remove(user.id)} />
                    </View>

                    <FormInput label="Full Name" placeholder="Full name" value={user.fullName} onChangeText={(v) => update(user.id, { fullName: v })} required autoCapitalize="words" />
                    <FormInput label="Username / Email" placeholder="admin@company.com" value={user.username} onChangeText={(v) => update(user.id, { username: v })} required keyboardType="email-address" autoCapitalize="none" />
                    <FormInput label="Password" placeholder="Set initial password" value={user.password} onChangeText={(v) => update(user.id, { password: v })} required autoCapitalize="none" />
                    <ChipSelector label="Role" options={ROLES} selected={user.role} onSelect={(v) => update(user.id, { role: v })} required />
                    <FormInput label="Email" placeholder="user@company.com" value={user.email} onChangeText={(v) => update(user.id, { email: v })} keyboardType="email-address" autoCapitalize="none" />
                    <FormInput label="Mobile" placeholder="+91 98765 43210" value={user.mobile} onChangeText={(v) => update(user.id, { mobile: v })} keyboardType="phone-pad" />
                    <FormInput label="Department" placeholder="HR, Finance, IT" value={user.department} onChangeText={(v) => update(user.id, { department: v })} autoCapitalize="words" />
                </Animated.View>
            ))}

            <AddButton onPress={addUser} label="Add User" />
        </Animated.View>
    );
}

// ============ STEP 14 — ACTIVATION ============

function Step14Activation({
    companyName,
    currentStatus,
    onStatusChange,
}: {
    companyName: string;
    currentStatus: string;
    onStatusChange: (s: string) => void;
}) {
    const checklistPhases = [
        { phase: 'Company Identity', items: ['Display name & legal name', 'Business type & industry', 'Company code & CIN', 'Corporate email domain'] },
        { phase: 'Compliance & Statutory', items: ['PAN & TAN entered', 'GSTIN configured', 'PF & ESI details', 'ROC filing state'] },
        { phase: 'Address', items: ['Registered address complete', 'Corporate/HQ address confirmed'] },
        { phase: 'Fiscal & Calendar', items: ['FY period selected', 'Payroll cycle configured', 'Timezone & working days set'] },
        { phase: 'Preferences', items: ['Currency & language set', 'Compliance toggles reviewed', 'Integrations configured'] },
        { phase: 'Locations', items: ['Branches added', 'Key contacts added', 'Plants configured (if applicable)'] },
        { phase: 'Time & Config', items: ['Shifts created', 'No Series defined', 'IOT Reasons populated', 'Controls reviewed'] },
        { phase: 'User Access', items: ['Company Admin created', 'Role assignments confirmed'] },
    ];

    return (
        <Animated.View entering={FadeInUp.duration(300)}>
            <LinearGradient
                colors={[colors.primary[600], colors.accent[600]]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.activationHero}
            >
                <View style={styles.activationCircle1} />
                <View style={styles.activationCircle2} />
                <Svg width={48} height={48} viewBox="0 0 24 24">
                    <Path d="M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" stroke="rgba(255,255,255,0.9)" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </Svg>
                <Text className="mt-4 text-center font-inter text-xl font-bold text-white">
                    Ready to Activate
                </Text>
                <Text className="mt-1 text-center font-inter text-sm text-primary-200">
                    {companyName || 'New Company'}
                </Text>
            </LinearGradient>

            <SectionCard title="Set Company Status">
                <Text className="mb-3 font-inter text-xs text-neutral-500">
                    Select the activation status for this tenant:
                </Text>
                {[
                    { status: 'Draft', subtitle: 'Setup is still in progress — not yet live', color: colors.warning[500] },
                    { status: 'Pilot', subtitle: 'Company is in trial/UAT phase with limited users', color: colors.info[500] },
                    { status: 'Active', subtitle: 'Company is live — full production use', color: colors.success[500] },
                ].map((opt) => (
                    <Pressable
                        key={opt.status}
                        onPress={() => onStatusChange(opt.status)}
                        style={[styles.statusOption, currentStatus === opt.status && styles.statusOptionActive]}
                    >
                        <View style={[styles.statusDot, { backgroundColor: opt.color }]} />
                        <View style={{ flex: 1 }}>
                            <Text className={`font-inter text-sm font-bold ${currentStatus === opt.status ? 'text-primary-700' : 'text-primary-950'}`}>
                                {opt.status}
                            </Text>
                            <Text className="font-inter text-xs text-neutral-500">{opt.subtitle}</Text>
                        </View>
                        <View style={[styles.radioCircle, currentStatus === opt.status && styles.radioCircleActive]}>
                            {currentStatus === opt.status && <View style={styles.radioInner} />}
                        </View>
                    </Pressable>
                ))}
            </SectionCard>

            <SectionCard title="Provisioning Checklist">
                <Text className="mb-3 font-inter text-xs text-neutral-500">
                    Verify all phases are complete before going live:
                </Text>
                {checklistPhases.map((phase) => (
                    <View key={phase.phase} style={styles.checklistPhase}>
                        <Text className="mb-1.5 font-inter text-xs font-bold text-primary-900">
                            {phase.phase}
                        </Text>
                        {phase.items.map((item) => (
                            <View key={item} style={styles.checklistItem}>
                                <Svg width={14} height={14} viewBox="0 0 24 24">
                                    <Path d="M9 11l3 3L22 4" stroke={colors.success[500]} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                </Svg>
                                <Text className="ml-2 font-inter text-xs text-neutral-600">{item}</Text>
                            </View>
                        ))}
                    </View>
                ))}
            </SectionCard>
        </Animated.View>
    );
}

// ============ FORM STATE INTERFACES ============

interface Step1Form {
    displayName: string; legalName: string; businessType: string; industry: string;
    companyCode: string; shortName: string; incorporationDate: string; employees: string;
    cin: string; website: string; emailDomain: string; status: string;
}
interface Step2Form {
    pan: string; tan: string; gstin: string; pfRegNo: string;
    esiCode: string; ptReg: string; lwfrNo: string; rocState: string;
}
interface Step3Form {
    regLine1: string; regLine2: string; regCity: string; regDistrict: string;
    regState: string; regCountry: string; regPin: string; regStdCode: string;
    sameAsRegistered: boolean; corpLine1: string; corpCity: string; corpState: string; corpPin: string;
}
interface Step4Form {
    fyStart: string; payrollFreq: string; cutoffDay: string; disbursementDay: string;
    weekStart: string; timezone: string; workingDays: string[];
}
interface Step5Form {
    currency: string; language: string; dateFormat: string; numberFormat: string; timeFormat: string;
    indiaCompliance: boolean; multiCurrency: boolean; ess: boolean; mobileApp: boolean;
    aiChatbot: boolean; eSign: boolean; biometric: boolean; bankIntegration: boolean;
    emailNotif: boolean; whatsapp: boolean;
}
interface Step8Form { multiPlantMode: boolean; plantConfig: 'common' | 'per-plant'; }
interface Step9Form { dayStartTime: string; dayEndTime: string; weeklyOffs: string[]; }
interface Step12Form {
    ncEditMode: boolean; loadUnload: boolean; cycleTime: boolean;
    payrollLock: boolean; leaveCarryForward: boolean; overtimeApproval: boolean;
    mfa: boolean; backdatedEntry: boolean; docNumberLock: boolean;
}

const STEP_META = [
    { title: 'Company Identity', subtitle: 'Basic info & status' },
    { title: 'Statutory & Tax', subtitle: 'PAN, TAN, GSTIN, PF' },
    { title: 'Address', subtitle: 'Registered & corporate' },
    { title: 'Fiscal & Calendar', subtitle: 'FY, payroll, working days' },
    { title: 'Preferences', subtitle: 'Currency, language, flags' },
    { title: 'Branches', subtitle: 'Locations & geo-fencing' },
    { title: 'Key Contacts', subtitle: 'HR, Finance, IT contacts' },
    { title: 'Plants', subtitle: 'Multi-plant management' },
    { title: 'Shifts & Time', subtitle: 'Shift master & downtime' },
    { title: 'No. Series', subtitle: 'Document numbering' },
    { title: 'IOT Reasons', subtitle: 'Machine downtime reasons' },
    { title: 'System Controls', subtitle: 'Operational settings' },
    { title: 'Users', subtitle: 'Admin user creation' },
    { title: 'Activation', subtitle: 'Review & go live' },
];

// ============ MAIN COMPONENT ============

export function TenantOnboardingScreen() {
    const router = useRouter();
    const insets = useSafeAreaInsets();
    const { show: showConfirm, modalProps: confirmModalProps } = useConfirmModal();

    const [step, setStep] = React.useState(1);

    // Step 1
    const [step1, setStep1] = React.useState<Step1Form>({
        displayName: '', legalName: '', businessType: '', industry: '',
        companyCode: '', shortName: '', incorporationDate: '', employees: '',
        cin: '', website: '', emailDomain: '', status: 'Draft',
    });

    // Step 2
    const [step2, setStep2] = React.useState<Step2Form>({
        pan: '', tan: '', gstin: '', pfRegNo: '', esiCode: '', ptReg: '', lwfrNo: '', rocState: '',
    });

    // Step 3
    const [step3, setStep3] = React.useState<Step3Form>({
        regLine1: '', regLine2: '', regCity: '', regDistrict: '', regState: '',
        regCountry: 'India', regPin: '', regStdCode: '',
        sameAsRegistered: true, corpLine1: '', corpCity: '', corpState: '', corpPin: '',
    });

    // Step 4
    const [step4, setStep4] = React.useState<Step4Form>({
        fyStart: 'apr-mar', payrollFreq: 'Monthly', cutoffDay: 'Last Working Day',
        disbursementDay: '1st of Next Month', weekStart: 'Monday', timezone: 'IST UTC+5:30',
        workingDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
    });

    // Step 5
    const [step5, setStep5] = React.useState<Step5Form>({
        currency: 'INR — ₹', language: 'English', dateFormat: 'DD/MM/YYYY',
        numberFormat: 'Indian (2,00,000)', timeFormat: '12-hour (AM/PM)',
        indiaCompliance: true, multiCurrency: false, ess: true, mobileApp: true,
        aiChatbot: false, eSign: false, biometric: false, bankIntegration: false,
        emailNotif: false, whatsapp: false,
    });

    // Step 6
    const [branches, setBranches] = React.useState<Branch[]>([]);

    // Step 7
    const [contacts, setContacts] = React.useState<Contact[]>([
        { id: '1', name: '', designation: '', department: '', mobile: '', email: '', type: 'Primary', linkedin: '' },
    ]);

    // Step 8
    const [step8, setStep8] = React.useState<Step8Form>({ multiPlantMode: false, plantConfig: 'common' });
    const [plants, setPlants] = React.useState<Plant[]>([]);

    // Step 9
    const [step9, setStep9] = React.useState<Step9Form>({
        dayStartTime: '', dayEndTime: '', weeklyOffs: ['Sunday'],
    });
    const [shifts, setShifts] = React.useState<Shift[]>([]);

    // Step 10
    const [noSeries, setNoSeries] = React.useState<NoSeriesItem[]>([]);

    // Step 11
    const [iotReasons, setIotReasons] = React.useState<IOTReason[]>([]);

    // Step 12
    const [step12, setStep12] = React.useState<Step12Form>({
        ncEditMode: false, loadUnload: false, cycleTime: false,
        payrollLock: true, leaveCarryForward: true, overtimeApproval: false,
        mfa: false, backdatedEntry: false, docNumberLock: true,
    });

    // Step 13
    const [users, setUsers] = React.useState<UserItem[]>([
        { id: '1', fullName: '', username: '', password: '', role: 'Company Admin', email: '', mobile: '', department: '' },
    ]);

    const mergeStep1 = (updates: Partial<Step1Form>) => setStep1((prev) => ({ ...prev, ...updates }));
    const mergeStep2 = (updates: Partial<Step2Form>) => setStep2((prev) => ({ ...prev, ...updates }));
    const mergeStep3 = (updates: Partial<Step3Form>) => setStep3((prev) => ({ ...prev, ...updates }));
    const mergeStep4 = (updates: Partial<Step4Form>) => setStep4((prev) => ({ ...prev, ...updates }));
    const mergeStep5 = (updates: Partial<Step5Form>) => setStep5((prev) => ({ ...prev, ...updates }));
    const mergeStep8 = (updates: Partial<Step8Form>) => setStep8((prev) => ({ ...prev, ...updates }));
    const mergeStep9 = (updates: Partial<Step9Form>) => setStep9((prev) => ({ ...prev, ...updates }));
    const mergeStep12 = (updates: Partial<Step12Form>) => setStep12((prev) => ({ ...prev, ...updates }));

    const handleBack = () => {
        if (step > 1) {
            setStep(step - 1);
        } else {
            showConfirm({
                title: 'Discard Changes?',
                message: 'All unsaved onboarding data will be lost.',
                variant: 'warning',
                confirmText: 'Discard',
                onConfirm: () => router.back(),
            });
        }
    };

    const handleNext = () => {
        if (step < TOTAL_STEPS) setStep(step + 1);
    };

    const handleCreateCompany = () => {
        showConfirm({
            title: 'Create Company',
            message: `Create ${step1.displayName || 'new company'} with status "${step1.status}"? The tenant will be provisioned on the platform.`,
            variant: 'primary',
            confirmText: 'Create',
            onConfirm: () => {
                // TODO: API call with all form data
                router.back();
            },
        });
    };

    const handleSaveDraft = () => {
        // TODO: persist draft
    };

    const isLastStep = step === TOTAL_STEPS;
    const meta = STEP_META[step - 1];

    const renderStep = () => {
        switch (step) {
            case 1: return <Step1Identity form={step1} setForm={mergeStep1} />;
            case 2: return <Step2Statutory form={step2} setForm={mergeStep2} />;
            case 3: return <Step3Address form={step3} setForm={mergeStep3} />;
            case 4: return <Step4Fiscal form={step4} setForm={mergeStep4} />;
            case 5: return <Step5Preferences form={step5} setForm={mergeStep5} />;
            case 6: return <Step6Branches branches={branches} setBranches={setBranches} />;
            case 7: return <Step7Contacts contacts={contacts} setContacts={setContacts} />;
            case 8: return <Step8Plants form={step8} setForm={mergeStep8} plants={plants} setPlants={setPlants} />;
            case 9: return <Step9Shifts form={step9} setForm={mergeStep9} shifts={shifts} setShifts={setShifts} />;
            case 10: return <Step10NoSeries noSeries={noSeries} setNoSeries={setNoSeries} />;
            case 11: return <Step11IOTReasons reasons={iotReasons} setReasons={setIotReasons} />;
            case 12: return <Step12Controls form={step12} setForm={mergeStep12} />;
            case 13: return <Step13Users users={users} setUsers={setUsers} />;
            case 14: return (
                <Step14Activation
                    companyName={step1.displayName}
                    currentStatus={step1.status}
                    onStatusChange={(s) => mergeStep1({ status: s })}
                />
            );
            default: return null;
        }
    };

    return (
        <View style={styles.container}>
            <LinearGradient
                colors={[colors.gradient.surface, colors.white]}
                style={StyleSheet.absoluteFill}
            />

            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={{ flex: 1 }}
                keyboardVerticalOffset={0}
            >
                {/* ---- Header ---- */}
                <Animated.View
                    entering={FadeInDown.duration(350)}
                    style={[styles.header, { paddingTop: insets.top + 8 }]}
                >
                    <Pressable onPress={handleBack} style={styles.headerBackBtn}>
                        <ChevronLeft size={20} color={colors.primary[600]} strokeWidth={2} />
                    </Pressable>

                    <View style={styles.headerCenter}>
                        <Text className="font-inter text-base font-bold text-primary-950">
                            {meta.title}
                        </Text>
                        <Text className="font-inter text-xs text-neutral-500">
                            Step {step} of {TOTAL_STEPS} · {meta.subtitle}
                        </Text>
                    </View>

                    <Pressable onPress={handleSaveDraft} style={styles.saveDraftBtn}>
                        <Text className="font-inter text-xs font-semibold text-primary-500">
                            Save Draft
                        </Text>
                    </Pressable>
                </Animated.View>

                {/* ---- Step Indicator ---- */}
                <StepIndicator currentStep={step} totalSteps={TOTAL_STEPS} />

                {/* ---- Content ---- */}
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 120 }]}
                    keyboardShouldPersistTaps="handled"
                    bounces={false}
                >
                    <Animated.View key={step} entering={SlideInRight.duration(280)} exiting={SlideOutLeft.duration(200)}>
                        {renderStep()}
                    </Animated.View>
                </ScrollView>

                {/* ---- Bottom CTA ---- */}
                <Animated.View
                    entering={FadeIn.duration(300)}
                    style={[styles.bottomCTA, { paddingBottom: insets.bottom + 12 }]}
                >
                    {step > 1 && (
                        <Pressable onPress={handleBack} style={styles.prevButton}>
                            <ChevronLeft size={18} color={colors.primary[600]} strokeWidth={2} />
                        </Pressable>
                    )}

                    <Pressable
                        onPress={isLastStep ? handleCreateCompany : handleNext}
                        style={styles.nextBtnWrapper}
                    >
                        <LinearGradient
                            colors={[colors.gradient.start, colors.gradient.end]}
                            start={{ x: 0, y: 0 }}
                            end={{ x: 1, y: 0 }}
                            style={styles.nextBtn}
                        >
                            <Text className="font-inter text-base font-bold text-white">
                                {isLastStep ? 'Create Company' : 'Continue'}
                            </Text>
                            {!isLastStep && (
                                <ChevronRight size={18} color="#fff" strokeWidth={2} />
                            )}
                        </LinearGradient>
                    </Pressable>
                </Animated.View>
            </KeyboardAvoidingView>

            <ConfirmModal {...confirmModalProps} />
        </View>
    );
}

// ============ STYLES ============

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.gradient.surface },

    // Header
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingBottom: 8,
    },
    headerBackBtn: {
        width: 36,
        height: 36,
        borderRadius: 11,
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
    },
    headerCenter: { flex: 1, alignItems: 'center' },
    saveDraftBtn: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 10,
        backgroundColor: colors.primary[50],
    },

    // Step Indicator
    stepIndicatorWrap: { paddingHorizontal: 20, paddingBottom: 8 },
    stepIndicatorContent: { alignItems: 'center', paddingVertical: 4 },
    stepDot: {
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: colors.neutral[200],
        justifyContent: 'center',
        alignItems: 'center',
    },
    stepDotActive: { backgroundColor: colors.primary[600] },
    stepDotCompleted: { backgroundColor: colors.success[500] },
    stepLine: { width: 16, height: 2, backgroundColor: colors.neutral[200], marginHorizontal: 3 },
    stepLineCompleted: { backgroundColor: colors.success[400] },
    stepProgress: {
        height: 3,
        borderRadius: 2,
        backgroundColor: colors.neutral[200],
        marginTop: 8,
        overflow: 'hidden',
    },
    stepProgressFill: {
        height: '100%',
        backgroundColor: colors.primary[500],
        borderRadius: 2,
    },

    // Scroll Content
    scrollContent: { paddingHorizontal: 20, paddingTop: 8 },

    // Form atoms
    fieldWrap: { marginBottom: 14 },
    fieldInput: {
        backgroundColor: colors.white,
        borderRadius: 12,
        borderWidth: 1.5,
        borderColor: colors.neutral[200],
        paddingHorizontal: 14,
        height: 48,
        justifyContent: 'center',
    },
    textInput: {
        fontSize: 14,
        color: colors.primary[950],
        fontFamily: 'Inter',
    },
    chipRow: { flexDirection: 'row', gap: 8, paddingVertical: 4 },
    chipGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, paddingVertical: 4 },
    chip: {
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: 20,
        backgroundColor: colors.white,
        borderWidth: 1.5,
        borderColor: colors.neutral[200],
    },
    chipActive: {
        backgroundColor: colors.primary[600],
        borderColor: colors.primary[600],
    },
    toggleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: colors.neutral[100],
    },
    radioOption: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
        padding: 14,
        borderRadius: 12,
        backgroundColor: colors.white,
        borderWidth: 1.5,
        borderColor: colors.neutral[200],
        marginBottom: 8,
    },
    radioOptionActive: {
        borderColor: colors.primary[400],
        backgroundColor: colors.primary[50],
    },
    radioCircle: {
        width: 20,
        height: 20,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: colors.neutral[300],
        justifyContent: 'center',
        alignItems: 'center',
        flexShrink: 0,
    },
    radioCircleActive: { borderColor: colors.primary[500] },
    radioInner: {
        width: 10,
        height: 10,
        borderRadius: 5,
        backgroundColor: colors.primary[600],
    },
    recommendedBadge: {
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 6,
        backgroundColor: colors.success[50],
    },
    sectionCard: {
        backgroundColor: colors.white,
        borderRadius: 16,
        padding: 16,
        marginBottom: 16,
        shadowColor: colors.primary[900],
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.04,
        shadowRadius: 8,
        elevation: 2,
        borderWidth: 1,
        borderColor: colors.primary[50],
    },
    infoCard: {
        backgroundColor: colors.primary[50],
        borderRadius: 12,
        padding: 14,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: colors.primary[100],
    },
    warningBanner: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        backgroundColor: colors.warning[50],
        borderRadius: 12,
        padding: 14,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: colors.warning[200],
    },
    itemCard: {
        backgroundColor: colors.white,
        borderRadius: 16,
        padding: 16,
        marginBottom: 12,
        borderWidth: 1.5,
        borderColor: colors.neutral[200],
        shadowColor: colors.primary[900],
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.04,
        shadowRadius: 8,
        elevation: 2,
    },
    hqCard: {
        borderColor: colors.primary[300],
        backgroundColor: colors.primary[50],
    },
    itemCardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    itemCardBadge: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 8,
        backgroundColor: colors.primary[100],
    },
    addButton: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        paddingVertical: 14,
        borderRadius: 12,
        borderWidth: 1.5,
        borderColor: colors.primary[200],
        borderStyle: 'dashed',
        justifyContent: 'center',
        marginBottom: 16,
        backgroundColor: colors.primary[50],
    },
    deleteIconBtn: {
        width: 32,
        height: 32,
        borderRadius: 8,
        backgroundColor: colors.danger[50],
        justifyContent: 'center',
        alignItems: 'center',
    },
    smallAddButton: {
        paddingVertical: 8,
        alignItems: 'center',
    },
    twoColumn: {
        flexDirection: 'row',
        gap: 10,
    },
    checkboxRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
        marginBottom: 12,
    },
    checkbox: {
        width: 22,
        height: 22,
        borderRadius: 6,
        borderWidth: 2,
        borderColor: colors.neutral[300],
        justifyContent: 'center',
        alignItems: 'center',
    },
    checkboxActive: {
        backgroundColor: colors.primary[600],
        borderColor: colors.primary[600],
    },
    dayToggleRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 10,
        paddingHorizontal: 4,
        borderBottomWidth: 1,
        borderBottomColor: colors.neutral[100],
    },
    dayToggleRowActive: {},
    dayBadge: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 8,
    },
    hqToggleBtn: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 8,
        backgroundColor: colors.neutral[100],
        marginRight: 8,
    },
    hqToggleBtnActive: {
        backgroundColor: colors.primary[100],
    },
    rowCenter: { flexDirection: 'row', alignItems: 'center' },
    slotRow: { flexDirection: 'row', gap: 8, alignItems: 'flex-end', marginBottom: 8 },
    previewBox: {
        backgroundColor: colors.primary[50],
        borderRadius: 10,
        padding: 12,
        marginTop: 4,
        alignItems: 'center',
    },
    logoUpload: {
        flexDirection: 'row',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 14,
        padding: 16,
        borderRadius: 12,
        borderWidth: 1.5,
        borderColor: colors.primary[200],
        borderStyle: 'dashed',
        backgroundColor: colors.primary[50],
        overflow: 'hidden',
    },
    logoPlaceholder: {
        width: 56,
        height: 56,
        borderRadius: 14,
        backgroundColor: colors.primary[100],
        justifyContent: 'center',
        alignItems: 'center',
    },
    logoUploadText: {
        flex: 1,
        flexShrink: 1,
        flexBasis: 0,
        minWidth: 0,
        overflow: 'hidden',
    },
    // Activation
    activationHero: {
        borderRadius: 20,
        padding: 32,
        alignItems: 'center',
        marginBottom: 16,
        overflow: 'hidden',
    },
    activationCircle1: {
        position: 'absolute', top: -30, right: -30, width: 120, height: 120,
        borderRadius: 60, backgroundColor: 'rgba(255,255,255,0.08)',
    },
    activationCircle2: {
        position: 'absolute', bottom: -20, left: -20, width: 80, height: 80,
        borderRadius: 40, backgroundColor: 'rgba(255,255,255,0.06)',
    },
    statusOption: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
        padding: 14,
        borderRadius: 12,
        backgroundColor: colors.white,
        borderWidth: 1.5,
        borderColor: colors.neutral[200],
        marginBottom: 8,
    },
    statusOptionActive: {
        borderColor: colors.primary[400],
        backgroundColor: colors.primary[50],
    },
    statusDot: { width: 12, height: 12, borderRadius: 6, flexShrink: 0 },
    checklistPhase: { marginBottom: 12 },
    checklistItem: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 3,
    },

    // Bottom CTA
    bottomCTA: {
        flexDirection: 'row',
        gap: 10,
        paddingHorizontal: 20,
        paddingTop: 12,
        borderTopWidth: 1,
        borderTopColor: colors.neutral[100],
        backgroundColor: colors.white,
    },
    prevButton: {
        width: 52,
        height: 56,
        borderRadius: 16,
        borderWidth: 1.5,
        borderColor: colors.primary[200],
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
    },
    nextBtnWrapper: {
        flex: 1,
        borderRadius: 16,
        overflow: 'hidden',
        shadowColor: colors.primary[500],
        shadowOffset: { width: 0, height: 6 },
        shadowOpacity: 0.3,
        shadowRadius: 12,
        elevation: 6,
    },
    nextBtn: {
        height: 56,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'row',
        gap: 8,
    },
});

