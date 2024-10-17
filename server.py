#!/usr/bin/env python3

from contextlib import asynccontextmanager
import logging
from typing import Any
from playwright.async_api import async_playwright, Page
from litestar import Litestar, get, Request, Response
from litestar.datastructures import State
from pydantic_settings import BaseSettings
from PIL import Image
from io import BytesIO


logger = logging.getLogger(__name__)

SCALE = 1.4
SIDEBAR_WIDTH = 256
HEADER_HEIGHT = 56
VIEW_WIDTH = 960
VIEW_HEIGHT = 540


class Settings(BaseSettings):
    headless: bool = True
    token: str = ''
    homeassistant_url: str = ''
    homeassistant_username: str = ''
    homeassistant_password: str = ''

    class Config:
        extra = "ignore"
        env_file = '.env'
        env_file_encoding = 'utf-8'


@asynccontextmanager
async def browser(state: State):
    settings: Settings = state['settings']

    playwright = await async_playwright().start()
    chromium = playwright.chromium
    browser = await chromium.launch(headless=settings.headless)
    context = await browser.new_context(viewport={ 'width': VIEW_WIDTH + SIDEBAR_WIDTH, 'height': VIEW_HEIGHT + HEADER_HEIGHT }, device_scale_factor=3, is_mobile=True)
    context.set_default_timeout(5_000)
    page = await context.new_page()

    state['page'] = page
    state['browser'] = browser

    _ = await page.goto(settings.homeassistant_url)
    _ = await page.wait_for_selector("ha-authorize")
    _ = await page.wait_for_selector(".action mwc-button")

    await page.type('[name="username"]', settings.homeassistant_username)
    await page.type('[name="password"]', settings.homeassistant_password)
    await page.click('.action mwc-button')

    _ = await page.wait_for_selector("home-assistant-main #view")

    yield page

    await browser.close()


async def handle_notification(page: Page):
    notification = await page.query_selector('notification-manager')
    if not notification:
        print('no notification')
        return

    toast = await notification.query_selector('ha-toast')
    if not toast:
        print('notification has no toast')
        return

    if not await toast.is_visible():
        print('notification toast not visible')
        return

    button = await toast.query_selector('mwc-button')
    if not button:
        print('toast no button')
        return

    print('notification button click')
    await button.click()


async def get_screenshot(state: State):
    async with browser(state) as page:
        view = await page.wait_for_selector("home-assistant-main #view")
        assert view

        await handle_notification(page)

        image_data = await page.screenshot(
            type="png",
            animations="disabled",
            clip={
                "x": SIDEBAR_WIDTH,
                "y": HEADER_HEIGHT,
                "width": VIEW_WIDTH,
                "height": VIEW_HEIGHT,
            },
            timeout=10_000,
        )
        image_bytes = BytesIO(image_data)

        image = Image.open(image_bytes)
        new_image = (
            image.resize(size=(VIEW_WIDTH, VIEW_HEIGHT))
            .convert("L")
            .rotate(90, expand=True)
        )
        _ = image_bytes.seek(0)
        new_image.save(image_bytes, format="PNG", quality=80, optimize=True)
        print("Image ready, size:", len(image_bytes.getvalue()))
        return image_bytes.getvalue()


@get("/")
async def index(request: Request[Any, Any, Any], state: State) -> Response[Any]:
    auth = request.headers.get('Authorization')
    settings: Settings = state['settings']
    token = settings.token

    if auth != f'Bearer {token}':
        logger.error('Unauthorized, "%s" is invalid', auth)
        return Response('Unauthorized', status_code=401, media_type='text/plain')

    try:
        return Response(await get_screenshot(state), media_type='image/png')
    except Exception as e:
        logger.exception(e)
        return Response('Error', status_code=500, media_type='text/plain')

settings = Settings()
if not settings.token:
    raise Exception('No token set!')
if not settings.homeassistant_url:
    raise Exception('No Home Assistant URL set!')
if not settings.homeassistant_username:
    raise Exception('No Home Assistant username set!')
if not settings.homeassistant_password:
    raise Exception('No Home Assistant password set!')

app = Litestar(
    route_handlers=[index],
    state=State(
        {
            "settings": Settings(),
        }
    ),
)
