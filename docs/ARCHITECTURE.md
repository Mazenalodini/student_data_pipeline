# Architecture — Student Multi-Source Data Pipeline

## 1. الهدف المعماري

المشروع مبني كـ **Reusable Data Pipeline** لمعالجة بيانات الطلاب القادمة من ثلاثة مصادر مختلفة:

```text
CSV + REST API + SQLite
          ↓
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

الهدف من هذا الفصل بين المراحل هو إبقاء مسؤوليات كل طبقة واضحة، وجعل إضافة مصدر جديد أو تغيير قاعدة معالجة أقل تأثيرًا على بقية النظام.

---

## 2. الطبقات الرئيسية

### Source Adapters — `app/sources/`

كل مصدر له Adapter مستقل:

```text
app/sources/
├── csv_source.py
├── api_source.py
└── database_source.py
```

مسؤولية هذه الطبقة هي القراءة من المصدر، توحيد البنية الأولية، تنفيذ قواعد الجودة الخاصة بالمصدر، وتحويل السجلات غير الصالحة إلى `RejectedRecord`.

### Transformation — `app/transformation/`

```text
app/transformation/
├── cleaner.py
├── integration.py
└── transformer.py
```

- `cleaner.py`: تنظيف النصوص ومعالجة Missing Values بالاستراتيجية المحددة في `config.json`.
- `integration.py`: دمج بيانات الطلاب الأكاديمية والتسجيلات باستخدام `student_id`.
- `transformer.py`: إنشاء Derived Features وبناء Dataset موجهة للتحليل وMachine Learning.

### Validation — `app/validation/`

`quality.py` مسؤول عن **Final Validation** بعد اكتمال الدمج والتحويل، ويتحقق من الأعمدة المطلوبة والقيم الرقمية والنصوص وعدم فراغ Dataset.

### Output — `app/output/`

مسؤول عن كتابة:

```text
data/processed/final_dataset.csv
data/processed/student_ml_dataset.csv
data/rejected/rejected_records.csv
```

بالإضافة إلى JSON reports الخاصة بالتشغيل والمصادر.

### Utilities — `app/utils/`

تحتوي على الخدمات المشتركة:

```text
hashing.py  → SHA-256 fingerprints
logger.py   → logging
metrics.py  → pipeline metrics
```

### Orchestration — `app/pipeline.py`

هذه الطبقة تنسق كامل الـPipeline وتحدد ترتيب المراحل، وتدير Full/Incremental Processing، والـcache، وكتابة التقارير.

### Entry Point — `main.py`

`main.py` هو CLI Entry Point بسيط ويستدعي Pipeline orchestration بدل وضع منطق المعالجة داخله.

---

## 3. تدفق البيانات

### Source 1 — CSV

المسار:

```text
data/raw/students.csv
```

يحتوي على بيانات الطالب الأساسية مثل `student_id`, `student_name`, `age`, `major`, `city`.

### Source 2 — REST API

الـPipeline يقرأ عنوان الـAPI من `config.json` أو من متغير البيئة:

```text
STUDENT_PIPELINE_API_URL
```

والـProduction endpoint الحالي هو:

```text
https://student-academic-profile-api.vercel.app/students
```

الـAPI يوفر بيانات أكاديمية مثل `gpa`, `attendance`, و`status`.

### Source 3 — SQLite

المسار:

```text
database/students.db
```

ويحتوي على جداول `courses` و`enrollments`. يتم استخراج معلومات التسجيل والمقرر بواسطة SQL `INNER JOIN`.

---

## 4. Validation وCleaning

يتم التحقق على مستويين:

```text
Source Validation
       ↓
Cleaning / Preparation
       ↓
Integration
       ↓
Final Validation
```

أهم القواعد:

| المجال | القاعدة |
|---|---|
| `student_id` | مطلوب ولا يقبل NULL في المصدر الأساسي |
| `age` | من 16 إلى 80 |
| `gpa` | من 0 إلى 4 |
| `attendance` | من 0 إلى 100 |
| `score` | من 0 إلى 100 |
| النصوص | إزالة المسافات الزائدة وتوحيد بعض القيم النصية |
| Duplicates | اكتشافها ورفض السجل الزائد مع سبب واضح |

القيم المفقودة في الحقول الرقمية المحددة تستخدم **Median Imputation** وفق الإعدادات.

القيم غير الصالحة ضمن النطاقات لا يتم تصحيحها بشكل صامت؛ بل تذهب إلى `rejected_records.csv` مع سبب الرفض.

---

## 5. Integration Strategy

المفتاح المشترك بين المصادر هو:

```text
student_id
```

منطق الدمج هو:

```text
CSV student profile
        +
