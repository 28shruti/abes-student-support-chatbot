"""Real ABES Engineering College facts used by build_faq.py.
Sources (retrieved 31-Oct-2026):
  MD  = ABES Mandatory Disclosure, 18 March 2025   https://abes.abes.ac.in/pdf/Mandatory-Disclosure-March-2025.pdf
  GRC = ABES Grievance Redressal Cell page         https://abes.ac.in/GRC-grievance-redressal-cell.php
Only institutional contacts are used (no personal mobile numbers of staff or students).
NOTE: the college discloses fees only as 'as per norms' and links to its fee pages, so no fee amounts are stated here."""
SITE = "ABES website, courses-offered page (https://www.abes.ac.in/courses-offered.html), read 2026-10-31"
MD  = "ABES Mandatory Disclosure 18-Mar-2025 (https://abes.abes.ac.in/pdf/Mandatory-Disclosure-March-2025.pdf), retrieved 2026-10-31"
GRC = "ABES GRC page (https://abes.ac.in/GRC-grievance-redressal-cell.php) + Mandatory Disclosure 18-Mar-2025, retrieved 2026-10-31"

# replace the answer of an existing generic FAQ (matched by the start of its question)
OVERRIDE = {
 "How do I apply for admission?": (SITE,
  "At ABES, 85% of seats are filled through counselling (JEE Main based, via AKTU/UPTAC) and 15% through direct admission as per the college policy. Direct-admission candidates apply online through the ERP enquiry link on abes.ac.in/courses-offered.html. Admission enquiry: 8448494111."),
 "What are the eligibility criteria": (MD,
  "Eligibility follows UP Government / AKTU norms: B.Tech admission is through counselling on JEE Main rank and MCA through CUET rank. Programme-wise eligibility and cut-off ranks are published by the college; check the Admission Procedure page on abes.ac.in or write to info@abes.ac.in."),
 "What are the university office and working hours?": (MD,
  "Academic hours at ABES Engineering College are 8:30 AM to 4:30 PM. For office or counter timings of a particular department, call 0120-7135112 or e-mail info@abes.ac.in."),
 "Where can I find my class timetable?": (MD,
  "As per the college's disclosure, the academic timetable is available in your department. Your department office or class coordinator can share the latest version."),
 "When does the semester start and end?": (MD,
  "ABES is affiliated to Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow, and follows the AKTU academic calendar, which is published on aktu.ac.in. Departments announce any college-level changes."),
 "What is the fee structure for my programme?": (SITE,
  "ABES B.Tech fee 2026-27 is Rs. 1,81,200 per year in total (tuition Rs. 1,10,000 plus career planning, exam, technology and other heads, including a Rs. 5,000 refundable security deposit). Other programmes have their own fee tabs on abes.ac.in/courses-offered.html."),
 "What is the hostel fee?": (SITE,
  "ABES hostel fee 2026-27 ranges from about Rs. 1,36,500 (boys, 4-seater non-AC) to Rs. 1,77,500 (2-seater AC), including a Rs. 5,000 refundable security deposit. See abes.ac.in/courses-offered.html for the full table."),
 "What documents are required for admission?": (SITE,
  "At final admission bring two self-attested photocopies and the originals of: allotment letter (counselling candidates), entrance exam result, X and XII marksheets and certificates, transfer/migration certificate, character certificate, Aadhar cards, photographs and the other documents listed on abes.ac.in/courses-offered.html."),
 "What is the refund policy?": (SITE,
  "On cancellation of admission, fees are refunded as per UGC refund rules. On hostel withdrawal only the security, mess and laundry charges for unused months are refundable pro rata."),
 "How do I file a complaint or grievance?": (GRC,
  "ABES has a Grievance Redressal Cell (GRC), formed as per AICTE directions to handle complaints from students and staff. You can lodge a grievance through the GRC page on abes.ac.in (GRC-grievance-redressal-cell). The committee is chaired by the Director and includes the Registrar, Chief Proctor and a Member Secretary. A human support agent will also follow up."),
 "How can I report harassment or ragging?": (GRC,
  "ABES has an Anti-Ragging Committee (headed by the Director, with the Chief Proctor and Deputy Proctor), an Internal Complaints Committee (ICC) for harassment, and a Dean for Campus Life & Student Welfare (dcsw@abes.ac.in). The national anti-ragging helpline is 1800-180-5522. I am also alerting a human support agent now."),
 "What if my complaint is not resolved?": (GRC,
  "If a complaint is not resolved at department level, it can go to the central Grievance Redressal Cell, whose committee either upholds the earlier decision or changes it. The Institute committee also has a University (AKTU) nominee, and an Ombudsman exists at the university level. A human agent can help you escalate."),
 "Who is the grievance officer?": (GRC,
  "The Grievance Redressal Committee at ABES is chaired by the Director and includes the Registrar, the Chief Proctor, an AKTU official and a senior AKTU professor, with a Member Secretary. You can reach the offices at director@abes.ac.in or registrar@abes.ac.in."),
 "Can I access e-journals and digital resources from home?": (MD,
  "ABES provides e-library facilities, and its library subscribes to national and international journals. Ask the library staff how to get your remote-access login."),
}

