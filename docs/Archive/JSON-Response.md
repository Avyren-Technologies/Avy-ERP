## API - `http://localhost:3030/api/v1/platform/tenants/onboard`
- JSON Payload:
```json
{"identity":{"displayName":"Chetan Technologies","legalName":"Chetan Technologies PVT LTD","businessType":"Private Limited (Pvt. Ltd.)","industry":"IT","companyCode":"AUTO-CHETAN","shortName":"CHET","incorporationDate":"05/03/2026","cin":"U72900KA2022PTC145678","website":"https://avexora-tech.com","emailDomain":"avexora-tech.com","logoUrl":"blob:http://localhost:5173/bd3cad21-2500-4f07-b99b-68d62609fef4","wizardStatus":"Active"},"statutory":{"pan":"AAVCS7832K","tan":"BLRA04567C","gstin":"29AAVCS7832K1Z5","pfRegNo":"KA/BLR/0456789/000/0001","esiCode":"53-00-987654-000-0001","ptReg":"KA-PT-2023-0456789","lwfrNo":"KA-LWF-0456789","rocState":"Karnataka"},"address":{"registered":{"line1":"Plot No. 45, 2nd Floor, Orion Tech Park, Outer Ring Road","line2":"Near Ecospace Business Park, Bellandur","city":"Bengaluru","district":"Bengaluru Urban","state":"Karnataka","pin":"560103","country":"India","stdCode":"080"},"sameAsRegistered":false,"corporate":{"line1":"No. 128, 1st Main Road, 5th Block, Jayanagar","line2":"Opposite Jayanagar Metro Station","city":"Bengaluru","district":"Bengaluru Urban","state":"Karnataka","pin":"560041","country":"India","stdCode":"080"}},"fiscal":{"fyType":"apr-mar","payrollFreq":"Monthly","cutoffDay":"28","disbursementDay":"1","weekStart":"Monday","timezone":"IST UTC+5:30","workingDays":["Monday","Tuesday","Wednesday","Thursday","Friday"]},"preferences":{"currency":"INR — ₹","language":"English","dateFormat":"DD/MM/YYYY","numberFormat":"Indian (2,00,000)","timeFormat":"12-hour (AM/PM)","indiaCompliance":true,"multiCurrency":false,"ess":false,"mobileApp":true,"webApp":true,"systemApp":true,"aiChatbot":false,"eSign":false,"biometric":false,"bankIntegration":true,"emailNotif":true,"whatsapp":false,"razorpayEnabled":false,"razorpayAutoDisbursement":false,"razorpayTestMode":true},"endpoint":{"endpointType":"custom","customBaseUrl":"https://avyerp.com/chetan/api/v1"},"strategy":{"multiLocationMode":true,"locationConfig":"per-location"},"locations":[{"name":"Bengaluru HQ","code":"BLR-HQ-01","facilityType":"Head Office","status":"Active","isHQ":true,"addressLine1":"Plot No. 45, 2nd Floor, Orion Tech Park, Outer Ring Road","addressLine2":"Near Ecospace Business Park, Bellandur","city":"Bengaluru","district":"Bengaluru Urban","state":"Karnataka","pin":"560104","country":"India","gstin":"29AAVCS7832K1Z5","contactName":"Rohit Sharma","contactDesignation":"Plant Head","contactEmail":"rohit@chetan.com","contactCountryCode":"+91","contactPhone":"9876543210","geoEnabled":true,"geoLocationName":"Factory Main Gate","geoLat":"12.9716","geoLng":"77.594","geoRadius":100,"geoShape":"circle","moduleIds":["hr","production","vendor","visitor"],"customModulePricing":{},"userTier":"starter","billingCycle":"monthly","trialDays":14},{"name":"Mumbai Regional Office","code":"BOM-RO-02","facilityType":"Regional Office","status":"Active","isHQ":false,"addressLine1":"401, Sapphire IT Park, Powai","addressLine2":"Saki Vihar Road","city":"Mumbai","district":"Mumbai Suburban","state":"Maharashtra","pin":"400076","country":"India","gstin":"27AAACZ1234F1Z6","contactName":"Rajesh Kumar","contactDesignation":"Regional Head","contactEmail":"rajesh.kumar@chetan.com","contactCountryCode":"+91","contactPhone":"737383272","geoEnabled":true,"geoLocationName":"Powai Office Building","geoLat":"19.1176","geoLng":"72.9060","geoRadius":200,"geoShape":"circle","moduleIds":["hr","production","vendor","visitor"],"customModulePricing":{},"userTier":"starter","billingCycle":"monthly","trialDays":14}],"contacts":[{"name":"Rohan Mehta","designation":"Chief Financial Officer","department":"Finance","type":"Primary","email":"rohan.mehta@dummycompany.in","countryCode":"+91","mobile":"9876500001","linkedin":"https://www.google.com/search?q=https://linkedin.com/in/rohanmehta-dummy"},{"name":"Anita Desai","designation":"Head of Legal","department":"Legal","type":"Legal Contact","email":"anita.desai@dummycompany.in","countryCode":"+91","mobile":"9876543210","linkedin":"https://www.google.com/search?q=https://linkedin.com/in/anitadesai-dummy"}],"shifts":{"dayStartTime":"06:00","dayEndTime":"17:59","weeklyOffs":["Sunday"],"items":[{"name":"Morning Shift","fromTime":"06:00","toTime":"14:00","noShuffle":false,"downtimeSlots":[{"id":"1773901738812","type":"Tea Break","duration":"15"},{"id":"1773901786211","type":"Lunch Break","duration":"30"}]},{"name":"Afternoon Shift","fromTime":"14:00","toTime":"22:00","noShuffle":false,"downtimeSlots":[{"id":"1773901742145","type":"Tea Break","duration":"15"},{"id":"1773901805461","type":"Other","duration":"30"}]},{"name":"Night Shift","fromTime":"22:00","toTime":"05:59","noShuffle":false,"downtimeSlots":[{"id":"1773901745279","type":"Other","duration":"30"},{"id":"1773901748995","type":"Other","duration":"15"}]}]},"noSeries":[{"code":"WO","linkedScreen":"Work Order","description":"Work Order","prefix":"WO-","suffix":"Fy-2025-","numberCount":4,"startNumber":1},{"code":"GRN","linkedScreen":"Goods Return","description":"Goods Receipt Note","prefix":"GRN","suffix":"-FY-26-","numberCount":4,"startNumber":1}],"iotReasons":[{"reasonType":"Machine Idle","reason":"Tool Breakage","description":"Tool Breakage","department":"Production","planned":true,"duration":"7"}],"controls":{"ncEditMode":true,"loadUnload":true,"cycleTime":true,"payrollLock":true,"leaveCarryForward":true,"overtimeApproval":true,"mfa":true},"users":[{"fullName":"Rahul Kulkarni","username":"rahul_kulkarni","password":"Rahul@9889","role":"Company Admin","email":"rahul.kulkarni@avyren.com","mobile":"986363722"}]}
```

