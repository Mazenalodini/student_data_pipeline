# Student Multi-Source Data Pipeline

## نظرة عامة

هذا المشروع عبارة عن **Data Engineering Pipeline احترافي** يجمع بيانات الطلاب من ثلاثة مصادر مستقلة:

1. CSV File
2. Online REST API عبر HTTPS
3. SQLite Database

ثم يطبق:

`Extract → Validate → Clean → Integrate → Transform → Final Validation → Load`

ويولد Dataset موحدًا صالحًا للتحليل وMachine Learning.

## المخرجات المطلوبة

```text
data/processed/final_dataset.csv
data/rejected/rejected_records.csv
logs/pipeline.log
```

ويضيف المشروع مخرجات احترافية أخرى:

```text
data/processed/student_ml_dataset.csv
reports/pipeline_metrics.json
reports/pipeline_run.md
state/source_manifest.json
```

## الفكرة الهندسية

البيانات موزعة بين أنظمة مختلفة. لكل مصدر Adapter مستقل، ثم تنتقل البيانات إلى طبقات مستقلة للتنظيف والدمج والتحويل والتحقق والإخراج.

```text
CSV ───────────┐
REST API ──────┼──→ Extraction
SQLite ────────┘
                    ↓
                Validation
                    ↓
                  Clean
                    ↓
                Integration
                    ↓
               Transformation
                    ↓
              Final Validation
                 /        \
                ↓          ↓
             Valid       Invalid
                ↓          ↓
       final_dataset   rejected_records
```

## مصادر البيانات

### CSV

المسار:

`data/raw/students.csv`

ويحتوي على:

```text
student_id
student_name
age
major
city
```

يتضمن الملف مشاكل متعمدة لاختبار Data Quality، مثل Missing Values وDuplicates وInvalid Age واختلاف حالة الأحرف والمسافات الإضافية.

### Online REST API

الـPipeline يتعامل مع HTTPS endpoint بالمخطط:

```json
{
  "student_id": 1001,
  "gpa": 3.45,
  "attendance": 92,
  "status": "Active"
}
```

وتم تجهيز `api_service/` ليتم نشره على Cloud مثل Render أو Railway.

**مهم:** المشروع جاهز للنشر، لكن إنشاء خدمة عامة على Cloud يحتاج حسابك وصلاحياتك؛ لذلك URL الإنتاج يوضع في `config.json` أو متغير البيئة بدل وضع URL وهمي في الكود.

### SQLite

قاعدة البيانات:

`database/students.db`

وتحتوي على:

```text
courses
enrollments
```

ويتم استخراج بيانات التسجيل باستخدام SQL JOIN.

## قواعد Data Quality

| الحقل | القاعدة |
|---|---|
| student_id | مطلوب وغير مكرر داخل المصدر |
| age | بين 16 و80 |
| gpa | بين 0 و4 |
| attendance | بين 0 و100 |
| score | بين 0 و100 |
| النصوص | Trim + توحيد الحالة |

### Missing Values

القيم المفقودة في الحقول الرقمية تتم معالجتها باستخدام **Median** حسب الإعداد في `config.json`.

### Invalid Values

القيم خارج النطاق لا يتم تعديلها بشكل صامت، بل يتم رفض السجل وتسجيل السبب في:

`data/rejected/rejected_records.csv`

وهذا يحافظ على Data Lineage ويجعل قرار الـPipeline قابلًا للمراجعة.

## Integration

يتم الربط باستخدام:

`student_id`

مثال:

```text
CSV
student_id + student_name + age + major + city

        +

API
student_id + gpa + attendance + status

        +

SQLite
student_id + course + score + semester
```

ثم تنتج Dataset موحدة.

## الأعمدة المشتقة

المشروع ينشئ أكثر من العمودين المطلوبين:

### performance_level

```text
GPA >= 3.5 → Excellent
GPA >= 3.0 → Very Good
GPA >= 2.5 → Good
GPA >= 2.0 → Acceptable
GPA < 2.0  → At Risk
```

### attendance_status

```text
Attendance >= 75 → Good
Attendance < 75  → Low
```

### score_band

```text
90–100 → A
80–89  → B
70–79  → C
60–69  → D
0–59   → F
```

### source

```text
CSV+API+DATABASE
```

وهي Data Lineage بسيطة توضّح أن السجل النهائي تم بناؤه من المصادر الثلاثة.

## Rejected Records

الملف يحتوي على معلومات إضافية تتجاوز الحد الأدنى المطلوب:

```text
source
record_type
student_id
error_reason
raw_record
detected_at
```

وبالتالي لا يتم حذف البيانات الخاطئة دون تفسير.

## Incremental Processing

المشروع يستخدم **Source Fingerprints** عبر SHA-256 لتتبع حالة المصادر.

في التشغيل الافتراضي `incremental`، إذا لم تتغير المصادر وكان الناتج موجودًا، يتم إعادة استخدام النتائج بدل تنفيذ Pipeline كامل من جديد.

