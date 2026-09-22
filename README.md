# Student Multi-Source Data Pipeline

## نظرة عامة

هذا المشروع عبارة عن **Data Engineering Pipeline** مبني بلغة Python لمعالجة بيانات الطلاب القادمة من ثلاثة مصادر مختلفة:

- **CSV File**: بيانات الهوية والبيانات الأساسية للطلاب.
- **Online REST API**: البيانات الأكاديمية مثل GPA والحضور والحالة.
- **SQLite Database**: بيانات المقررات والتسجيلات والدرجات.

يمر كل مصدر عبر خط معالجة موحد:

```text
Extract
  ↓
Validate
  ↓
Clean
  ↓
Integrate
  ↓
Transform
  ↓
Final Validation
  ↓
Load
```

النتيجة الأساسية هي Dataset موحدة جاهزة للتحليل وMachine Learning، مع فصل السجلات غير الصالحة في ملف مستقل مع سبب الرفض.

---

## أهداف المشروع

يطبق المشروع عمليًا مفاهيم Data Engineering المطلوبة في التكليف، مع التركيز على:

- التعامل مع **Multi-Source Data**.
- فصل مسؤوليات مصادر البيانات عن منطق المعالجة.
- تطبيق **Data Validation** قبل وبعد الدمج.
- معالجة Missing Values وDuplicates وInvalid Values.
- دمج المصادر باستخدام `student_id` كمفتاح أعمال مشترك.
- إنشاء Features مشتقة قابلة للاستخدام في التحليل وML.
- الاحتفاظ بالسجلات المرفوضة مع سبب الرفض.
- توفير Logging وMetrics وData Lineage.
- دعم **Full Processing** و**Incremental Processing**.

---

## Architecture

```text
                         DATA SOURCES
            ┌────────────────┼────────────────┐
            │                │                │
           CSV          REST API           SQLite
            │                │                │
            └────────────────┼────────────────┘
                             ↓
                         Extraction
                             ↓
                    Source Validation
                             ↓
                           Cleaning
                             ↓
                         Integration
                             ↓
                        Transformation
                             ↓
                      Final Validation
                        /           \
                       /             \
              Valid Records      Rejected Records
                    │                  │
                    ↓                  ↓
          final_dataset.csv   rejected_records.csv
                    │
                    ↓
              ML / BI / Analysis
```

### مسؤوليات الطبقات

| الطبقة | المسؤولية |
|---|---|
| `app/sources/` | استخراج كل مصدر ومعالجة قواعده الخاصة والتحقق الأولي |
| `app/transformation/cleaner.py` | تنظيف النصوص ومعالجة Missing Values |
| `app/transformation/integration.py` | دمج CSV + REST API + SQLite |
| `app/transformation/transformer.py` | Features مشتقة وDataset موجهة لـML |
| `app/validation/quality.py` | التحقق النهائي من جودة Dataset |
| `app/output/` | كتابة Final Dataset وRejected Records والـJSON outputs |
| `app/utils/` | Logging وMetrics وHashing |
| `app/pipeline.py` | Orchestration وتنفيذ دورة الـPipeline |
| `main.py` | CLI Entry Point فقط |

---

## Project Structure

```text
student_data_pipeline/
├── app/
│   ├── sources/
│   │   ├── csv_source.py
│   │   ├── api_source.py
│   │   └── database_source.py
│   ├── transformation/
│   │   ├── cleaner.py
│   │   ├── integration.py
│   │   └── transformer.py
│   ├── validation/
│   │   └── quality.py
│   ├── output/
│   │   └── csv_writer.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── metrics.py
│   │   └── hashing.py
│   ├── config.py
│   ├── models.py
│   └── pipeline.py
├── api_service/
│   ├── main.py
│   ├── data/students_api.json
│   ├── Dockerfile
│   ├── render.yaml
│   └── requirements.txt
├── data/
│   ├── raw/
│   ├── processed/
│   └── rejected/
├── database/
│   ├── schema.sql
│   └── students.db
├── docs/
├── logs/
├── reports/
├── state/
├── scripts/
│   └── setup_database.py
├── tests/
├── config.json
├── main.py
└── requirements.txt
```

---

## Data Sources

### 1. CSV Source

الملف:

```text
data/raw/students.csv
```

الحقول الأساسية:

```text
student_id
student_name
age
major
city
```

يستخدم هذا المصدر لاختبار قواعد Data Quality، بما في ذلك Missing Values وDuplicates وInvalid Values وتباين النصوص.

