from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.db.models.message_log import MessageLog
from app.db.models.user import User
from app.utils.validators import create_response
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi.encoders import jsonable_encoder
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# --- GET MESSAGE LOGS ENDPOINT ---
@router.get("/all-logs", summary="Getting message logs.")
async def get_all_logs(
    request: Request,
    recipient: Optional[str] = Query(None, description="Filter by recipient email or phone"),
    delivery_status: Optional[bool] = Query(None, description="Filter by message status"),
    date_filter: Optional[str] = Query(
        None,
        description="Date filter: today, yesterday, last_7_days, last_month, custom"
    ),
    start_date: Optional[datetime] = Query(None, description="Start date (for custom range)"),
    end_date: Optional[datetime] = Query(None, description="End date (for custom range)"),
    limit: int = Query(10, gt=0, le=100, description="Number of logs to return per page (max 100)"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        query = db.query(MessageLog)
        now = datetime.now(timezone.utc)

        if recipient:
            query = query.filter(
                or_(
                    MessageLog.recipient.ilike(f"%{recipient}%"),
                    MessageLog.recipient_name.ilike(f"%{recipient}%")  # assuming this column exists
                ),
                MessageLog.user_id == current_user.id
            )
        else:
            query = query.filter(MessageLog.user_id == current_user.id)

        # Status filter
        if delivery_status is not None:
            query = query.filter(MessageLog.status == delivery_status, MessageLog.user_id == current_user.id)

        # Date filter logic
        if date_filter:
            if date_filter == "today":
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end = now
            elif date_filter == "yesterday":
                start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=1)
            elif date_filter == "last_7_days":
                start = now - timedelta(days=7)
                end = now
            elif date_filter == "last_month":
                start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
                end = start.replace(day=1) + timedelta(days=32)
                end = end.replace(day=1) - timedelta(seconds=1)
            elif date_filter == "custom":
                if start_date and end_date:
                    start = start_date
                    end = end_date
                else:
                    return create_response(status.HTTP_400_BAD_REQUEST, "Start and end dates are required for custom range.")
            else:
                return create_response(status.HTTP_400_BAD_REQUEST, "Invalid date filter.")

            query = query.filter(MessageLog.created_at >= start, MessageLog.created_at <= end, MessageLog.user_id == current_user.id)

        logs = query.order_by(MessageLog.created_at.desc()).offset(offset).limit(limit).all()
        total = query.count()
        logs_json = jsonable_encoder(logs)
        base_url = str(request.url).split('?')[0]
        query_params = dict(request.query_params)

        # Calculate next offset
        next_offset = offset + limit
        prev_offset = max(offset - limit, 0)

        next_url = None
        if next_offset < total:
            query_params["offset"] = next_offset
            query_params["limit"] = limit
            next_url = f"{base_url}?{query_params}"

        previous_url = None
        if offset > 0:
            query_params["offset"] = prev_offset
            query_params["limit"] = limit
            previous_url = f"{base_url}?{query_params}"

        data = {
            "result": logs_json,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "total_pages": (total + limit - 1) // limit,
                "next": next_url,
                "previous": previous_url
            }
        }

        return create_response(status.HTTP_200_OK, "Logs retrieved successfully.", data=data)
        
    except Exception as err:
        logger.error(f"Error in get all logs: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
