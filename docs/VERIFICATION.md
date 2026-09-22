# Verification Record

هذه الوثيقة تسجل آخر عمليات التحقق الفعلية التي تمت على نسخة المشروع.

---

## 1. Automated Tests

تم تشغيل:

```powershell
python -m pytest -q
```

والنتيجة الأخيرة:

```text
9 passed
```

الاختبارات الحالية تغطي:

```text
CSV extraction and normalization
CSV duplicate/invalid handling
REST API extraction
REST API missing-value handling
SQLite extraction and validation
Source integration
Final validation
Derived features
Student-level ML aggregation
```

---

## 2. Full End-to-End Verification

تم تشغيل:

```powershell
python main.py --mode full
```

والـPipeline اكتمل بنجاح من Extraction حتى Load.

آخر نتيجة مسجلة:

```text
Processing mode         : full
CSV records             : 14
API records             : 14
Database records        : 21
Integrated records      : 18
Valid final records     : 18
Rejected records        : 11
Duplicate records       : 3
Missing values handled  : 3
Cross-source mismatches : 3
Cache hits              : 0
Cache misses            : 0
```

المخرجات التي تم إنشاؤها تشمل:

```text
data/processed/final_dataset.csv
data/processed/student_ml_dataset.csv
data/rejected/rejected_records.csv
reports/pipeline_metrics.json
reports/pipeline_run.md
logs/pipeline.log
data/raw/students_api_raw.json
data/raw/enrollments_raw.csv
```

---

## 3. Incremental Verification

تم تشغيل:

```powershell
python main.py
```

وبما أن `default_mode` في `config.json` مضبوط على `incremental`، تم تنفيذ Incremental Processing.

آخر نتيجة مسجلة:

```text
Processing mode         : incremental
CSV records             : 14
API records             : 14
Database records        : 21
Integrated records      : 18
Valid final records     : 18
Rejected records        : 11
Cache hits              : 3
Cache misses            : 0
```

كما سجل الـlog:

```text
No source changes detected; reusing previous pipeline outputs.
```

هذا يثبت أن الـcache وإعادة استخدام نتائج المصدر تعمل عند عدم تغير الـfingerprints.

---

## 4. Raw API JSON Verification

تم التحقق من:

```text
data/raw/students_api_raw.json
```

باستخدام JSON parser، وكانت النتيجة:

```text
Valid JSON          : YES
Records             : 14
Contains NaN        : False
Contains null       : True
```

وهذا مهم لأن JSON القياسي لا يستخدم `NaN` كقيمة JSON صالحة، لذلك يتم تحويل القيم المفقودة إلى `null` عند كتابة الـraw snapshot.

---

## 5. Rejected Records Verification

تم إنشاء:

```text
data/rejected/rejected_records.csv
```

وتظهر فيه أسباب مرفوضات حقيقية من مصادر متعددة، مثل:

```text
Duplicate record
Invalid Age
Invalid GPA
Invalid Score
Missing student_id
student_id not found in CSV source
Student missing from REST API source
```

ويتم الاحتفاظ بـsource وraw record ووقت الاكتشاف لتسهيل التتبع.

---

## 6. Online API Verification

Production API المستخدم من الـPipeline:

```text
https://student-academic-profile-api.vercel.app
```

النقاط الرئيسية:

```text
/health
/students
/students/{student_id}
/meta
/docs
```

تم التحقق سابقًا من أن `/health` يعيد حالة الخدمة، وأن `/students` يعيد بيانات الطلاب عبر HTTPS.

---

## 7. Final Verification Procedure

لإعادة التحقق على جهاز جديد:

```powershell
python -m pytest -q
python main.py --mode full
python main.py
```

ثم راجع:

```text
final_dataset.csv
rejected_records.csv
pipeline_metrics.json
pipeline_run.md
pipeline.log
students_api_raw.json
```