## API - `http://localhost:3030/api/v1/platform/tenants/onboard`
- JSON Response:

```json
{
    "success": true,
    "data": {
        "id": "cmmx3k1w3000111cgp5ln4aze",
        "name": "Chetan Technologies",
        "industry": "IT",
        "size": "SMALL",
        "website": "https://avexora-tech.com",
        "gstNumber": "29AAVCS7832K1Z5",
        "address": null,
        "contactPerson": null,
        "createdAt": "2026-03-19T06:36:19.732Z",
        "updatedAt": "2026-03-19T06:36:19.732Z",
        "displayName": "Chetan Technologies",
        "legalName": "Chetan Technologies PVT LTD",
        "shortName": "CHET",
        "businessType": "Private Limited (Pvt. Ltd.)",
        "companyCode": "AUTO-CHETAN",
        "cin": "U72900KA2022PTC145678",
        "incorporationDate": "05/03/2026",
        "employeeCount": null,
        "emailDomain": "avexora-tech.com",
        "logoUrl": "blob:http://localhost:5173/bd3cad21-2500-4f07-b99b-68d62609fef4",
        "pan": "AAVCS7832K",
        "tan": "BLRA04567C",
        "gstin": "29AAVCS7832K1Z5",
        "pfRegNo": "KA/BLR/0456789/000/0001",
        "esiCode": "53-00-987654-000-0001",
        "ptReg": "KA-PT-2023-0456789",
        "lwfrNo": "KA-LWF-0456789",
        "rocState": "Karnataka",
        "registeredAddress": {
            "pin": "560103",
            "city": "Bengaluru",
            "line1": "Plot No. 45, 2nd Floor, Orion Tech Park, Outer Ring Road",
            "line2": "Near Ecospace Business Park, Bellandur",
            "state": "Karnataka",
            "country": "India",
            "stdCode": "080",
            "district": "Bengaluru Urban"
        },
        "corporateAddress": {
            "pin": "560041",
            "city": "Bengaluru",
            "line1": "No. 128, 1st Main Road, 5th Block, Jayanagar",
            "line2": "Opposite Jayanagar Metro Station",
            "state": "Karnataka",
            "country": "India",
            "stdCode": "080",
            "district": "Bengaluru Urban"
        },
        "sameAsRegistered": false,
        "fiscalConfig": {
            "fyType": "apr-mar",
            "timezone": "IST UTC+5:30",
            "cutoffDay": "28",
            "weekStart": "Monday",
            "payrollFreq": "Monthly",
            "workingDays": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday"
            ],
            "disbursementDay": "1"
        },
        "preferences": {
            "ess": false,
            "eSign": false,
            "webApp": true,
            "currency": "INR — ₹",
            "language": "English",
            "whatsapp": false,
            "aiChatbot": false,
            "biometric": false,
            "mobileApp": true,
            "systemApp": true,
            "dateFormat": "DD/MM/YYYY",
            "emailNotif": true,
            "timeFormat": "12-hour (AM/PM)",
            "numberFormat": "Indian (2,00,000)",
            "multiCurrency": false,
            "bankIntegration": true,
            "indiaCompliance": true
        },
        "razorpayConfig": null,
        "endpointType": "custom",
        "customEndpointUrl": "https://avyerp.com/chetan/api/v1",
        "multiLocationMode": true,
        "locationConfig": "per-location",
        "selectedModuleIds": null,
        "customModulePricing": null,
        "userTier": null,
        "customUserLimit": null,
        "customTierPrice": null,
        "billingCycle": "monthly",
        "trialDays": 0,
        "dayStartTime": "06:00",
        "dayEndTime": "17:59",
        "weeklyOffs": [
            "Sunday"
        ],
        "systemControls": {
            "mfa": true,
            "cycleTime": true,
            "loadUnload": true,
            "ncEditMode": true,
            "payrollLock": true,
            "overtimeApproval": true,
            "leaveCarryForward": true
        },
        "wizardStatus": "Active",
        "locations": [
            {
                "id": "cmmx3k1wb000411cg9kf5lbrm",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Bengaluru HQ",
                "code": "BLR-HQ-01",
                "facilityType": "Head Office",
                "customFacilityType": null,
                "status": "Active",
                "isHQ": true,
                "addressLine1": "Plot No. 45, 2nd Floor, Orion Tech Park, Outer Ring Road",
                "addressLine2": "Near Ecospace Business Park, Bellandur",
                "city": "Bengaluru",
                "district": "Bengaluru Urban",
                "state": "Karnataka",
                "pin": "560104",
                "country": "India",
                "stdCode": null,
                "gstin": "29AAVCS7832K1Z5",
                "stateGST": null,
                "contactName": "Rohit Sharma",
                "contactDesignation": "Plant Head",
                "contactEmail": "rohit@chetan.com",
                "contactCountryCode": "+91",
                "contactPhone": "9876543210",
                "geoEnabled": true,
                "geoLocationName": "Factory Main Gate",
                "geoLat": "12.9716",
                "geoLng": "77.594",
                "geoRadius": 100,
                "geoShape": "circle",
                "moduleIds": [
                    "hr",
                    "production",
                    "vendor",
                    "visitor"
                ],
                "customModulePricing": {},
                "userTier": "starter",
                "customUserLimit": null,
                "customTierPrice": null,
                "billingCycle": "monthly",
                "trialDays": 14,
                "createdAt": "2026-03-19T06:36:19.739Z",
                "updatedAt": "2026-03-19T06:36:19.739Z"
            },
            {
                "id": "cmmx3k1wb000511cg1j0vd0ke",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Mumbai Regional Office",
                "code": "BOM-RO-02",
                "facilityType": "Regional Office",
                "customFacilityType": null,
                "status": "Active",
                "isHQ": false,
                "addressLine1": "401, Sapphire IT Park, Powai",
                "addressLine2": "Saki Vihar Road",
                "city": "Mumbai",
                "district": "Mumbai Suburban",
                "state": "Maharashtra",
                "pin": "400076",
                "country": "India",
                "stdCode": null,
                "gstin": "27AAACZ1234F1Z6",
                "stateGST": null,
                "contactName": "Rajesh Kumar",
                "contactDesignation": "Regional Head",
                "contactEmail": "rajesh.kumar@chetan.com",
                "contactCountryCode": "+91",
                "contactPhone": "737383272",
                "geoEnabled": true,
                "geoLocationName": "Powai Office Building",
                "geoLat": "19.1176",
                "geoLng": "72.9060",
                "geoRadius": 200,
                "geoShape": "circle",
                "moduleIds": [
                    "hr",
                    "production",
                    "vendor",
                    "visitor"
                ],
                "customModulePricing": {},
                "userTier": "starter",
                "customUserLimit": null,
                "customTierPrice": null,
                "billingCycle": "monthly",
                "trialDays": 14,
                "createdAt": "2026-03-19T06:36:19.739Z",
                "updatedAt": "2026-03-19T06:36:19.739Z"
            }
        ],
        "contacts": [
            {
                "id": "cmmx3k1wc000611cgxknyy1uz",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Rohan Mehta",
                "designation": "Chief Financial Officer",
                "department": "Finance",
                "type": "Primary",
                "email": "rohan.mehta@dummycompany.in",
                "countryCode": "+91",
                "mobile": "9876500001",
                "linkedin": "https://www.google.com/search?q=https://linkedin.com/in/rohanmehta-dummy",
                "createdAt": "2026-03-19T06:36:19.741Z",
                "updatedAt": "2026-03-19T06:36:19.741Z"
            },
            {
                "id": "cmmx3k1wc000711cgsbtwd2fq",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Anita Desai",
                "designation": "Head of Legal",
                "department": "Legal",
                "type": "Legal Contact",
                "email": "anita.desai@dummycompany.in",
                "countryCode": "+91",
                "mobile": "9876543210",
                "linkedin": "https://www.google.com/search?q=https://linkedin.com/in/anitadesai-dummy",
                "createdAt": "2026-03-19T06:36:19.741Z",
                "updatedAt": "2026-03-19T06:36:19.741Z"
            }
        ],
        "shifts": [
            {
                "id": "cmmx3k1we000811cgs616mynt",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Morning Shift",
                "fromTime": "06:00",
                "toTime": "14:00",
                "noShuffle": false,
                "downtimeSlots": [
                    {
                        "type": "Tea Break",
                        "duration": "15"
                    },
                    {
                        "type": "Lunch Break",
                        "duration": "30"
                    }
                ],
                "createdAt": "2026-03-19T06:36:19.742Z",
                "updatedAt": "2026-03-19T06:36:19.742Z"
            },
            {
                "id": "cmmx3k1we000911cgy917buft",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Afternoon Shift",
                "fromTime": "14:00",
                "toTime": "22:00",
                "noShuffle": false,
                "downtimeSlots": [
                    {
                        "type": "Tea Break",
                        "duration": "15"
                    },
                    {
                        "type": "Other",
                        "duration": "30"
                    }
                ],
                "createdAt": "2026-03-19T06:36:19.742Z",
                "updatedAt": "2026-03-19T06:36:19.742Z"
            },
            {
                "id": "cmmx3k1we000a11cgllb5xc58",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Night Shift",
                "fromTime": "22:00",
                "toTime": "05:59",
                "noShuffle": false,
                "downtimeSlots": [
                    {
                        "type": "Other",
                        "duration": "30"
                    },
                    {
                        "type": "Other",
                        "duration": "15"
                    }
                ],
                "createdAt": "2026-03-19T06:36:19.742Z",
                "updatedAt": "2026-03-19T06:36:19.742Z"
            }
        ],
        "noSeries": [
            {
                "id": "cmmx3k1wf000c11cg1wzpf4o7",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "code": "GRN",
                "linkedScreen": "Goods Return",
                "description": "Goods Receipt Note",
                "prefix": "GRN",
                "suffix": "-FY-26-",
                "numberCount": 4,
                "startNumber": 1,
                "createdAt": "2026-03-19T06:36:19.743Z",
                "updatedAt": "2026-03-19T06:36:19.743Z"
            },
            {
                "id": "cmmx3k1wf000b11cgd6d17kyk",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "code": "WO",
                "linkedScreen": "Work Order",
                "description": "Work Order",
                "prefix": "WO-",
                "suffix": "Fy-2025-",
                "numberCount": 4,
                "startNumber": 1,
                "createdAt": "2026-03-19T06:36:19.743Z",
                "updatedAt": "2026-03-19T06:36:19.743Z"
            }
        ],
        "iotReasons": [
            {
                "id": "cmmx3k1wg000d11cgbu62l3id",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "reasonType": "Machine Idle",
                "reason": "Tool Breakage",
                "description": "Tool Breakage",
                "department": "Production",
                "planned": true,
                "duration": "7",
                "createdAt": "2026-03-19T06:36:19.744Z",
                "updatedAt": "2026-03-19T06:36:19.744Z"
            }
        ],
        "tenant": {
            "id": "cmmx3k1w8000311cgsed4551r",
            "schemaName": "tenant_cmmx3k1w3000111cgp5ln4aze",
            "companyId": "cmmx3k1w3000111cgp5ln4aze",
            "status": "ACTIVE",
            "createdAt": "2026-03-19T06:36:19.736Z",
            "updatedAt": "2026-03-19T06:36:19.736Z",
            "subscriptions": [
                {
                    "id": "cmmx3k1wh000f11cgnkuwopq6",
                    "tenantId": "cmmx3k1w8000311cgsed4551r",
                    "planId": "starter",
                    "userTier": "STARTER",
                    "billingCycle": "MONTHLY",
                    "modules": {},
                    "status": "ACTIVE",
                    "startDate": "2026-03-19T06:36:19.745Z",
                    "endDate": null,
                    "trialEndsAt": "2026-04-02T06:36:19.745Z",
                    "createdAt": "2026-03-19T06:36:19.745Z",
                    "updatedAt": "2026-03-19T06:36:19.745Z"
                }
            ]
        },
        "users": [
            {
                "id": "cmmx3k22n000h11cgz5si0paw",
                "email": "rahul.kulkarni@avyren.com",
                "firstName": "Rahul",
                "lastName": "Kulkarni",
                "phone": "986363722",
                "role": "COMPANY_ADMIN",
                "isActive": true,
                "lastLogin": null,
                "createdAt": "2026-03-19T06:36:19.968Z"
            }
        ]
    },
    "message": "Tenant onboarded successfully"
}
```

