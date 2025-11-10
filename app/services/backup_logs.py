from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.api.deps import require_permission
from app.schemas.backup_logs import BackupLogsUpdate, BackupLogsOut
from app.crud import backup_logs as crud