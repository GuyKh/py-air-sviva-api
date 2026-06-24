"""Common HTTP utilities for the Sviva Air API wrapper.

Adapted for the Sviva Air API's different auth mechanism
(token generation vs. JWT bearer).
"""

import http
import json
import logging
from json import JSONDecodeError
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

import aiohttp
from aiohttp import ClientError, ClientSession

from air_sviva_api.models.exceptions import SvivaAirError

logger = logging.getLogger(__name__)

# Domains for fallback mechanism
PRIMARY_DOMAIN = "air-papi.sviva.gov.il"
SECONDARY_DOMAIN = "air-api.sviva.gov.il"
FALLBACK_DOMAINS = {
    PRIMARY_DOMAIN: SECONDARY_DOMAIN,
    SECONDARY_DOMAIN: PRIMARY_DOMAIN,
}

# HTTP status codes that should trigger a fallback
RETRYABLE_STATUS_CODES = {404, 500, 502, 503, 504}


def _get_fallback_url(url: str) -> Optional[str]:
    """Get a fallback URL by swapping the domain between primary and secondary.

    Args:
        url: The original URL

    Returns:
        The fallback URL if the domain is in our fallback map, otherwise None
    """
    try:
        parsed = urlparse(url)
        if parsed.netloc in FALLBACK_DOMAINS:
            new_netloc = FALLBACK_DOMAINS[parsed.netloc]
            return urlunparse(parsed._replace(netloc=new_netloc))
    except Exception:
        # If we can't parse the URL, don't fallback
        pass
    return None


async def send_get_request(
    session: ClientSession,
    url: str,
    timeout: Optional[int | aiohttp.ClientTimeout] = 30,
    headers: Optional[dict[str, str]] = None,
) -> Any:
    """Send an async GET request and return the JSON response.

    Args:
        session: The aiohttp ClientSession to use.
        url: The URL to request.
        timeout: Timeout in seconds or aiohttp.ClientTimeout object.
        headers: Optional HTTP headers.

    Returns:
        The parsed JSON response (dict or list), or None for 204 No Content.

    Raises:
        SvivaAirError: If the request fails or returns an unsuccessful status.
    """
    last_error: Optional[Exception] = None
    urls_to_try = [url]
    fallback_url = _get_fallback_url(url)
    if fallback_url:
        urls_to_try.append(fallback_url)

    for attempt_url in urls_to_try:
        try:
            if isinstance(timeout, int):
                timeout = aiohttp.ClientTimeout(total=timeout)

            resp = await session.get(url=attempt_url, headers=headers, timeout=timeout)
            # Handle 204 No Content as a successful response with no data
            if resp.status == http.HTTPStatus.NO_CONTENT:
                return None
            json_resp = await resp.json(content_type=None)
        except TimeoutError as ex:
            last_error = SvivaAirError(-1, f"Request timed out: ({str(ex)})")
            continue  # Try next URL if available
        except ClientError as ex:
            last_error = SvivaAirError(-1, f"HTTP client error: ({str(ex)})")
            continue  # Try next URL if available
        except JSONDecodeError as ex:
            # JSON decode errors are not retryable as they indicate invalid response format
            raise SvivaAirError(-1, f"Invalid JSON response: {str(ex)}")

        if resp.status != http.HTTPStatus.OK:
            error_detail = ""
            if isinstance(json_resp, dict):
                error_detail = json.dumps(json_resp)
            # Check if status is retryable
            if resp.status in RETRYABLE_STATUS_CODES:
                last_error = SvivaAirError(resp.status, f"API returned status {resp.status}: {error_detail}")
                continue  # Try next URL if available
            else:
                # Non-retryable error, raise immediately
                raise SvivaAirError(resp.status, f"API returned status {resp.status}: {error_detail}")

        return json_resp

    # If we exhausted all URLs, raise the last error
    if last_error:
        raise last_error
    # This should not happen, but just in case
    raise SvivaAirError(-1, "Failed to retrieve data from all attempted URLs")


