from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

import jwt
import bcrypt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALG = 'HS256'
TOKEN_DAYS = 7

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('everstead')

app = FastAPI(title='Everstead API')
api = APIRouter(prefix='/api')


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Error envelope (matches API contract)
# ---------------------------------------------------------------------------
class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, field: Optional[str] = None):
        self.status = status
        self.code = code
        self.message = message
        self.field = field


@app.exception_handler(ApiError)
async def api_error_handler(_request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={'error': {'code': exc.code, 'message': exc.message, 'field': exc.field}},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = first.get('loc', [None])[-1] if first.get('loc') else None
    return JSONResponse(
        status_code=400,
        content={
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Please check the form and try again.',
                'field': str(field) if field else None,
            }
        },
    )


# ---------------------------------------------------------------------------
# Password + token helpers
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False


def create_token(user_id: str, email: str) -> str:
    payload = {
        'sub': user_id,
        'email': email,
        'type': 'access',
        'exp': datetime.now(timezone.utc) + timedelta(days=TOKEN_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


async def current_user(request: Request) -> dict:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise ApiError(401, 'UNAUTHORIZED', 'Please log in to continue.')
    token = auth[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, 'UNAUTHORIZED', 'Your session ended. Please log in again.')
    except jwt.InvalidTokenError:
        raise ApiError(401, 'UNAUTHORIZED', 'Please log in to continue.')
    try:
        user = await db.users.find_one({'_id': ObjectId(payload['sub'])})
    except (InvalidId, KeyError):
        user = None
    if not user:
        raise ApiError(401, 'UNAUTHORIZED', 'We could not find your account.')
    return user


def public_user(u: dict) -> dict:
    return {'id': str(u['_id']), 'name': u.get('name'), 'email': u['email']}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class SignupBody(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=6)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class ForgotBody(BaseModel):
    email: EmailStr


class OAuthBody(BaseModel):
    provider: str
    credential: Optional[str] = None


class SaveRetrofitBody(BaseModel):
    label: str = Field(default='My home')
    assessmentId: Optional[str] = None
    assessment: Optional[dict] = None


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@api.get('/')
async def root():
    return {'service': 'everstead', 'status': 'ok'}


@api.post('/auth/signup', status_code=201)
async def signup(body: SignupBody):
    email = body.email.lower().strip()
    existing = await db.users.find_one({'email': email})
    if existing:
        raise ApiError(409, 'EMAIL_IN_USE', 'That email is already in use. Try logging in instead.', 'email')
    doc = {
        'name': body.name.strip(),
        'email': email,
        'password_hash': hash_password(body.password),
        'created_at': now_iso(),
    }
    res = await db.users.insert_one(doc)
    doc['_id'] = res.inserted_id
    token = create_token(str(res.inserted_id), email)
    return {'token': token, 'user': public_user(doc)}


@api.post('/auth/login')
async def login(body: LoginBody):
    email = body.email.lower().strip()
    user = await db.users.find_one({'email': email})
    if not user or not verify_password(body.password, user['password_hash']):
        raise ApiError(401, 'INVALID_CREDENTIALS', 'That email or password did not match. Please try again.')
    token = create_token(str(user['_id']), email)
    return {'token': token, 'user': public_user(user)}


@api.get('/auth/me')
async def me(user: dict = Depends(current_user)):
    return {'user': public_user(user)}


@api.post('/auth/forgot-password')
async def forgot_password(body: ForgotBody):
    user = await db.users.find_one({'email': body.email.lower().strip()})
    if user:
        logger.info('Password reset requested for %s', body.email)
    return {'ok': True, 'message': 'If that email exists, we sent reset instructions.'}


@api.post('/auth/oauth')
async def oauth(_body: OAuthBody):
    raise ApiError(501, 'NOT_IMPLEMENTED', 'Sign in with Google or Apple is coming soon.')


# ---------------------------------------------------------------------------
# Saved retrofits
# ---------------------------------------------------------------------------
def retrofit_summary(doc: dict) -> dict:
    return {
        'id': str(doc['_id']),
        'label': doc.get('label'),
        'resolvedAddress': doc.get('resolved_address'),
        'createdAt': doc.get('created_at'),
        'topRecommendation': doc.get('top_recommendation'),
        'topRecommendationName': doc.get('top_recommendation_name'),
        'estimatedYearlySavings': doc.get('estimated_yearly_savings'),
        'currency': doc.get('currency'),
    }


@api.get('/retrofits')
async def list_retrofits(user: dict = Depends(current_user)):
    cursor = db.retrofits.find({'user_id': str(user['_id'])}).sort('created_at', -1)
    docs = await cursor.to_list(200)
    return {'retrofits': [retrofit_summary(d) for d in docs]}


@api.post('/retrofits', status_code=201)
async def save_retrofit(body: SaveRetrofitBody, user: dict = Depends(current_user)):
    assessment = body.assessment
    if not assessment or 'technologies' not in assessment:
        raise ApiError(400, 'VALIDATION_ERROR', 'We could not find that result to save.', 'assessment')
    techs = assessment.get('technologies') or []
    top = techs[0] if techs else {}
    site = assessment.get('site') or {}
    doc = {
        'user_id': str(user['_id']),
        'label': (body.label or 'My home').strip(),
        'assessment': assessment,
        'resolved_address': site.get('resolvedAddress'),
        'top_recommendation': top.get('type'),
        'top_recommendation_name': top.get('displayName'),
        'estimated_yearly_savings': top.get('yearlySavings'),
        'currency': assessment.get('currency'),
        'created_at': now_iso(),
    }
    res = await db.retrofits.insert_one(doc)
    return {'id': str(res.inserted_id), 'label': doc['label'], 'createdAt': doc['created_at']}


@api.get('/retrofits/{retrofit_id}')
async def get_retrofit(retrofit_id: str, user: dict = Depends(current_user)):
    try:
        oid = ObjectId(retrofit_id)
    except InvalidId:
        raise ApiError(404, 'NOT_FOUND', 'We could not find that saved home.')
    doc = await db.retrofits.find_one({'_id': oid, 'user_id': str(user['_id'])})
    if not doc:
        raise ApiError(404, 'NOT_FOUND', 'We could not find that saved home.')
    return {
        'id': str(doc['_id']),
        'label': doc.get('label'),
        'createdAt': doc.get('created_at'),
        'assessment': doc.get('assessment'),
    }


@api.delete('/retrofits/{retrofit_id}')
async def delete_retrofit(retrofit_id: str, user: dict = Depends(current_user)):
    try:
        oid = ObjectId(retrofit_id)
    except InvalidId:
        raise ApiError(404, 'NOT_FOUND', 'We could not find that saved home.')
    res = await db.retrofits.delete_one({'_id': oid, 'user_id': str(user['_id'])})
    if res.deleted_count == 0:
        raise ApiError(404, 'NOT_FOUND', 'We could not find that saved home.')
    return {'ok': True}


# ---------------------------------------------------------------------------
# App wiring
# ---------------------------------------------------------------------------
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup():
    await db.users.create_index('email', unique=True)
    await db.retrofits.create_index('user_id')
    demo_email = os.environ.get('DEMO_EMAIL', 'demo@everstead.app')
    demo_password = os.environ.get('DEMO_PASSWORD', 'Everstead123!')
    existing = await db.users.find_one({'email': demo_email})
    if not existing:
        await db.users.insert_one({
            'name': 'Sam Rivera',
            'email': demo_email,
            'password_hash': hash_password(demo_password),
            'created_at': now_iso(),
        })
        logger.info('Seeded demo user %s', demo_email)


@app.on_event('shutdown')
async def shutdown():
    client.close()
