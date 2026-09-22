# Demo Checklist — Student Multi-Source Data Pipeline

هذا الملف مخصص للعرض أمام الدكتور خطوة بخطوة بدون التنقل العشوائي بين أجزاء المشروع.

---

## 1. ابدأ بفكرة المشروع

افتح `README.md` وابدأ بشرح الفكرة:

```text
CSV + REST API + SQLite
        ↓
Extract → Validate → Clean → Integrate → Transform
        ↓
Final Validation → Load
```

الجملة الأساسية في العرض:

> المشروع يجمع بيانات من ثلاثة مصادر مختلفة، يتحقق من جودتها، ينظفها، يدمجها باستخدام `student_id`، ثم ينتج Dataset نهائية قابلة للتحليل وMachine Learning مع الاحتفاظ بالسجلات المرفوضة وأسبابها.

---

## 2. اعرض مصادر البيانات الثلاثة

### CSV

افتح:

```text
data/raw/students.csv
```

ووضح أنه يحتوي على البيانات الأساسية للطلاب.

### REST API

افتح المتصفح على:

```text
https://student-academic-profile-api.vercel.app/docs
```

ثم اعرض:

```text
GET /health
GET /students
GET /students/{student_id}
```

### SQLite

افتح:

```text
database/students.db
```

واشرح جدولَي:

```text
courses
enrollments
```

---

## 3. اعرض الهيكل

في VS Code افتح:

```text
app/
data/
database/
tests/
docs/
api_service/
main.py
config.json
```

اشرح أن `app/sources/` يعزل كل مصدر عن الآخر، وأن `app/pipeline.py` مسؤول عن orchestration.

---

## 4. اعرض SQL

افتح:

```text
docs/DATA_AND_SQL.md
```

ثم:

```text
database/schema.sql
app/sources/database_source.py
```

وضح أن SQLite لا تتم قراءته مباشرة كملف، بل يتم تنفيذ SQL `INNER JOIN` لاستخراج بيانات التسجيل مع معلومات المقرر.

---

## 5. شغّل Full Processing

نفّذ في Terminal:

```powershell
python main.py --mode full
```

ثم وضح المراحل الظاهرة في الـlog:

```text
REST API extraction
CSV extraction
SQLite extraction
Data integration
Transformation
Final validation
Final dataset creation
Rejected records writing
Pipeline completed successfully
```

---

## 6. اعرض Data Quality

افتح:

```text
data/rejected/rejected_records.csv
```

أظهر أمثلة مثل:

```text
Invalid Age
Invalid GPA
Invalid Score
Missing student_id
Duplicate record
student_id not found in CSV source
Student missing from REST API source
```

ثم اشرح أن السجل غير الصالح لا يختفي بصمت؛ بل يسجل مصدره وسبب رفضه وتمثيله الخام.

---

## 7. اعرض Final Dataset

افتح:

```text
data/processed/final_dataset.csv
```

وضح أن الـgrain هو:

```text
One Row per Student × Course × Semester
```

وأظهر الـfeatures المشتقة:

```text
performance_level
attendance_status
score_band
source
```

---

## 8. اعرض ML Dataset

افتح:

```text
data/processed/student_ml_dataset.csv
```

وضح أنه:

```text
One Row per Student
```

ويحتوي على Features تجميعية مثل:

```text
course_count
total_credit_hours
average_score
highest_score
lowest_score
```

---

## 9. اعرض Logging وMetrics

افتح:

```text
logs/pipeline.log
reports/pipeline_metrics.json
reports/pipeline_run.md
```

وضح أن المشروع لا يكتفي بإنتاج Dataset، بل يسجل execution history وsource counts وrejections وprocessing time وhashes وcache information.

---

## 10. أثبت Incremental Processing

بدون تعديل المصادر، نفذ مرة أخرى:

```powershell
python main.py
```

ثم وضح:

```text
default_mode = incremental
```

وأن النظام يستخدم source fingerprints وvalidated caches لإعادة استخدام النتائج عندما لا تتغير المصادر.

---

## 11. شغّل الاختبارات

نفّذ:

```powershell
python -m pytest -q
```

والنتيجة المستهدفة في النسخة الحالية:

```text
9 passed
```

---

## 12. إذا سأل الدكتور: لماذا `student_id` يتكرر؟

الإجابة:

> لأن `final_dataset.csv` ليست Student Table فقط؛ بل تمثل مستوى `Student × Course × Semester`. الطالب الواحد يمكن أن يكون لديه عدة تسجيلات مقررات، لذلك تكرار `student_id` طبيعي في هذا الـgrain. أما `student_ml_dataset.csv` فهي One Row per Student.

---

## 13. إذا سأل الدكتور: لماذا لا نعدل Invalid Values بدل رفضها؟

الإجابة:

> لأن تعديل قيمة غير صالحة دون دليل قد يغيّر الحقيقة الأصلية للبيانات. لذلك المشروع يرفض السجل ويسجل السبب في `rejected_records.csv`، بينما يستخدم Median فقط للقيم الرقمية المفقودة التي تسمح بها الاستراتيجية المحددة في الإعدادات.

---

## 14. إذا سأل الدكتور: كيف تضيف Source جديدًا؟

الإجابة:

> أضيف Source Adapter جديد داخل `app/sources/` ليحول المصدر إلى Contract موحد، ثم يمكن إعادة استخدام طبقات Validation وCleaning وIntegration وTransformation وOutput دون إعادة كتابة المشروع بالكامل.

---

## 15. آخر فحص قبل التسليم

نفّذ بالترتيب:

```powershell
python -m pytest -q
python main.py --mode full
python main.py
```

ثم تأكد من وجود:

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

وأخذ Screenshots لكل مرحلة مطلوبة في التكليف:

```text
Terminal / commands
CSV source
REST API /docs
SQLite
Pipeline execution
Rejected records
Final dataset
Metrics
Logs
Tests
Incremental run
```
