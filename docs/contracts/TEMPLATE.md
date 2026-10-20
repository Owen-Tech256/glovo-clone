# Contract: <phase and feature>

Copy this file for each phase. One row per route or action. Frontend and backend work from this document.

| Field | Content |
|---|---|
| URL and method | |
| Role / permission required | |
| Authentication and ownership check | |
| Form or query fields (name, type, required, limits) | |
| Validation rules and error messages | |
| Handler and service function | |
| Database records read or written | |
| Success response (status, redirect target, flash) | |
| Error responses (400, 403, 404, 409, 422, 429) | |
| Authorization failure behaviour | |
| CSRF required | |
| Rate limit | |
| Covering tests | |

Notes: use POST then redirect then GET for form submissions, prevent double submission, keep submitted values on validation errors.
