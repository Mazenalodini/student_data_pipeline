# Online REST API Service

This folder contains the REST API that serves the academic source used by the pipeline.

## API contract

`GET /students`

```json
[
  {
    "student_id": 1001,
    "gpa": 3.7,
    "attendance": 94,
    "status": "active"
  }
]
```

## Useful endpoints

- `/` — service information
- `/health` — health check
- `/students` — full dataset
- `/students/{student_id}` — one student
- `/students?status=active` — filtered students
- `/meta` — metadata and schema
- `/docs` — OpenAPI/Swagger UI

## Cloud deployment

The service is ready for cloud deployment with:

- `render.yaml` for a Render-style deployment configuration
- `Dockerfile` for container-based platforms
- a separate `requirements.txt`

After deployment, use the public HTTPS `/students` URL as the pipeline's API source.