### 2. Online REST API

المصدر المنشور حاليًا:

```text
https://student-academic-profile-api.vercel.app/students
```

الـAPI يوفر بيانات أكاديمية بهذا الشكل:

```json
{
  "student_id": 1001,
  "gpa": 3.7,
  "attendance": 94,
  "status": "Active"
}
```

نقطة الصحة:

```text
/health
```

وواجهة التوثيق:

```text
/docs
```

نقطة جلب الطلاب هي:

```text
/students
```

يقرأ الـPipeline عنوان الـAPI من `config.json`، مع إمكانية تجاوزه بواسطة متغير البيئة `STUDENT_PIPELINE_API_URL`.

### 3. SQLite Source

قاعدة البيانات:

```text
database/students.db
```

الجداول الرئيسية:

```text
courses
enrollments
```

ويتم استخراج معلومات التسجيل والمقرر باستخدام SQL `JOIN`.

---

## Data Quality Rules

| الحقل | قاعدة التحقق |
|---|---|
| `student_id` | Required وUnique داخل المصدر |
| `age` | من 16 إلى 80 |
| `gpa` | من 0 إلى 4 |
| `attendance` | من 0 إلى 100 |
| `score` | من 0 إلى 100 |
| Text fields | Trim + Normalization |

### Missing Values

تتم معالجة القيم الرقمية المفقودة وفق الاستراتيجية الموجودة في `config.json`، وحاليًا تعتمد على **Median** للحقول الرقمية المحددة.

### Invalid Values

القيم التي تخالف حدود الجودة لا يتم تصحيحها بشكل صامت. يتم رفض السجل وتسجيل السبب في:

```text
data/rejected/rejected_records.csv
```

### Duplicate Records

يتم اكتشاف التكرارات على مستوى المصدر، ويتم رفض التكرار مع الإبقاء على السجل المقبول الأساسي.

---

## Integration

المفتاح المشترك بين المصادر هو:

```text
student_id
```

مصدر CSV يوفر بيانات الطالب الأساسية، وREST API يوفر الملف الأكاديمي، وSQLite يوفر حقائق التسجيل بالمقرر.

الـFinal Dataset يحتفظ بمستوى تفصيل **Student × Course × Semester**؛ لذلك قد يظهر `student_id` أكثر من مرة عندما يكون الطالب مسجلًا في أكثر من مقرر أو فصل.

تم أيضًا إنشاء Dataset ثانية بمستوى **One Row Per Student** لأغراض ML والتحليل.

---

## Transformations

ينتج المشروع Features مشتقة، من أهمها:

### `performance_level`

```text
GPA >= 3.5 → Excellent
GPA >= 3.0 → Very Good
GPA >= 2.5 → Good
GPA >= 2.0 → Acceptable
GPA < 2.0  → At Risk
```

### `attendance_status`

```text
Attendance >= 75 → Good
Attendance < 75  → Low
```

### `score_band`

```text
90–100 → A
80–89  → B
70–79  → C
60–69  → D
0–59   → F
```

### `source`

```text
CSV+API+DATABASE
```

يستخدم هذا الحقل كجزء من **Data Lineage** لتوضيح مصادر البيانات التي ساهمت في بناء السجل النهائي.

---

## Rejected Records

الملف:

```text
data/rejected/rejected_records.csv
```

ويحتوي على معلومات مثل:

```text
source
record_type
student_id
error_reason
raw_record
detected_at
```

وبالتالي لا يتم إسقاط السجل غير الصالح دون تفسير؛ بل يبقى قابلًا للمراجعة والتتبع.

---

## Raw Data and Traceability

يحافظ المشروع على Raw snapshots للمصادر المهمة:

```text
data/raw/students.csv
data/raw/students_api_raw.json
data/raw/enrollments_raw.csv
```

ويتم استخدام SHA-256 fingerprints لتتبع حالة المصادر ودعم Incremental Processing.

---

## Incremental Processing

يدعم المشروع نمطين للتشغيل:

### Full Processing

يعيد بناء النتائج من المصادر من البداية:

```powershell
python main.py --mode full
```

### Incremental Processing

يستخدم fingerprints وvalidated caches لإعادة استخدام نتائج المصادر التي لم تتغير.

التشغيل الافتراضي:

```powershell
python main.py
```

قبل إعادة الاستخدام، يتم فحص الـREST API لأن الـpayload قد يتغير حتى لو لم يتغير عنوان الـendpoint.

