from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
import os
import secrets
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
CALLBACK_URL = os.getenv("CALLBACK_URL", "http://localhost:8000/user/github-code")
GITHUB_API_URL = "https://api.github.com"
REPO_NAME = os.getenv("REPO_NAME", "UNotes-Data")

user_sessions = {}


@router.get("/")
async def root():
    return {
        "message": "GitHub Auto Repo Manager",
        "workflow": "Login -> Check if repo exists -> Create if not exists -> Return repo info",
        "endpoint": "GET /login - Start OAuth and auto-manage repo"
    }


@router.get("/github-login")
async def github_login():
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    state = secrets.token_urlsafe(32)
    scopes = "repo"
    
    # Adding prompt=consent forces GitHub to show the authorization page every time
    auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&"
        f"redirect_uri={CALLBACK_URL}&"
        f"scope={scopes}&"
        f"state={state}&"
        f"prompt=consent"
    )
    
    return RedirectResponse(url=auth_url)


async def check_repo_exists(token: str, username: str, repo_name: str) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{username}/{repo_name}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None


async def create_private_repo(token: str, repo_name: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    payload = {
        "name": repo_name,
        "description": f"Private repository for application data",
        "private": True,
        "auto_init": True,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_URL}/user/repos",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create repository: {response.text}"
            )


@router.get("/github-code")
async def github_callback(request: Request, code: str, state: Optional[str] = None):
    
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    async with httpx.AsyncClient() as client:
        try:
            
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": CALLBACK_URL
                },
                timeout=30.0
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(status_code=400, detail="No access token received")
            
            
            user_response = await client.get(
                f"{GITHUB_API_URL}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                timeout=30.0
            )
            
            user_data = user_response.json()
            username = user_data.get("login")
            user_id = user_data.get("id")
            
            
            existing_repo = await check_repo_exists(access_token, username, REPO_NAME)
            
            if existing_repo:
                repo_info = {
                    "action": "existing",
                    "message": f"Using existing repository: {REPO_NAME}",
                    "repo": {
                        "name": existing_repo["name"],
                        "full_name": existing_repo["full_name"],
                        "html_url": existing_repo["html_url"],
                        "private": existing_repo["private"]
                    }
                }
            else:
                new_repo = await create_private_repo(access_token, REPO_NAME)
                repo_info = {
                    "action": "created",
                    "message": f"Created new private repository: {REPO_NAME}",
                    "repo": {
                        "name": new_repo["name"],
                        "full_name": new_repo["full_name"],
                        "html_url": new_repo["html_url"],
                        "private": new_repo["private"]
                    }
                }
            
            
            session_id = secrets.token_urlsafe(32)
            user_sessions[session_id] = {
                "token": access_token,
                "username": username,
                "user_id": user_id,
                "repo_info": repo_info
            }
            
            auth_data = {
                "session_id": session_id,
                "access_token": access_token,
                "username": username,
                "user_id": user_id,
                "repository": repo_info
            }
            
            return templates.TemplateResponse("login_success.html", {
                "request": request,
                "auth_data": auth_data
            })
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"OAuth request failed: {str(e)}")


@router.get("/github-logout")
async def github_logout(request: Request):
    
    request.session.clear()
    
    return templates.TemplateResponse("logout.html", {"request": request})