## API - `http://localhost:3030/api/v1/platform/companies?page=1&limit=25`

- JSON Response:

```json
{
    "success": true,
    "data": [
        {
            "id": "cmmx3k1w3000111cgp5ln4aze",
            "name": "Chetan Technologies",
            "industry": "IT",
            "size": "SMALL",
            "website": "https://avexora-tech.com",
            "gstNumber": "29AAVCS7832K1Z5",
            "address": null,
            "contactPerson": null,
            "createdAt": "2026-03-19T06:36:19.732Z",
            "updatedAt": "2026-03-19T06:36:19.732Z",
            "displayName": "Chetan Technologies",
            "legalName": "Chetan Technologies PVT LTD",
            "shortName": "CHET",
            "businessType": "Private Limited (Pvt. Ltd.)",
            "companyCode": "AUTO-CHETAN",
            "cin": "U72900KA2022PTC145678",
            "incorporationDate": "05/03/2026",
            "employeeCount": null,
            "emailDomain": "avexora-tech.com",
            "logoUrl": "blob:http://localhost:5173/bd3cad21-2500-4f07-b99b-68d62609fef4",
            "pan": "AAVCS7832K",
            "tan": "BLRA04567C",
            "gstin": "29AAVCS7832K1Z5",
            "pfRegNo": "KA/BLR/0456789/000/0001",
            "esiCode": "53-00-987654-000-0001",
            "ptReg": "KA-PT-2023-0456789",
            "lwfrNo": "KA-LWF-0456789",
            "rocState": "Karnataka",
            "registeredAddress": {
                "pin": "560103",
                "city": "Bengaluru",
                "line1": "Plot No. 45, 2nd Floor, Orion Tech Park, Outer Ring Road",
                "line2": "Near Ecospace Business Park, Bellandur",
                "state": "Karnataka",
                "country": "India",
                "stdCode": "080",
                "district": "Bengaluru Urban"
            },
            "corporateAddress": {
                "pin": "560041",
                "city": "Bengaluru",
                "line1": "No. 128, 1st Main Road, 5th Block, Jayanagar",
                "line2": "Opposite Jayanagar Metro Station",
                "state": "Karnataka",
                "country": "India",
                "stdCode": "080",
                "district": "Bengaluru Urban"
            },
            "sameAsRegistered": false,
            "fiscalConfig": {
                "fyType": "apr-mar",
                "timezone": "IST UTC+5:30",
                "cutoffDay": "28",
                "weekStart": "Monday",
                "payrollFreq": "Monthly",
                "workingDays": [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday"
                ],
                "disbursementDay": "1"
            },
            "preferences": {
                "ess": false,
                "eSign": false,
                "webApp": true,
                "currency": "INR — ₹",
                "language": "English",
                "whatsapp": false,
                "aiChatbot": false,
                "biometric": false,
                "mobileApp": true,
                "systemApp": true,
                "dateFormat": "DD/MM/YYYY",
                "emailNotif": true,
                "timeFormat": "12-hour (AM/PM)",
                "numberFormat": "Indian (2,00,000)",
                "multiCurrency": false,
                "bankIntegration": true,
                "indiaCompliance": true
            },
            "endpointType": "custom",
            "customEndpointUrl": "https://avyerp.com/chetan/api/v1",
            "multiLocationMode": true,
            "locationConfig": "per-location",
            "selectedModuleIds": null,
            "customModulePricing": null,
            "userTier": null,
            "customUserLimit": null,
            "customTierPrice": null,
            "billingCycle": "monthly",
            "trialDays": 0,
            "dayStartTime": "06:00",
            "dayEndTime": "17:59",
            "weeklyOffs": [
                "Sunday"
            ],
            "systemControls": {
                "mfa": true,
                "cycleTime": true,
                "loadUnload": true,
                "ncEditMode": true,
                "payrollLock": true,
                "overtimeApproval": true,
                "leaveCarryForward": true
            },
            "wizardStatus": "Active",
            "tenant": {
                "id": "cmmx3k1w8000311cgsed4551r",
                "schemaName": "tenant_cmmx3k1w3000111cgp5ln4aze",
                "status": "ACTIVE"
            },
            "_count": {
                "locations": 2,
                "contacts": 2,
                "users": 1
            }
        },
        {
            "id": "cmmwiuqjy0001iq6tan93n0y6",
            "name": "Avyren Technologies",
            "industry": "IT",
            "size": "SMALL",
            "website": "https://avyrentechnologies.com",
            "gstNumber": "29AAKPC1234L1Z5",
            "address": null,
            "contactPerson": null,
            "createdAt": "2026-03-18T20:56:46.318Z",
            "updatedAt": "2026-03-18T21:09:48.771Z",
            "displayName": "Avyren Technologies",
            "legalName": "Avyren Technologies PVT LTD",
            "shortName": "AVY",
            "businessType": "Private Limited (Pvt. Ltd.)",
            "companyCode": "AVY-01",
            "cin": "U782CH728SHHSS78",
            "incorporationDate": "25/10/2025",
            "employeeCount": null,
            "emailDomain": "avyrentechnologies.com",
            "logoUrl": "blob:http://localhost:5173/4f7bb3e8-9196-452b-b41c-c7c5aad277bc",
            "pan": "AAKPC1234L",
            "tan": "BLRA12345B",
            "gstin": "29AAKPC1234L1Z5",
            "pfRegNo": "KA/BLR/1234567/000/0001",
            "esiCode": "53-00-987654-000-0001",
            "ptReg": "KA/PT/2023/123456",
            "lwfrNo": "KALWF123456789",
            "rocState": "Karnataka",
            "registeredAddress": {
                "pin": "560100",
                "city": "Belgaum",
                "line1": "Belagum",
                "line2": "Belgaum",
                "state": "Karnataka",
                "country": "India",
                "stdCode": "080",
                "district": "Belgaum"
            },
            "corporateAddress": null,
            "sameAsRegistered": true,
            "fiscalConfig": {
                "fyType": "apr-mar",
                "timezone": "IST UTC+5:30",
                "cutoffDay": "28",
                "weekStart": "Monday",
                "payrollFreq": "Monthly",
                "workingDays": [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday"
                ],
                "disbursementDay": "5"
            },
            "preferences": {
                "ess": false,
                "eSign": false,
                "webApp": true,
                "currency": "INR — ₹",
                "language": "English",
                "whatsapp": false,
                "aiChatbot": false,
                "biometric": false,
                "mobileApp": true,
                "systemApp": true,
                "dateFormat": "DD/MM/YYYY",
                "emailNotif": false,
                "timeFormat": "12-hour (AM/PM)",
                "numberFormat": "Indian (2,00,000)",
                "multiCurrency": false,
                "bankIntegration": true,
                "indiaCompliance": true
            },
            "endpointType": "default",
            "customEndpointUrl": null,
            "multiLocationMode": true,
            "locationConfig": "per-location",
            "selectedModuleIds": null,
            "customModulePricing": null,
            "userTier": null,
            "customUserLimit": null,
            "customTierPrice": null,
            "billingCycle": "monthly",
            "trialDays": 0,
            "dayStartTime": "00:00",
            "dayEndTime": "23:59",
            "weeklyOffs": [
                "Sunday"
            ],
            "systemControls": {
                "mfa": true,
                "cycleTime": true,
                "loadUnload": true,
                "ncEditMode": true,
                "payrollLock": true,
                "overtimeApproval": true,
                "leaveCarryForward": true
            },
            "wizardStatus": "Active",
            "tenant": {
                "id": "cmmwiuqk00003iq6t8wqk4p6o",
                "schemaName": "tenant_cmmwiuqjy0001iq6tan93n0y6",
                "status": "ACTIVE"
            },
            "_count": {
                "locations": 3,
                "contacts": 1,
                "users": 1
            }
        },
        {
            "id": "cmmwidaoq0000132wwieg8cjc",
            "name": "Acme Manufacturing Pvt Ltd",
            "industry": "Manufacturing",
            "size": "SMALL",
            "website": null,
            "gstNumber": null,
            "address": {
                "city": "Pune",
                "line1": "Industrial Area",
                "state": "Maharashtra",
                "country": "India",
                "pincode": "411001"
            },
            "contactPerson": {
                "name": "Company Admin",
                "email": "admin@acme.local",
                "phone": ""
            },
            "createdAt": "2026-03-18T20:43:12.602Z",
            "updatedAt": "2026-03-18T20:44:06.113Z",
            "displayName": null,
            "legalName": null,
            "shortName": null,
            "businessType": null,
            "companyCode": null,
            "cin": null,
            "incorporationDate": null,
            "employeeCount": null,
            "emailDomain": null,
            "logoUrl": null,
            "pan": null,
            "tan": null,
            "gstin": null,
            "pfRegNo": null,
            "esiCode": null,
            "ptReg": null,
            "lwfrNo": null,
            "rocState": null,
            "registeredAddress": null,
            "corporateAddress": null,
            "sameAsRegistered": true,
            "fiscalConfig": null,
            "preferences": null,
            "endpointType": "default",
            "customEndpointUrl": null,
            "multiLocationMode": false,
            "locationConfig": "common",
            "selectedModuleIds": null,
            "customModulePricing": null,
            "userTier": null,
            "customUserLimit": null,
            "customTierPrice": null,
            "billingCycle": "monthly",
            "trialDays": 0,
            "dayStartTime": null,
            "dayEndTime": null,
            "weeklyOffs": null,
            "systemControls": null,
            "wizardStatus": "Draft",
            "tenant": {
                "id": "cmmwidaov0002132wlj2hvt0a",
                "schemaName": "tenant_acme_manufacturing_pvt_ltd",
                "status": "ACTIVE"
            },
            "_count": {
                "locations": 0,
                "contacts": 0,
                "users": 1
            }
        }
    ],
    "message": "Companies retrieved successfully",
    "meta": {
        "page": 1,
        "limit": 25,
        "total": 3,
        "totalPages": 1
    }
}
```

