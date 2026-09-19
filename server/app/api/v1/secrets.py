from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.secret import Secret
from app.schemas.secret import SecretCreate, SecretBulkCreate, SecretResponse
from app.services.secret_service import secret_manager

router = APIRouter(prefix="/projects/{project_id}/secrets", tags=["Secrets Vault"])

@router.get("", response_model=list[SecretResponse])
async def list_secrets(project_id: str, db: AsyncSession = Depends(get_db)):
    """
    Lists metadata for all encrypted secrets for a project.
    Values are NEVER returned in plaintext across the wire for zero-trust protection.
    """
    proj_res = await db.execute(select(Project.id).where(Project.id == project_id))
    if not proj_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    query = select(Secret).where(Secret.project_id == project_id).order_by(Secret.key.asc())
    result = await db.execute(query)
    secrets = result.scalars().all()

    return secrets

@router.post("", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def set_secret(project_id: str, payload: SecretCreate, db: AsyncSession = Depends(get_db)):
    """
    Encrypts and persists an environment variable secret with AES-256-GCM.
    """
    proj_res = await db.execute(select(Project.id).where(Project.id == project_id))
    if not proj_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    # Encrypt with project-derived key and fresh 96-bit nonce
    ciphertext, nonce = secret_manager.encrypt(project_id, payload.value)

    # Check if key already exists
    query = select(Secret).where(Secret.project_id == project_id, Secret.key == payload.key)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        existing.encrypted_value = ciphertext
        existing.nonce = nonce
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        new_secret = Secret(
            project_id=project_id,
            key=payload.key,
            encrypted_value=ciphertext,
            nonce=nonce,
            is_system=False
        )
        db.add(new_secret)
        await db.commit()
        await db.refresh(new_secret)
        return new_secret

@router.post("/bulk", response_model=list[SecretResponse])
async def bulk_set_secrets(project_id: str, payload: SecretBulkCreate, db: AsyncSession = Depends(get_db)):
    """
    Bulk uploads and encrypts multiple secrets (used by 'deploy env push').
    """
    proj_res = await db.execute(select(Project.id).where(Project.id == project_id))
    if not proj_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    saved_secrets = []
    for key, value in payload.secrets.items():
        ciphertext, nonce = secret_manager.encrypt(project_id, value)
        query = select(Secret).where(Secret.project_id == project_id, Secret.key == key)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.encrypted_value = ciphertext
            existing.nonce = nonce
            saved_secrets.append(existing)
        else:
            new_sec = Secret(
                project_id=project_id,
                key=key,
                encrypted_value=ciphertext,
                nonce=nonce,
                is_system=False
            )
            db.add(new_sec)
            saved_secrets.append(new_sec)

    await db.commit()
    for s in saved_secrets:
        await db.refresh(s)
    return saved_secrets

@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(project_id: str, key: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes an encrypted secret from the project vault.
    """
    query = select(Secret).where(Secret.project_id == project_id, Secret.key == key)
    result = await db.execute(query)
    secret = result.scalar_one_or_none()

    if not secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Secret '{key}' not found.")

    await db.delete(secret)
    await db.commit()
    return None