async def send_post_request(
    session: ClientSession,
    url: str,
    timeout: Optional[int | aiohttp.ClientTimeout] = 30,
    headers: Optional[dict[str, str]] = None,
    data: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> Any:
    """Send an async POST request and return the JSON response.

    Args:
        session: The aiohttp ClientSession to use.
        url: The URL to request.
        timeout: Timeout in seconds or aiohttp.ClientTimeout object.
        headers: Optional HTTP headers.
        data: Optional form data to send.
        json_data: Optional JSON-serializable data to send.

    Returns:
        The parsed JSON response (dict or list).

    Raises:
        SvivaAirError: If the request fails or returns a non-200 status.
    """
    last_error: Optional[Exception] = None
    urls_to_try = [url]
    fallback_url = _get_fallback_url(url)
    if fallback_url:
        urls_to_try.append(fallback_url)

    for attempt_url in urls_to_try:
        try:
            if isinstance(timeout, int):
                timeout = aiohttp.ClientTimeout(total=timeout)

            resp = await session.post(
                url=attempt_url,
                data=data,
                json=json_data,
                headers=headers,
                timeout=timeout,
            )
            json_resp: Any = await resp.json(content_type=None)
        except TimeoutError as ex:
            last_error = SvivaAirError(-1, f"Request timed out: ({str(ex)})")
            continue  # Try next URL if available
        except ClientError as ex:
            last_error = SvivaAirError(-1, f"HTTP client error: ({str(ex)})")
            continue  # Try next URL if available
        except JSONDecodeError as ex:
            # JSON decode errors are not retryable as they indicate invalid response format
            raise SvivaAirError(-1, f"Invalid JSON response: {str(ex)}")

        if resp.status != http.HTTPStatus.OK:
            error_detail = ""
            if isinstance(json_resp, dict):
                error_detail = json.dumps(json_resp)
            # Check if status is retryable
            if resp.status in RETRYABLE_STATUS_CODES:
                last_error = SvivaAirError(resp.status, f"API returned status {resp.status}: {error_detail}")
                continue  # Try next URL if available
            else:
                # Non-retryable error, raise immediately
                raise SvivaAirError(resp.status, f"API returned status {resp.status}: {error_detail}")

        return json_resp

    # If we exhausted all URLs, raise the last error
    if last_error:
        raise last_error
    # This should not happen, but just in case
    raise SvivaAirError(-1, "Failed to retrieve data from all attempted URLs")


async def send_text_get_request(
    session: ClientSession,
    url: str,
    timeout: Optional[int | aiohttp.ClientTimeout] = 30,
    headers: Optional[dict[str, str]] = None,
) -> str:
    """Send an async GET request and return the raw text response.

    Args:
        session: The aiohttp ClientSession to use.
        url: The URL to request.
        timeout: Timeout in seconds or aiohttp.ClientTimeout object.
        headers: Optional HTTP headers.

    Returns:
        The raw text response body.

    Raises:
        SvivaAirError: If the request fails or returns a non-200 status.
    """
    last_error: Optional[Exception] = None
    urls_to_try = [url]
    fallback_url = _get_fallback_url(url)
    if fallback_url:
        urls_to_try.append(fallback_url)

    for attempt_url in urls_to_try:
        try:
            if isinstance(timeout, int):
                timeout = aiohttp.ClientTimeout(total=timeout)

            resp = await session.get(url=attempt_url, headers=headers, timeout=timeout)
            text_resp = await resp.text()
        except TimeoutError as ex:
            last_error = SvivaAirError(-1, f"Request timed out: ({str(ex)})")
            continue  # Try next URL if available
        except ClientError as ex:
            last_error = SvivaAirError(-1, f"HTTP client error: ({str(ex)})")
            continue  # Try next URL if available

        if resp.status != http.HTTPStatus.OK:
            # Check if status is retryable
            if resp.status in RETRYABLE_STATUS_CODES:
                last_error = SvivaAirError(resp.status, f"API returned status {resp.status}")
                continue  # Try next URL if available
            else:
                # Non-retryable error, raise immediately
                raise SvivaAirError(resp.status, f"API returned status {resp.status}")

        return text_resp

    # If we exhausted all URLs, raise the last error
    if last_error:
        raise last_error
    # This should not happen, but just in case
    raise SvivaAirError(-1, "Failed to retrieve data from all attempted URLs")


async def send_text_post_request(
    session: ClientSession,
    url: str,
    timeout: Optional[int | aiohttp.ClientTimeout] = 30,
    headers: Optional[dict[str, str]] = None,
    data: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> str:
    """Send an async POST request and return the raw text response.

    Args:
        session: The aiohttp ClientSession to use.
        url: The URL to request.
        timeout: Timeout in seconds or aiohttp.ClientTimeout object.
        headers: Optional HTTP headers.
        data: Optional form data to send.
        json_data: Optional JSON-serializable data to send.

    Returns:
        The raw text response body.

    Raises:
        SvivaAirError: If the request fails or returns a non-200 status.
    """
    last_error: Optional[Exception] = None
    urls_to_try = [url]
    fallback_url = _get_fallback_url(url)
    if fallback_url:
        urls_to_try.append(fallback_url)

    for attempt_url in urls_to_try:
        try:
            if isinstance(timeout, int):
                timeout = aiohttp.ClientTimeout(total=timeout)

            resp = await session.post(
                url=attempt_url,
                data=data,
                json=json_data,
                headers=headers,
                timeout=timeout,
            )
            text_resp = await resp.text()
        except TimeoutError as ex:
            last_error = SvivaAirError(-1, f"Request timed out: ({str(ex)})")
            continue  # Try next URL if available
        except ClientError as ex:
            last_error = SvivaAirError(-1, f"HTTP client error: ({str(ex)})")
            continue  # Try next URL if available

        if resp.status != http.HTTPStatus.OK:
            # Check if status is retryable
            if resp.status in RETRYABLE_STATUS_CODES:
                last_error = SvivaAirError(
                    resp.status,
                    f"API returned status {resp.status} for URL {attempt_url}. "
                    f"Headers: {headers}. Response: {text_resp[:200]}",
                )
                continue  # Try next URL if available
            else:
                # Non-retryable error, raise immediately
                raise SvivaAirError(
                    resp.status,
                    f"API returned status {resp.status} for URL {attempt_url}. "
                    f"Headers: {headers}. Response: {text_resp[:200]}",
                )

        return text_resp

    # If we exhausted all URLs, raise the last error
    if last_error:
        raise last_error
    # This should not happen, but just in case
    raise SvivaAirError(-1, "Failed to retrieve data from all attempted URLs")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth using Haversine formula.

    Args:
        lat1: Latitude of point 1 in decimal degrees
        lon1: Longitude of point 1 in decimal degrees
        lat2: Latitude of point 2 in decimal degrees
        lon2: Longitude of point 2 in decimal degrees

    Returns:
        Distance between the two points in kilometers
    """
    import math

    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers
    r = 6371.0

    return c * r
