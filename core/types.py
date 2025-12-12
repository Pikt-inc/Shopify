from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from pydantic import BaseModel, field_validator
import re
from typing import Protocol

GID_REGEX = re.compile(r"^gid://shopify/[A-Za-z]+/\d+$")

class ShopifyResource(BaseModel):
    id: str

    @field_validator("id")
    def validate_gid(cls, v):
        if not GID_REGEX.match(v):
            raise ValueError("id must be a valid Shopify GID (e.g., gid://shopify/Product/1234567890)")
        return v