## API - `http://localhost:3030/api/v1/auth/refresh-token`

```json
{
    "success": true,
    "data": {
        "tokens": {
            "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbW13aWRiMWcwMDA1MTMyd3JjMnhld3lsIiwiZW1haWwiOiJzdXBlcmFkbWluQGF2eWVycC5sb2NhbCIsInJvbGVJZCI6IlNVUEVSX0FETUlOIiwicGVybWlzc2lvbnMiOlsiKiJdLCJpYXQiOjE3NzM5MDIxNzksImV4cCI6MTc3MzkwMzA3OX0.LCAfrZ4xbgJuxT1F-lqUbeiF8bTMY4cperAatgcDBd8",
            "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbW13aWRiMWcwMDA1MTMyd3JjMnhld3lsIiwiZW1haWwiOiJzdXBlcmFkbWluQGF2eWVycC5sb2NhbCIsInJvbGVJZCI6IlNVUEVSX0FETUlOIiwicGVybWlzc2lvbnMiOlsiKiJdLCJpYXQiOjE3NzM5MDIxNzksImV4cCI6MTc3NDUwNjk3OX0.kmwUoUARDMVp2dolLiFsqVpVWZqx0UGHBevUkpIv5z8",
            "expiresIn": 900
        }
    },
    "message": "Token refreshed successfully"
}
```