REST academic profile
        +
SQLite enrollment facts
        ↓
Integrated Dataset
```

يتم أولًا استبعاد سجلات API/SQLite التي لا يوجد `student_id` الخاص بها في CSV، وتسجيلها ضمن Rejected Records. بعد ذلك يتم الدمج على الطلاب المتوافقين.

---

## 6. Grain of the Outputs

### `final_dataset.csv`

الغرض منه الاحتفاظ بالتفاصيل على مستوى التسجيل، ولذلك يكون الـgrain:

```text
One Row per Student × Course × Semester
```

بالتالي من الطبيعي أن يظهر `student_id` أكثر من مرة للطالب المسجل في عدة مقررات.

### `student_ml_dataset.csv`

يتم تجميع بيانات التسجيل إلى:

```text
One Row per Student
```

ويشمل Features مثل:

```text
course_count
total_credit_hours
average_score
highest_score
lowest_score
```

---

## 7. Transformation

تُنشأ في `transformer.py` الميزات التالية:

```text
performance_level
attendance_status
score_band
source
```

`source` يمثل **Data Lineage** الأساسي للصف النهائي، والقيمة الحالية للسجلات المتكاملة هي:

```text
CSV+API+DATABASE
```

---

## 8. Rejected Records وTraceability

السجلات غير الصالحة تحفظ في:

```text
data/rejected/rejected_records.csv
```

ويتم حفظ معلومات تشمل:

```text
source
record_type
student_id
error_reason
raw_record
detected_at
```

هذا يمنع فقدان سبب الرفض ويجعل البيانات قابلة للمراجعة والتتبع.

---

## 9. Incremental Processing

المشروع يدعم وضعين:

```text
Full Processing
Incremental Processing
```

### Full

يعيد تنفيذ المراحل من المصادر:

```powershell
python main.py --mode full
```

### Incremental

الوضع الافتراضي في `config.json` هو:

```json
"default_mode": "incremental"
```

ويستخدم SHA-256 fingerprints للملفات المحلية وfingerprint للـAPI endpoint والـAPI payload، مع validated caches داخل `state/`.

عند عدم وجود تغييرات في المصادر ووجود المخرجات السابقة، يمكن إعادة استخدام النتائج السابقة بدل إعادة بناء كل شيء.

**ملاحظة:** لأن الـAPI مصدر remote، يحتاج الـPipeline حاليًا إلى الاتصال به للحصول على الـpayload وتحديد ما إذا كان محتواه قد تغير.

---

## 10. Configuration

الإعدادات المهمة خارج Business Logic في:

```text
config.json
```

وتشمل:

```text
API URL
Timeout
Retries
Backoff
SQLite path
Output paths
Missing-value strategies
Default processing mode
Attendance threshold
```

ويمكن تجاوز عنوان الـAPI من البيئة:

```powershell
$env:STUDENT_PIPELINE_API_URL="https://example.com/students"
```

---

## 11. Observability

ينتج المشروع ثلاثة أنواع رئيسية من الـobservability:

### Logging

```text
logs/pipeline.log
```

### Metrics

```text
reports/pipeline_metrics.json
```

وتتضمن source counts، rejected counts، duplicates، missing values، processing time، source hashes، وcache hits/misses.

### Run Report

```text
reports/pipeline_run.md
```

ويلخص نتيجة التشغيل ومخرجاته.

---

## 12. Extensibility

يمكن إضافة Source Adapter جديد تحت:

```text
app/sources/
```

مع الحفاظ على طبقات التنظيف والدمج والتحويل والمخرجات الحالية.

أمثلة مستقبلية ممكنة:

```text
Excel
JSON File
PostgreSQL
MySQL
MongoDB
```

وهذا هو السبب في فصل Source Extraction عن Transformation وOutput.
