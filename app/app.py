from fastapi import FastAPI, HTTPException, File, Form,UploadFile, Depends
from app.schemas import postCreate, postResponse, UserRead, UserCreate, UserUpdate
from app.db import Post, create_db_and_table, get_async_session,User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager

from app.images import imagekit
import shutil
import os
import uuid
import tempfile

from app.users import auth_backend, current_active_user, fastapi_users

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_table()
    yield 
    

app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix= "/auth/jwt", tags = ['auth'])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix= "/auth", tags = ['auth'])
app.include_router(fastapi_users.get_reset_password_router(), prefix= "/auth", tags = ['auth'])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix= "/auth", tags = ['auth'])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix= "/users", tags = ['users'])

# @app.get("/hello")
# def hello():
#     return {"message":'hello-world'}

text_posts = {
    1: {"title": "Getting Started with FastAPI", "content": "Learn how to build APIs quickly using FastAPI."},
    2: {"title": "Understanding Python Virtual Environments", "content": "Why virtual environments are important and how to use them."},
    3: {"title": "Building Your First REST API", "content": "Step-by-step guide to creating a RESTful service."},
    4: {"title": "Async Programming in Python", "content": "Introduction to async and await in Python."},
    5: {"title": "Connecting FastAPI to a Database", "content": "How to integrate SQL databases with FastAPI."},
    6: {"title": "Handling Errors Gracefully", "content": "Best practices for error handling in APIs."},
    7: {"title": "Deploying FastAPI Applications", "content": "Different ways to deploy your FastAPI app."},
    8: {"title": "Introduction to Pydantic Models", "content": "Using Pydantic for data validation."},
    9: {"title": "Securing Your API", "content": "Authentication and authorization basics."},
    10: {"title": "Optimizing API Performance", "content": "Tips to make your API faster and scalable."}
}

# @app.get("/items")
# def get_items():
#     return text_posts

# @app.get("/items/{id}")
# def get_items(id: int):
#     if id not in text_posts:
#         raise HTTPException(status_code = 404, detail= "Page Not Found")
#     return text_posts.get(id)

# @app.get("/posts")
# def get_all_posts(limit: int = None):
#     if limit:
#         return list(text_posts.values())[:limit]
#     return text_posts
    
# @app.get("/posts/{id}")
# def get_by_id(id: int) ->  postResponse:
#     if id not in text_posts:
#         raise HTTPException(status_code=404, detail = "Out of the box")
#     return text_posts.get(id)

@app.post("/posts")
def add_post(post: postCreate) : 
    new_post = {"title": post.title, "content": post.content}
    text_posts[max(text_posts.keys()) + 1] = new_post
    return new_post

@app.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    caption: str = Form(""),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    temp_file_path = None

    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        # Generate unique name (since v5 doesn't use options like before)
        unique_filename = f"{uuid.uuid4()}_{file.filename}"

        # Upload using v5 SDK
        with open(temp_file_path, "rb") as f:
            upload_result = imagekit.files.upload(
                file=f.read(),
                file_name=unique_filename,
                tags=["backend-upload"]
            )

        if upload_result and upload_result.url:
            post = Post(
                user_id=user.id,
                caption=caption,
                url=upload_result.url,
                file_type="video" if file.content_type and file.content_type.startswith("video/") else "image",
                file_name=upload_result.name
            )

            session.add(post)
            await session.commit()
            await session.refresh(post)

            return post

        else:
            raise HTTPException(status_code=400, detail="Upload failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        file.file.close()

@app.get("/feed")
async def add_feed(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    post_data = []
    for post in posts:
        post_data.append(
            {
                "id": str(post.id),
                "user_id": str(post.user_id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
                "is_owner": post.user_id == user.id

            }

        )
    return {"posts": post_data}

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, 
                      user: User = Depends(current_active_user),
                      session: AsyncSession = Depends(get_async_session)):
    try:
        post_uuid = uuid.UUID(post_id)

        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail = "Post not found")
        
        if post.user_id != user.id:
            raise HTTPException(status_code =403 , detail = "Not have permission to delete")
        
        await session.delete(post)
        await session.commit()

        return {"success": True, "message": "Post deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail = str(e))
    
