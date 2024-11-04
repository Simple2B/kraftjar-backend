# ruff: noqa: F401

from .auth import verify_apple_token, get_apple_fullname
from .registration import (
    register_user,
    verify_phone,
    set_phone,
    send_otp_to_user,
    validate_phone,
    send_sms_to_user,
    change_password,
)
from .oauth2 import create_access_token
from .service import get_services
from .location import get_locations
from .user import (
    search_users,
    get_user_profile,
    public_search_users,
    get_public_user_profile,
    filter_users_by_locations,
    filter_and_order_users,
)
from .job import (
    search_jobs,
    get_jobs_on_home_page,
    job_statistics,
    filter_jobs_by_locations,
    filter_and_order_jobs,
    create_out_search_jobs,
    get_job,
    get_pending_jobs,
    get_in_progress_jobs,
    get_archived_jobs,
    get_completed_jobs_without_rate,
)
from .rate import update_user_average_rate, update_users_average_rate
from .file import is_image_file, is_video_file, get_file_type, delete_file, create_file
from .application import reject_other_not_accepted_applications

from .push_notification import (
    send_created_job_notification,
    send_apply_application_notification,
    send_accepted_application_notification,
    send_rejected_application_notification,
    send_job_started_notification,
    send_job_finished_notification,
    send_job_confirmed_notification,
    send_job_payment_confirmed_notification,
    notification_is_read_by_user,
)
from .push_notification_settings import create_user_notification_settings
