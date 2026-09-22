# Data Contracts & SQL Design

هذه الوثيقة تجمع **Data Contracts** للمصادر مع تصميم SQLite واستعلام الاستخراج المستخدم داخل الـPipeline.

---

## 1. CSV Data Contract

المصدر:

```text
data/raw/students.csv
```

الأعمدة الأساسية:

| Column | Type | Rule |
|---|---|---|
| `student_id` | integer | required / business key / unique داخل المصدر |
| `student_name` | string | required |
| `age` | integer | 16..80 |
| `major` | string | optional text |
| `city` | string | optional text ويتم تنظيفه |

يتم تحويل أسماء الأعمدة إلى شكل canonical مثل `student_id` و`student_name`، وتحويل الأنواع الرقمية قبل تنفيذ قواعد الجودة.

---

## 2. REST API Data Contract

Production endpoint الحالي:

```text
https://student-academic-profile-api.vercel.app/students
```

الـresponse عبارة عن JSON array، والعنصر النموذجي:

```json
[
  {
    "student_id": 1001,
    "gpa": 3.7,
    "attendance": 94,
    "status": "Active"
  }
]
```

الأعمدة المطلوبة:

| Column | Rule |
|---|---|
| `student_id` | required / unique داخل الاستجابة |
| `gpa` | 0..4 |
| `attendance` | 0..100 |
| `status` | text |

حالات الخطأ التي يتعامل معها الـAPI adapter تشمل:

```text
Missing/invalid URL
Timeout
Connection Error
HTTP Error
Other Request Error
Invalid JSON
Empty response
Non-array response
Missing required columns
```

كما يستخدم الـadapter retries وbackoff في حالات Timeout وConnection Error حسب إعدادات `config.json`.

---

## 3. SQLite Data Contract

المصدر:

```text
database/students.db
```

### `courses`

```text
course_id     INTEGER PRIMARY KEY
course_name   TEXT NOT NULL UNIQUE
credit_hours  INTEGER NOT NULL, 1..6
```

### `enrollments`

```text
enrollment_id  INTEGER PRIMARY KEY AUTOINCREMENT
student_id     INTEGER NOT NULL
course_id      INTEGER NOT NULL
semester       TEXT NOT NULL
score          REAL أو NULL قبل التنظيف
```

`course_id` يرتبط منطقيًا بالسجل المقابل في `courses.course_id`، وتستخدم عملية الاستخراج SQL `JOIN` لإنتاج بيانات التسجيل مع معلومات المقرر.

Indexes الحالية:

```text
idx_enrollments_student_id
idx_enrollments_course_id
```

---

## 4. SQL Extraction Query

الاستعلام المستخدم في `app/sources/database_source.py` هو:

```sql
SELECT
    e.student_id,
    e.course_id,
    c.course_name,
    c.credit_hours,
    e.semester,
    e.score
FROM enrollments AS e
INNER JOIN courses AS c
    ON c.course_id = e.course_id
ORDER BY e.student_id, e.course_id, e.semester;
```

الغرض من `INNER JOIN` هو الحصول على صفوف التسجيل التي تمتلك Course Definition متوافقًا في جدول `courses`.

---

## 5. Quality Rules Across Sources

```text
student_id  → required
age         → 16..80
gpa         → 0..4
attendance  → 0..100
score       → 0..100
```

كما تتم معالجة:

```text
Missing Values
Duplicates
Extra Spaces
Text normalization
Type conversion
Missing IDs across sources
```

القيمة الرقمية المفقودة تعالج وفق الاستراتيجية الموجودة في `config.json`، بينما القيم غير الصالحة يتم رفضها مع سبب واضح.

---

## 6. Integration Contract

المفتاح المشترك:

```text
student_id
```

والمسؤوليات هي:

```text
CSV
  → Student profile

REST API
  → Academic profile

SQLite
  → Course enrollment facts
```

النتيجة تكون على مستوى:

```text
Student × Course × Semester
```

ثم يمكن بناء Dataset ثانية على مستوى الطالب الواحد لأغراض ML والتحليل.

---

## 7. Final Dataset Schema

`data/processed/final_dataset.csv` يحتوي على الحقول الأساسية التالية:

```text
student_id
student_name
age
major
city
gpa
attendance
status
course_id
course_name
credit_hours
semester
score
performance_level
attendance_status
score_band
source
```

---

## 8. ML Dataset Schema

`data/processed/student_ml_dataset.csv` هو One Row Per Student ويضيف Features تجميعية مثل:

```text
course_count
total_credit_hours
average_score
highest_score
lowest_score
```

---

## 9. Database Setup

إنشاء/إعادة بناء قاعدة SQLite يتم بواسطة:

```powershell
python scripts\setup_database.py
```

ويتم تطبيق التصميم من:

```text
database/schema.sql
```
