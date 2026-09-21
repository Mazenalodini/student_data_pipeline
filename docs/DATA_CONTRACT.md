# Data Contracts

## CSV contract

```text
student_id: integer, required, unique
student_name: string, required
age: integer, expected 16..80
major: string
city: string
```

## REST API contract

```json
{
  "student_id": 1001,
  "gpa": 3.45,
  "attendance": 92,
  "status": "Active"
}
```

Rules:

- `student_id` required and unique within the API response
- `gpa` expected range 0..4
- `attendance` expected range 0..100

## SQLite contract

### courses

```text
course_id: integer primary key
course_name: text unique and required
credit_hours: integer 1..6
```

### enrollments

```text
enrollment_id: integer primary key
student_id: integer business key
course_id: foreign key to courses
semester: required text
score: 0..100 or NULL before cleaning
```
