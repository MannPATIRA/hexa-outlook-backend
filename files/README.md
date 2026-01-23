# Files Directory

This directory stores drawing files (PDF, DWG) and STEP files (3D CAD models) that are served by the API.

## Structure

- `drawings/` - Drawing files (PDF, DWG, etc.)
- `step/` - STEP files (3D CAD models)

## File Naming

Files should match the names returned by the API:
- Drawing files: e.g., `drawing_PR001_main.pdf`, `drawing_PR001_detail.dwg`
- STEP files: e.g., `model_PR001.step`, `assembly_PR001.step`

## Accessing Files

Files are served via the API endpoint:
- `/api/files/{filename}` - Direct file access
- `/api/files/rfq/{rfq_id}/{filename}` - RFQ-specific file access

## Example

If the API returns `drawing_PR001_main.pdf` in the attachments array, the file can be accessed at:
```
https://your-backend-url/api/files/drawing_PR001_main.pdf
```
