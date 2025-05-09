# KOSGE Backend API Documentation

## Authentication

- `POST /api/login`
  - Request: `{ "username": string, "password": string }`
  - Response: `{ "token": string, "user": string }`
  - Status: 200 OK, 401 Unauthorized

## Content Management

- `GET /api/cms/sections`

  - Response: `{ "sections": [{ "section": string, "metadata": object }] }`
  - Status: 200 OK

- `GET /api/cms/content/<section>`

  - Query: `?language=string`
  - Response: `{ "content": string, "metadata": object, "html": string }`
  - Status: 200 OK, 404 Not Found

- `POST /api/cms/content/<section>`

  - Request: `{ "title": string, "content": string, "metadata": object }`
  - Response: `{ "success": boolean, "section": string }`
  - Status: 201 Created, 400 Bad Request

- `PUT /api/cms/content/<section>`

  - Request: `{ "content": string, "metadata": object, "language": string }`
  - Response: `{ "success": boolean, "section": string }`
  - Status: 200 OK, 404 Not Found

- `DELETE /api/cms/content/<section>`
  - Query: `?language=string`
  - Response: `{ "success": boolean }`
  - Status: 200 OK, 404 Not Found

## Image Management

- `GET /api/banners`

  - Response: `{ "banners": [string] }`
  - Status: 200 OK

- `POST /api/banners`

  - Request: `multipart/form-data` with file field
  - Response: `{ "url": string, "filename": string }`
  - Status: 201 Created, 400 Bad Request
  - File types: PNG, JPG, JPEG, GIF
  - Max size: 16MB

- `DELETE /api/banners/<filename>`

  - Response: `{ "success": boolean, "filename": string }`
  - Status: 200 OK, 404 Not Found

- `GET /api/uploads/<filename>`
  - Response: Image file
  - Status: 200 OK, 404 Not Found

## Participant Management

- `GET /api/participants`

  - Response: `{ "participants": [object] }`
  - Status: 200 OK

- `POST /api/participants`
  - Request: `{ "name": string, "email": string?, "message": string?, "banner": string? }`
  - Response: `{ "success": boolean, "participant": object }`
  - Status: 201 Created, 400 Bad Request

## Health Check

- `GET /api/health`
  - Response: `{ "status": "ok" }`
  - Status: 200 OK