---

## Configuration

جميع الإعدادات المهمة موجودة خارج منطق الـPipeline في:

```text
config.json
```

ويتضمن ذلك:

- API URL
- timeout
- retries
- backoff
- database path
- output paths
- missing-value strategies
- default processing mode
- attendance threshold

يمكن تجاوز عنوان الـAPI من البيئة:

```powershell
$env:STUDENT_PIPELINE_API_URL="https://example.com/students"
```

ويُفضّل استخدام environment variable عندما يكون عنوان الخدمة مختلفًا بين البيئات.

---

## Pipeline Metrics

يولد المشروع تقرير Metrics في:

```text
reports/pipeline_metrics.json
```

ويشمل:

- source record counts
- integrated records
- valid final records
- rejected records
- duplicate records
- missing values handled
- rejection reasons
- source fingerprints
- cache hits / misses
- processing time

كما يتم إنشاء تقرير تشغيلي في:

```text
reports/pipeline_run.md
```

---

## Logging

يتم تسجيل التنفيذ في:

```text
logs/pipeline.log
```

ويتضمن مراحل التشغيل والأخطاء وحالة المصادر ونتيجة الـPipeline.

---

## Installation

المشروع يستخدم Python ولا يحتاج إلى مكتبات خارجية لتشغيل خدمة الـAPI المحلية أو الـPipeline باستثناء الحزم الموجودة في `requirements.txt`.

إنشاء البيئة:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

تثبيت الاعتماديات:

```powershell
python -m pip install -r requirements.txt
```

إنشاء/إعادة بناء قاعدة SQLite:

```powershell
python scripts\setup_database.py
```

---

## Running the Pipeline

Full run:

```powershell
python main.py --mode full
```

Incremental run:

```powershell
python main.py
```

---

## Tests

تشغيل الاختبارات:

```powershell
python -m pytest -q
```

الاختبارات الحالية تغطي:

1. CSV extraction
2. REST API extraction
3. SQLite extraction
4. Duplicate handling
5. Missing values
6. Invalid records
7. Source integration
8. Transformation / derived features
9. Final validation

آخر تحقق أثناء إعداد النسخة:

```text
9 passed
```

---

## Outputs

### Required outputs

```text
data/processed/final_dataset.csv
data/rejected/rejected_records.csv
logs/pipeline.log
```

### Additional engineering outputs

```text
data/processed/student_ml_dataset.csv
reports/pipeline_metrics.json
reports/pipeline_run.md
state/source_manifest.json
```

### Grain of each dataset

`final_dataset.csv`:

```text
One row per Student × Course × Semester
```

`student_ml_dataset.csv`:

```text
One row per Student
```

---

## API Service

الخدمة موجودة في:

```text
api_service/
```

وتستخدم FastAPI.

Endpoints الرئيسية:

```text
/
/health
/students
/students/{student_id}
/meta
/docs
```

الخدمة منشورة حاليًا على Vercel، والـPipeline يستخدم endpoint الإنتاج الموجود في `config.json`.

---

## Assignment Mapping

| Requirement | Implementation |
|---|---|
| CSV Extraction | `app/sources/csv_source.py` |
| REST API Extraction | `app/sources/api_source.py` |
| SQLite Extraction | `app/sources/database_source.py` |
| Validation | Source validators + `app/validation/quality.py` |
| Cleaning | `app/transformation/cleaner.py` + source preparation |
| Missing Values | Configured Median strategy |
| Duplicates | Source-level duplicate detection |
| Column Normalization | Source adapters |
| Type Conversion | Source adapters |
| Derived Columns | `app/transformation/transformer.py` |
| Integration | `app/transformation/integration.py` |
| Rejected Records | `data/rejected/rejected_records.csv` |
| Final Load | `app/output/csv_writer.py` |
| Logging | `app/utils/logger.py` |
| Configuration | `config.json` |
| Incremental Processing | SHA-256 fingerprints + caches |
| Data Lineage | `source` + run metadata |
| Metrics | `app/utils/metrics.py` |
| Reusable Architecture | Source adapter modules |
| Tests | `tests/` |

---

## Final Assignment Questions

### 1. لماذا نحتاج إلى Data Pipeline متعددة المصادر؟

لأن البيانات في الأنظمة الواقعية تكون موزعة بين ملفات وقواعد بيانات وواجهات APIs. الـPipeline يوفر مسارًا منظمًا لاستخراج البيانات والتحقق منها وتنظيفها ودمجها وتحويلها قبل استخدامها.