## API - `http://localhost:3030/api/v1/platform/companies/cmmx3k1w3000111cgp5ln4aze`

- JSON Response:

```json
{
    "success": true,
    "data": {
        "id": "cmmx3k1w3000111cgp5ln4aze",
        "name": "Chetan Technologies",
        "industry": "IT",
        "size": "SMALL",
        "website": "https://avexora-tech.com",
        "gstNumber": "29AAVCS7832K1Z5",
        "address": null,
        "contactPerson": null,
        "createdAt": "2026-03-19T06:36:19.732Z",
        "updatedAt": "2026-03-19T06:36:19.732Z",
        "displayName": "Chetan Technologies",
        "legalName": "Chetan Technologies PVT LTD",
        "shortName": "CHET",
        "businessType": "Private Limited (Pvt. Ltd.)",
        "companyCode": "AUTO-CHETAN",
        "cin": "U72900KA2022PTC145678",
        "incorporationDate": "05/03/2026",
        "employeeCount": null,
        "emailDomain": "avexora-tech.com",
        "logoUrl": "blob:http://localhost:5173/bd3cad21-2500-4f07-b99b-68d62609fef4",
        "pan": "AAVCS7832K",
        "tan": "BLRA04567C",
        "gstin": "29AAVCS7832K1Z5",
        "pfRegNo": "KA/BLR/0456789/000/0001",
        "esiCode": "53-00-987654-000-0001",
        "ptReg": "KA-PT-2023-0456789",
        "lwfrNo": "KA-LWF-0456789",
        "rocState": "Karnataka",
        "registeredAddress": {
            "pin": "560103",
            "city": "Bengaluru",
            "line1": "Plot No. 45, 2nd Floor, Orion Tech Park, Outer Ring Road",
            "line2": "Near Ecospace Business Park, Bellandur",
            "state": "Karnataka",
            "country": "India",
            "stdCode": "080",
            "district": "Bengaluru Urban"
        },
        "corporateAddress": {
            "pin": "560041",
            "city": "Bengaluru",
            "line1": "No. 128, 1st Main Road, 5th Block, Jayanagar",
            "line2": "Opposite Jayanagar Metro Station",
            "state": "Karnataka",
            "country": "India",
            "stdCode": "080",
            "district": "Bengaluru Urban"
        },
        "sameAsRegistered": false,
        "fiscalConfig": {
            "fyType": "apr-mar",
            "timezone": "IST UTC+5:30",
            "cutoffDay": "28",
            "weekStart": "Monday",
            "payrollFreq": "Monthly",
            "workingDays": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday"
            ],
            "disbursementDay": "1"
        },
        "preferences": {
            "ess": false,
            "eSign": false,
            "webApp": true,
            "currency": "INR — ₹",
            "language": "English",
            "whatsapp": false,
            "aiChatbot": false,
            "biometric": false,
            "mobileApp": true,
            "systemApp": true,
            "dateFormat": "DD/MM/YYYY",
            "emailNotif": true,
            "timeFormat": "12-hour (AM/PM)",
            "numberFormat": "Indian (2,00,000)",
            "multiCurrency": false,
            "bankIntegration": true,
            "indiaCompliance": true
        },
        "razorpayConfig": null,
        "endpointType": "custom",
        "customEndpointUrl": "https://avyerp.com/chetan/api/v1",
        "multiLocationMode": true,
        "locationConfig": "per-location",
        "selectedModuleIds": null,
        "customModulePricing": null,
        "userTier": null,
        "customUserLimit": null,
        "customTierPrice": null,
        "billingCycle": "monthly",
        "trialDays": 0,
        "dayStartTime": "06:00",
        "dayEndTime": "17:59",
        "weeklyOffs": [
            "Sunday"
        ],
        "systemControls": {
            "mfa": true,
            "cycleTime": true,
            "loadUnload": true,
            "ncEditMode": true,
            "payrollLock": true,
            "overtimeApproval": true,
            "leaveCarryForward": true
        },
        "wizardStatus": "Active",
        "locations": [
            {
                "id": "cmmx3k1wb000411cg9kf5lbrm",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Bengaluru HQ",
                "code": "BLR-HQ-01",
                "facilityType": "Head Office",
                "customFacilityType": null,
                "status": "Active",
                "isHQ": true,
                "addressLine1": "Plot No. 45, 2nd Floor, Orion Tech Park, Outer Ring Road",
                "addressLine2": "Near Ecospace Business Park, Bellandur",
                "city": "Bengaluru",
                "district": "Bengaluru Urban",
                "state": "Karnataka",
                "pin": "560104",
                "country": "India",
                "stdCode": null,
                "gstin": "29AAVCS7832K1Z5",
                "stateGST": null,
                "contactName": "Rohit Sharma",
                "contactDesignation": "Plant Head",
                "contactEmail": "rohit@chetan.com",
                "contactCountryCode": "+91",
                "contactPhone": "9876543210",
                "geoEnabled": true,
                "geoLocationName": "Factory Main Gate",
                "geoLat": "12.9716",
                "geoLng": "77.594",
                "geoRadius": 100,
                "geoShape": "circle",
                "moduleIds": [
                    "hr",
                    "production",
                    "vendor",
                    "visitor"
                ],
                "customModulePricing": {},
                "userTier": "starter",
                "customUserLimit": null,
                "customTierPrice": null,
                "billingCycle": "monthly",
                "trialDays": 14,
                "createdAt": "2026-03-19T06:36:19.739Z",
                "updatedAt": "2026-03-19T06:36:19.739Z"
            },
            {
                "id": "cmmx3k1wb000511cg1j0vd0ke",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Mumbai Regional Office",
                "code": "BOM-RO-02",
                "facilityType": "Regional Office",
                "customFacilityType": null,
                "status": "Active",
                "isHQ": false,
                "addressLine1": "401, Sapphire IT Park, Powai",
                "addressLine2": "Saki Vihar Road",
                "city": "Mumbai",
                "district": "Mumbai Suburban",
                "state": "Maharashtra",
                "pin": "400076",
                "country": "India",
                "stdCode": null,
                "gstin": "27AAACZ1234F1Z6",
                "stateGST": null,
                "contactName": "Rajesh Kumar",
                "contactDesignation": "Regional Head",
                "contactEmail": "rajesh.kumar@chetan.com",
                "contactCountryCode": "+91",
                "contactPhone": "737383272",
                "geoEnabled": true,
                "geoLocationName": "Powai Office Building",
                "geoLat": "19.1176",
                "geoLng": "72.9060",
                "geoRadius": 200,
                "geoShape": "circle",
                "moduleIds": [
                    "hr",
                    "production",
                    "vendor",
                    "visitor"
                ],
                "customModulePricing": {},
                "userTier": "starter",
                "customUserLimit": null,
                "customTierPrice": null,
                "billingCycle": "monthly",
                "trialDays": 14,
                "createdAt": "2026-03-19T06:36:19.739Z",
                "updatedAt": "2026-03-19T06:36:19.739Z"
            }
        ],
        "contacts": [
            {
                "id": "cmmx3k1wc000611cgxknyy1uz",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Rohan Mehta",
                "designation": "Chief Financial Officer",
                "department": "Finance",
                "type": "Primary",
                "email": "rohan.mehta@dummycompany.in",
                "countryCode": "+91",
                "mobile": "9876500001",
                "linkedin": "https://www.google.com/search?q=https://linkedin.com/in/rohanmehta-dummy",
                "createdAt": "2026-03-19T06:36:19.741Z",
                "updatedAt": "2026-03-19T06:36:19.741Z"
            },
            {
                "id": "cmmx3k1wc000711cgsbtwd2fq",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Anita Desai",
                "designation": "Head of Legal",
                "department": "Legal",
                "type": "Legal Contact",
                "email": "anita.desai@dummycompany.in",
                "countryCode": "+91",
                "mobile": "9876543210",
                "linkedin": "https://www.google.com/search?q=https://linkedin.com/in/anitadesai-dummy",
                "createdAt": "2026-03-19T06:36:19.741Z",
                "updatedAt": "2026-03-19T06:36:19.741Z"
            }
        ],
        "shifts": [
            {
                "id": "cmmx3k1we000811cgs616mynt",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Morning Shift",
                "fromTime": "06:00",
                "toTime": "14:00",
                "noShuffle": false,
                "downtimeSlots": [
                    {
                        "type": "Tea Break",
                        "duration": "15"
                    },
                    {
                        "type": "Lunch Break",
                        "duration": "30"
                    }
                ],
                "createdAt": "2026-03-19T06:36:19.742Z",
                "updatedAt": "2026-03-19T06:36:19.742Z"
            },
            {
                "id": "cmmx3k1we000911cgy917buft",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Afternoon Shift",
                "fromTime": "14:00",
                "toTime": "22:00",
                "noShuffle": false,
                "downtimeSlots": [
                    {
                        "type": "Tea Break",
                        "duration": "15"
                    },
                    {
                        "type": "Other",
                        "duration": "30"
                    }
                ],
                "createdAt": "2026-03-19T06:36:19.742Z",
                "updatedAt": "2026-03-19T06:36:19.742Z"
            },
            {
                "id": "cmmx3k1we000a11cgllb5xc58",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "name": "Night Shift",
                "fromTime": "22:00",
                "toTime": "05:59",
                "noShuffle": false,
                "downtimeSlots": [
                    {
                        "type": "Other",
                        "duration": "30"
                    },
                    {
                        "type": "Other",
                        "duration": "15"
                    }
                ],
                "createdAt": "2026-03-19T06:36:19.742Z",
                "updatedAt": "2026-03-19T06:36:19.742Z"
            }
        ],
        "noSeries": [
            {
                "id": "cmmx3k1wf000c11cg1wzpf4o7",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "code": "GRN",
                "linkedScreen": "Goods Return",
                "description": "Goods Receipt Note",
                "prefix": "GRN",
                "suffix": "-FY-26-",
                "numberCount": 4,
                "startNumber": 1,
                "createdAt": "2026-03-19T06:36:19.743Z",
                "updatedAt": "2026-03-19T06:36:19.743Z"
            },
            {
                "id": "cmmx3k1wf000b11cgd6d17kyk",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "code": "WO",
                "linkedScreen": "Work Order",
                "description": "Work Order",
                "prefix": "WO-",
                "suffix": "Fy-2025-",
                "numberCount": 4,
                "startNumber": 1,
                "createdAt": "2026-03-19T06:36:19.743Z",
                "updatedAt": "2026-03-19T06:36:19.743Z"
            }
        ],
        "iotReasons": [
            {
                "id": "cmmx3k1wg000d11cgbu62l3id",
                "companyId": "cmmx3k1w3000111cgp5ln4aze",
                "reasonType": "Machine Idle",
                "reason": "Tool Breakage",
                "description": "Tool Breakage",
                "department": "Production",
                "planned": true,
                "duration": "7",
                "createdAt": "2026-03-19T06:36:19.744Z",
                "updatedAt": "2026-03-19T06:36:19.744Z"
            }
        ],
        "tenant": {
            "id": "cmmx3k1w8000311cgsed4551r",
            "schemaName": "tenant_cmmx3k1w3000111cgp5ln4aze",
            "companyId": "cmmx3k1w3000111cgp5ln4aze",
            "status": "ACTIVE",
            "createdAt": "2026-03-19T06:36:19.736Z",
            "updatedAt": "2026-03-19T06:36:19.736Z",
            "subscriptions": [
                {
                    "id": "cmmx3k1wh000f11cgnkuwopq6",
                    "tenantId": "cmmx3k1w8000311cgsed4551r",
                    "planId": "starter",
                    "userTier": "STARTER",
                    "billingCycle": "MONTHLY",
                    "modules": {},
                    "status": "ACTIVE",
                    "startDate": "2026-03-19T06:36:19.745Z",
                    "endDate": null,
                    "trialEndsAt": "2026-04-02T06:36:19.745Z",
                    "createdAt": "2026-03-19T06:36:19.745Z",
                    "updatedAt": "2026-03-19T06:36:19.745Z"
                }
            ]
        },
        "users": [
            {
                "id": "cmmx3k22n000h11cgz5si0paw",
                "email": "rahul.kulkarni@avyren.com",
                "firstName": "Rahul",
                "lastName": "Kulkarni",
                "phone": "986363722",
                "role": "COMPANY_ADMIN",
                "isActive": true,
                "lastLogin": null,
                "createdAt": "2026-03-19T06:36:19.968Z"
            }
        ]
    },
    "message": "Company retrieved successfully"
}
```