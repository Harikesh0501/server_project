from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import ManagedDatabase
from app.schemas.database import DatabaseCreate, DatabaseResponse, DatabaseBackupResponse
from app.services.db_provisioner import db_provisioner
from app.services.secret_service import secret_manager

router = APIRouter(prefix="/databases", tags=["Managed Databases"])

class RestoreRequest(BaseModel):
    backup_filename: str

def _format_db_response(db_item: ManagedDatabase, decrypted_url: str | None = None) -> DatabaseResponse:
    return DatabaseResponse(
        id=db_item.id,
        project_id=db_item.project_id,
        name=db_item.name,
        engine=db_item.engine,
        version=db_item.version,
        port=db_item.port,
        database_name=db_item.database_name,
        username=db_item.username,
        status=db_item.status,
        connection_url=decrypted_url,
        created_at=db_item.created_at,
        updated_at=db_item.updated_at
    )

@router.post("", response_model=DatabaseResponse, status_code=status.HTTP_201_CREATED)
async def create_database(payload: DatabaseCreate, db: AsyncSession = Depends(get_db)):
    """
    Provisions a new production-ready, isolated PostgreSQL 16 or Redis 7 database.
    Attaches to deploy-private-net, sets up persistent volumes, and injects credentials.
    """
    try:
        db_record = await db_provisioner.provision_database(
            name=payload.name,
            engine=payload.engine,
            project_id=payload.project_id,
            version=payload.version,
            db_session=db
        )

        decrypted_url = None
        if db_record.connection_url_secret_id:
            decrypted_url = await secret_manager.get_decrypted_secret(
                db_record.project_id,
                "DATABASE_URL" if db_record.engine == "postgres" else "REDIS_URL",
                db
            )

        return _format_db_response(db_record, decrypted_url)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("", response_model=list[DatabaseResponse])
async def list_databases(project_id: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    """
    Lists all managed databases across the platform, optionally filtered by project_id.
    """
    query = select(ManagedDatabase)
    if project_id:
        query = query.where(ManagedDatabase.project_id == project_id)
    
    query = query.order_by(ManagedDatabase.created_at.desc())
    result = await db.execute(query)
    databases = result.scalars().all()

    return [_format_db_response(d) for d in databases]

@router.get("/{database_id}", response_model=DatabaseResponse)
async def get_database(database_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches details and connection parameters for a specific database instance.
    """
    res = await db.execute(select(ManagedDatabase).where(ManagedDatabase.id == database_id))
    db_record = res.scalar_one_or_none()
    if not db_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Database {database_id} not found.")

    decrypted_url = None
    if db_record.connection_url_secret_id:
        decrypted_url = await secret_manager.get_decrypted_secret(
            db_record.project_id,
            "DATABASE_URL" if db_record.engine == "postgres" else "REDIS_URL",
            db
        )

    return _format_db_response(db_record, decrypted_url)

@router.post("/{database_id}/backup", response_model=DatabaseBackupResponse)
async def backup_database(database_id: str):
    """
    Triggers an on-demand compressed backup (pg_dump) for a PostgreSQL database.
    """
    try:
        data = await db_provisioner.create_backup(database_id)
        return DatabaseBackupResponse(**data)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{database_id}/restore")
async def restore_database(database_id: str, payload: RestoreRequest):
    """
    Restores a PostgreSQL database instance from an existing backup dump file.
    """
    try:
        await db_provisioner.restore_database(database_id, payload.backup_filename)
        return {"status": "success", "message": f"Database restored from {payload.backup_filename}"}
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{database_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_database(database_id: str):
    """
    Terminates and removes a managed database container and its database metadata.
    """
    await db_provisioner.delete_database(database_id)
    return None
