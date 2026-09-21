# SQLite Design

The SQLite source models an academic enrollment relationship.

## Courses

`courses` stores the reusable course dimension:

- `course_id` — primary key
- `course_name` — required and unique
- `credit_hours` — constrained to 1–6

## Enrollments

`enrollments` stores student-course facts:

- `enrollment_id` — primary key
- `student_id` — cross-system business key
- `course_id` — foreign key to `courses`
- `semester` — required
- `score` — quality-checked by the pipeline

## Integration query

The pipeline uses an `INNER JOIN`:

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

The final dataset keeps the student-course grain, while `student_ml_dataset.csv` aggregates the course facts to one row per student.
