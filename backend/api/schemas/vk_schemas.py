from pydantic import BaseModel, Field


# Query of the VK ID redirect: code, state and device_id on success, error and error_description otherwise.
class VkCallbackParams(BaseModel):
    state: str = Field(pattern=r"^[A-Za-z0-9_-]{1,128}$", description="State issued by the bot")
    code: str | None = Field(default=None, max_length=1024, description="Authorization code")
    device_id: str | None = Field(default=None, max_length=512, description="VK ID device id for the code exchange")
    error: str | None = Field(default=None, max_length=256, description="Error code when the user cancelled")