أما عند الحاجة إلى إعادة بناء كاملة:

```powershell
python main.py --mode full
```

وهذا يعطي المشروع أساسًا مناسبًا لتطوير Incremental ETL أكبر مستقبلًا.

## Pipeline Metrics

يتم حساب:

```text
Total Records
Source Records
Integrated Records
Valid Records
Rejected Records
Duplicate Records
Missing Values Handled
Processing Time
Rejection Reasons
Source Hashes
```

وتحفظ في:

`reports/pipeline_metrics.json`

## Clean Code

التقسيم الأساسي:

```text
app/sources
app/transformation
app/validation
app/output
app/utils
```

ولا يوجد Pipeline ضخم أو Business Logic داخل `main.py`.

كل طبقة لها مسؤولية محددة ويمكن اختبارها بشكل مستقل.

## التثبيت

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts\setup_database.py
```

## إعداد الـOnline API

ضع رابط الخدمة المنشورة في:

`config.json`

أو:

```powershell
$env:STUDENT_PIPELINE_API_URL="https://YOUR-DEPLOYED-API.example.com/students"
```

## التشغيل

Full:

```powershell
python main.py --mode full
```

Incremental:

```powershell
python main.py
```

## الاختبارات

```powershell
pytest -q
```

وتغطي الاختبارات أهم نقاط التكليف: CSV، API، SQLite، التكرارات، القيم المفقودة، السجلات المرفوضة، الدمج، التحويل، والتحقق النهائي.

## كيف يطابق المشروع التكليف؟

| متطلب الدكتور | الملف المسؤول |
|---|---|
| CSV Extraction | `app/sources/csv_source.py` |
| REST API Extraction | `app/sources/api_source.py` |
| SQLite Extraction | `app/sources/database_source.py` |
| Validation | `app/validation/quality.py` |
| Cleaning | `app/sources/*` + `app/transformation/cleaner.py` |
| Integration | `app/transformation/integration.py` |
| Transformation | `app/transformation/transformer.py` |
| Rejected Records | `app/output/csv_writer.py` |
| Logging | `app/utils/logger.py` |
| Metrics | `app/utils/metrics.py` |
| Configuration | `config.json` |
| Incremental | `app/pipeline.py` |
| Tests | `tests/` |

## إجابات الأسئلة النهائية

### 1. لماذا نحتاج Data Pipeline عند تعدد المصادر؟
لأن البيانات في الأنظمة الحقيقية موزعة بين ملفات وواجهات API وقواعد بيانات. الـPipeline يفرض مسارًا منظمًا لاستخراج البيانات وفحصها وتنظيفها ودمجها وتحويلها.

### 2. الفرق بين Raw وProcessed
Raw تحافظ قدر الإمكان على البيانات كما جاءت من المصدر. Processed هي بيانات تم تنظيفها وتوحيدها والتحقق منها وتجهيزها للاستخدام downstream.

### 3. الفرق بين Extract وTransform وLoad
Extract استخراج البيانات من المصدر، Transform تعديل شكلها وجودتها وتمثيلها، Load حفظ الناتج في الوجهة النهائية.

### 4. ما المشاكل التي ظهرت أثناء الدمج؟
اختلاف شكل الأعمدة، Missing Values، Duplicates، Invalid Values، اختلاف النصوص، وسجلات موجودة في مصدر وغير موجودة في مصدر آخر.

### 5. كيف تعاملنا مع Missing Values؟
استخدمنا Median للحقول الرقمية مثل GPA وAttendance وAge حسب إعدادات المشروع، وتم توثيق الاستراتيجية في `config.json`.

### 6. كيف تعاملنا مع Duplicate Records؟
تم اكتشاف Exact Duplicates وDuplicate Business Keys ورفض السجلات المكررة مع تسجيل السبب.

### 7. كيف تعاملنا مع Invalid Records؟
يتم فصلها عن البيانات الصحيحة وحفظها في `rejected_records.csv` مع سبب الرفض.

### 8. لماذا فصل Extraction عن Transformation؟
حتى لا تصبح تفاصيل المصدر مرتبطة بقواعد الأعمال. يمكن إضافة مصدر جديد دون إعادة كتابة كامل Pipeline.

### 9. لماذا Validation أساسي؟
لأنه يمنع البيانات غير الصحيحة من الانتقال إلى التحليل أو Machine Learning دون اكتشافها.

### 10. كيف نجعل Pipeline يعمل دوريًا؟
يمكن تشغيله بواسطة Windows Task Scheduler أو cron أو CI/CD أو Orchestrator مثل Airflow.

### 11. كيف نتعامل مع ملايين السجلات؟
باستخدام Chunking وIncremental Extraction وFiltering/Aggregation داخل Database وتخزين قابل للتوسع وتقسيم البيانات وطرق معالجة متوازية عند الحاجة.

### 12. الفرق بين Batch وStreaming
Batch يعالج البيانات على دفعات، بينما Streaming يعالج تدفقات البيانات بشكل مستمر أو قريب من الزمن الحقيقي.