### 2. ما الفرق بين Raw Data وProcessed Data؟

Raw Data تمثل البيانات القادمة من المصدر قبل المعالجة. أما Processed Data فقد مرت بالتنظيف والتوحيد والتحقق والتحويل وأصبحت مناسبة للاستخدام downstream.

### 3. ما المقصود بـ ETL؟

Extract تعني استخراج البيانات، Transform تعني تغيير شكلها أو جودتها أو تمثيلها، وLoad تعني كتابة النتيجة في وجهة الاستخدام.

### 4. ما مشكلات Integration الشائعة؟

اختلاف هياكل البيانات، Missing Values، Duplicates، اختلاف النصوص، Invalid Values، ووجود IDs في مصدر وعدم وجودها في مصدر آخر.

### 5. لماذا نستخدم Median في Missing Values؟

لأن Median استراتيجية بسيطة وحتمية وأقل تأثرًا بالقيم المتطرفة من Mean في كثير من الحالات. في هذا المشروع هي الاستراتيجية المحددة في `config.json` للحقول الرقمية المعنية.

### 6. كيف نتعامل مع Duplicates؟

يتم اكتشاف التكرارات وفق قواعد المصدر، ويرفض السجل المكرر مع تسجيل السبب بدل السماح له بالدخول إلى النتيجة النهائية دون تفسير.

### 7. ماذا نفعل مع Invalid Records؟

يتم رفضها وتسجيل المصدر والسجل وسبب الرفض في `rejected_records.csv`، بدل تعديلها بشكل صامت.

### 8. لماذا نفصل Extraction عن Transformation؟

حتى تبقى مشاكل الاتصال والقراءة والتنسيق الخاصة بالمصدر منفصلة عن Business Rules. هذا يجعل إضافة Source جديد أسهل ويقلل الترابط بين المكونات.

### 9. لماذا Final Validation مهمة؟

للتأكد من أن Dataset الناتجة بعد الدمج والتنظيف والتحويل ما زالت تحقق قواعد الجودة المطلوبة قبل تحميلها للاستخدام النهائي.

### 10. كيف يمكن تشغيل الـPipeline تلقائيًا؟

يمكن تشغيله باستخدام Windows Task Scheduler أو cron أو CI/CD أو أدوات orchestration مثل Airflow بحسب بيئة التشغيل.

### 11. كيف يمكن توسيعه لملايين السجلات؟

من خلال Chunked Processing، Incremental Extraction، تنفيذ filtering وaggregation داخل قاعدة البيانات، التخزين المقسم، وتحسين الموارد بدل تحميل كل البيانات في الذاكرة دفعة واحدة.

### 12. ما الفرق بين Batch Processing وStreaming؟

Batch يعالج البيانات على دفعات في أوقات محددة أو عند trigger. Streaming يعالج الأحداث بشكل مستمر أو شبه لحظي عند وصولها.

---

## Verification Snapshot

تم التحقق من النسخة الحالية باستخدام:

```powershell
python -m pytest -q
python main.py --mode full
python main.py
```

وكانت إحدى عمليات الـFull الأخيرة:

```text
CSV records             : 14
API records             : 14
Database records        : 21
Integrated records      : 18
Valid final records     : 18
Rejected records        : 11
Duplicate records       : 3
Missing values handled  : 3
Cross-source mismatches : 3
Processing mode         : full
```

كما تم التحقق من Raw API snapshot وأنه:

```text
Valid JSON     : YES
Records        : 14
Contains NaN   : False
Contains null  : True
```

---

## Clean Code Principles

المشروع مبني حول مبادئ:

- Separation of Concerns
- Single Responsibility
- Reusable Source Adapters
- Typed Interfaces
- Small Testable Functions
- Configuration outside Business Logic
- Structured Logging
- Rejected-Record Traceability
- Deterministic Outputs
- Source Fingerprinting

---

## مشروع قابل للتطوير

الهيكل الحالي يسمح لاحقًا بإضافة مصادر أو destinations جديدة دون إعادة كتابة الـPipeline بالكامل، مثل:

```text
New Source Adapter
       ↓
Existing Validation / Cleaning
       ↓
Existing Integration
       ↓
Existing Transformation
       ↓
Existing Output Layer
```

وهذا يحافظ على فصل المسؤوليات ويجعل المشروع مناسبًا للتوسع التدريجي.
