import sqlalchemy as sa
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log

device_router = APIRouter(prefix="/devices", tags=["devices"])


@device_router.put("/{device_id}", status_code=status.HTTP_200_OK, response_model=s.DeviceOut)
def update_device(
    device_id: str,
    device: s.DeviceIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Endpoint to update the device information, or create a new device if it does not exist.
    Currently only the device push token can be updated.
    """
    existing_device: m.Device = db.scalar(
        db.query(m.Device).where(sa.and_(m.Device.device_id == device_id, m.Device.is_deleted.is_(False)))
    )
    if not existing_device:
        log(log.INFO, "[update_device] Device not found. Creating new device")
        new_device = m.Device(**device.model_dump(), user_id=current_user.id, device_id=device_id)
        db.add(new_device)
        db.commit()
        log(log.INFO, "[update_device] Device [%s] created", new_device.id)
        return new_device

    if existing_device.user_id != current_user.id:
        log(log.ERROR, "[update_device] Device [%s] does not belong to the user [%s]", device_id, current_user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device does not belong to the user")

    if existing_device.user.is_deleted:
        log(log.ERROR, "[update_device] User [%s] is deleted. Can't update device [%s]", current_user.id, device_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is deleted. Can't update device")

    existing_device.push_token = device.push_token
    db.commit()

    log(log.INFO, "[update_device] Device [%s] updated", existing_device.id)
    return existing_device