# brand-new FAQs: (intent, question, alt_questions, answer, source)
NEW = [
 ("admissions","Which courses does ABES offer and how many seats are there?","programmes offered|list of courses|btech branches|seats in cse|intake of each branch|mca seats",
  "ABES (2026-27) offers B.Tech in CSE (900 seats), CSE-AI&ML (360), CSE-Data Science (180), ECE (180), Electrical & Computer Engineering (120), Mechanical (60) and Working-Professional CSE/ECE (30 each); MCA (180), BCA (120); M.Tech in CSE (12) and ECE (6). Seat numbers can change each year.", SITE),
 ("admissions","How can I contact ABES Engineering College?","college address|phone number of college|email id of college|where is abes located|college contact",
  "ABES Engineering College, 19th KM Stone, NH-09 (formerly NH-24), Ghaziabad - 201009, Uttar Pradesh. Phone: 0120-7135112. E-mail: info@abes.ac.in. Website: www.abes.ac.in. The nearest railway station is Ghaziabad (about 4 km).", MD),
 ("admissions","Is ABES approved and accredited?","is abes naac accredited|naac accreditation of abes|abes naac grade|naac grade|nba accreditation|aicte approval|affiliated to which university|aktu affiliation",
  "ABES is approved by AICTE, New Delhi, affiliated to Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow (college code 032), and NAAC accredited (Grade A). NBA accreditation was listed for CSE, ECE and ME up to 30 June 2025 - please check abes.ac.in for the current status.", MD),
 ("hostel","How many hostel seats are there at ABES?","hostel capacity|girls hostel available|boys hostel inside campus|hostel facility|hostel seats",
  "ABES has hostels inside the campus: 4 buildings for boys (1,033 seats) and 3 buildings for girls (458 seats). Apply through the hostel / admission office after confirming your admission.", MD),
 ("library","What does the ABES library offer?","total books in the library|library collection size|number of books available in library|journals available|e-library|library facilities",
  "The ABES library holds about 1,15,122 books (8,069 titles), subscribes to 179 national and 1,045 international journals, and provides e-library facilities.", MD),
 ("exams","Who conducts the semester exams and declares results?","aktu exam|aktu result|exams conducted by university|who gives degree|affiliating university exams|who declares results|who gives exam results",
  "ABES is affiliated to AKTU, so semester examinations, results and degrees follow AKTU rules and are published on aktu.ac.in. The college has a Dean (Examinations) office and a central examination facility, as per university norms.", MD),
 ("schedule","What computing and internet facilities are available on campus?","wifi in college|internet speed|computer lab|number of computers|internet bandwidth",
  "The campus has 1 Gbps internet bandwidth, about 1,440 PCs, one computer centre and 89 laboratories (as per the March 2025 disclosure).", MD),
 ("grievance","Which committees handle student complaints at ABES?","internal complaints committee|anti ragging committee|student welfare dean|sc st committee|equal opportunity cell",
  "ABES has a Grievance Redressal Committee, an Anti-Ragging Committee, an Internal Complaints Committee (ICC) for harassment, a SC/ST committee, an Equal Opportunity Cell and a Dean for Campus Life & Student Welfare (dcsw@abes.ac.in). A human agent can direct you to the right one.", GRC),
]
