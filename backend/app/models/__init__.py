# Importing every model here makes SQLAlchemy know about all tables when we create them.
from app.models.complaint import Complaint  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.fleet import Driver, Truck  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.provider import ServiceProvider  # noqa: F401
from app.models.route import CollectionStop, Route  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.waste_bin import WasteBin  # noqa: F401
from app.models.sms_log import SmsLog  # noqa: F401
from app.models.webhook_log import WebhookLog  # noqa: F401
