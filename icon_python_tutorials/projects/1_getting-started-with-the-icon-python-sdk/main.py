from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider

icon_service = IconService(HTTPProvider("https://ctz.solidwallet.io", 3))

block = icon_service.get_block("latest")

print(block)
