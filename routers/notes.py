from fastapi import Request, Form, APIRouter, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from utils import pick_color, get_date_string, get_uuid
import httpx
import json
import base64
from typing import Optional


router = APIRouter()
templates = Jinja2Templates(directory="templates")

GITHUB_API_URL = "https://api.github.com"


def get_note_list(request: Request) -> list:
    if "note_list" not in request.session:
        request.session["note_list"] = []
    return request.session["note_list"]


def set_note_list(request: Request, notes: list):
    request.session["note_list"] = notes


def clear_note_list(request: Request):
    if "note_list" in request.session:
        del request.session["note_list"]


async def create_or_update_github_file(
    access_token: str,
    username: str,
    repo_name: str,
    file_path: str,
    content: dict,
    message: str,
    sha: Optional[str] = None
):
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{file_path}"
    
    json_content = json.dumps(content, indent=2)
    encoded_content = base64.b64encode(json_content.encode()).decode()
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "message": message,
        "content": encoded_content
    }
    
    if sha:
        payload["sha"] = sha
    
    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=payload, timeout=30.0)
        return response.status_code in [200, 201], response.json() if response.status_code in [200, 201] else None


async def get_github_file_sha(
    access_token: str,
    username: str,
    repo_name: str,
    file_path: str
):
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{file_path}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            if response.status_code == 200:
                return response.json().get("sha")
        except Exception:
            pass
    return None


async def delete_github_file(
    access_token: str,
    username: str,
    repo_name: str,
    file_path: str,
    message: str
):
    sha = await get_github_file_sha(access_token, username, repo_name, file_path)
    if not sha:
        return False
    
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{file_path}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": message,
        "sha": sha
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method="DELETE",
                url=url, 
                headers=headers,
                json=payload,
                timeout=30.0
            )
            return response.status_code == 200
        except Exception:
            return False


async def load_notes_from_github(access_token: str, username: str, repo_name: str):
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/notes"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    notes = []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            if response.status_code == 200:
                files = response.json()
                
                for file in files:
                    if file["name"].endswith(".json"):
                        file_response = await client.get(
                            file["download_url"],
                            timeout=30.0
                        )
                        if file_response.status_code == 200:
                            note = file_response.json()
                            notes.append(note)
        except Exception:
            pass
    
    return notes


@router.get("/", response_class=HTMLResponse)
async def get_notes(request: Request):
    note_list = get_note_list(request)
    return templates.TemplateResponse("notes_list.html", {"request": request, "notes": note_list})


@router.get("/load", response_class=HTMLResponse)
async def load_notes(
    request: Request,
    access_token: str = Query(None),
    username: str = Query(None),
    repo_name: str = Query(None)
):
    if access_token and username and repo_name:
        github_notes = await load_notes_from_github(access_token, username, repo_name)
        if github_notes:
            set_note_list(request, github_notes)
    
    note_list = get_note_list(request)
    return templates.TemplateResponse("notes_list.html", {"request": request, "notes": note_list})


@router.post("/", response_class=HTMLResponse)
async def create_note(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    access_token: str = Form(""),
    username: str = Form(""),
    repo_name: str = Form("")
):
    note_list = get_note_list(request)
    
    if title or description:
        note = {
            "id": get_uuid(),
            "head": title,
            "info": description,
            "date": get_date_string(),
            "color": pick_color()
        }
        note_list.append(note)
        set_note_list(request, note_list)
        
        if access_token and username and repo_name:
            file_path = f"notes/{note['id']}.json"
            await create_or_update_github_file(
                access_token=access_token,
                username=username,
                repo_name=repo_name,
                file_path=file_path,
                content=note,
                message=f"Create note: {title}"
            )
    
    return templates.TemplateResponse("notes_list.html", {"request": request, "notes": note_list})


@router.put("/{note_id}", response_class=HTMLResponse)
async def update_note(
    request: Request,
    note_id: str,
    title: str = Form(""),
    description: str = Form(""),
    access_token: str = Form(""),
    username: str = Form(""),
    repo_name: str = Form("")
):
    note_list = get_note_list(request)
    note = next((n for n in note_list if n["id"] == note_id), None)
    
    if note and (title or description):
        note["head"] = title
        note["info"] = description
        note["date"] = get_date_string()
        set_note_list(request, note_list)
        
        if access_token and username and repo_name:
            file_path = f"notes/{note_id}.json"
            sha = await get_github_file_sha(access_token, username, repo_name, file_path)
            await create_or_update_github_file(
                access_token=access_token,
                username=username,
                repo_name=repo_name,
                file_path=file_path,
                content=note,
                message=f"Update note: {title}",
                sha=sha
            )
    
    return templates.TemplateResponse("single_note.html", {"request": request, "note": note})


@router.delete("/{note_id}", response_class=HTMLResponse)
async def delete_note(
    request: Request,
    note_id: str,
    access_token: str = Query(None),
    username: str = Query(None),
    repo_name: str = Query(None)
):
    note_list = get_note_list(request)
    note_list = [n for n in note_list if n["id"] != note_id]
    set_note_list(request, note_list)
    
    if access_token and username and repo_name:
        file_path = f"notes/{note_id}.json"
        await delete_github_file(
            access_token=access_token,
            username=username,
            repo_name=repo_name,
            file_path=file_path,
            message=f"Delete note: {note_id}"
        )
    
    return HTMLResponse("")