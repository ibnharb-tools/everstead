# Everstead Auth Testing

Demo user (seeded at startup): demo@everstead.app / Everstead123!

## API checks (use REACT_APP_BACKEND_URL or localhost:8001)
1. Signup
   curl -X POST $URL/api/auth/signup -H "Content-Type: application/json" \
     -d '{"name":"Test","email":"new@example.com","password":"secret123"}'
   -> 201 { token, user{id,name,email} }

2. Login
   curl -X POST $URL/api/auth/login -H "Content-Type: application/json" \
     -d '{"email":"demo@everstead.app","password":"Everstead123!"}'
   -> 200 { token, user }

3. Me (needs token)
   curl $URL/api/auth/me -H "Authorization: Bearer <token>"
   -> { user }

4. Save a retrofit (needs token, send full assessment object + label)
   POST $URL/api/retrofits  body: { "assessment": {..}, "label": "Our house" } -> 201 { id, label, createdAt }

5. List retrofits -> GET $URL/api/retrofits -> { retrofits: [...] }
6. Get one -> GET $URL/api/retrofits/{id} -> { id, label, createdAt, assessment }
7. Delete -> DELETE $URL/api/retrofits/{id} -> { ok: true }

Errors use the contract envelope: { "error": { "code", "message", "field" } }
- Bad login -> 401 INVALID_CREDENTIALS
- Duplicate signup email -> 409 EMAIL_IN_USE
- Missing/invalid token -> 401 UNAUTHORIZED
- Unknown retrofit id -> 404 NOT_FOUND
- OAuth -> 501 NOT_IMPLEMENTED
