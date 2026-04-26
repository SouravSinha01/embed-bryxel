import aiohttp


class PopcatClient:
	def __init__(self, base_url="https://api.popcat.xyz", session=None):
		self.base_url = base_url.rstrip("/")
		self.session = session

	async def generate(self, endpoint, image_url, secondary_image_url=None, text_value=None):
		endpoint = endpoint.strip().strip("/")
		if not endpoint:
			raise RuntimeError("Popcat endpoint is required.")

		owns_session = self.session is None
		session = self.session or aiohttp.ClientSession()

		try:
			if endpoint == "sadcat":
				if not text_value:
					raise RuntimeError("`sadcat` needs text. Example: `.sadcat life is tough`")
				return await self._fetch(session, endpoint, {"text": text_value})

			if endpoint == "huerotate":
				return await self._fetch(session, endpoint, {"image": image_url, "deg": 120})

			if endpoint == "ship":
				if not secondary_image_url:
					raise RuntimeError("`ship` needs two avatars. Mention another user.")

				params = {
					"user1": image_url,
					"user2": secondary_image_url,
				}
				return await self._fetch(session, endpoint, params)

			for param_name in ("image", "avatar"):
				try:
					return await self._fetch(session, endpoint, {param_name: image_url})
				except RuntimeError as exc:
					message = str(exc)
					if "status 400" in message or "status 404" in message:
						continue
					raise

			raise RuntimeError(
				f"Popcat endpoint `{endpoint}` rejected the avatar/image parameter."
			)
		finally:
			if owns_session:
				await session.close()

	async def _fetch(self, session, endpoint, params):
		url = f"{self.base_url}/v2/{endpoint}"
		async with session.get(url, params=params) as response:
			if response.status != 200:
				message = f"Popcat returned status {response.status}."
				content_type = response.headers.get("content-type", "")
				if "application/json" in content_type:
					try:
						payload = await response.json()
						detail = self._extract_error_detail(payload)
						if detail:
							message = f"Popcat returned status {response.status}: {detail}"
					except Exception:
						pass
				raise RuntimeError(message)

			data = await response.read()
			if not data:
				raise RuntimeError("Popcat returned an empty response.")

			return data

	def _extract_error_detail(self, payload):
		if isinstance(payload, str):
			text = payload.strip()
			return text or None

		if isinstance(payload, dict):
			for key in ("message", "error", "reason", "detail", "details"):
				value = payload.get(key)
				if isinstance(value, str) and value.strip():
					return value.strip()

			parts = []
			for key, value in payload.items():
				if isinstance(value, str) and value.strip():
					parts.append(f"{key}={value.strip()}")
				elif isinstance(value, (int, float)) and not isinstance(value, bool):
					parts.append(f"{key}={value}")

			if parts:
				return ", ".join(parts)

			return None

		if isinstance(payload, list):
			for item in payload:
				if isinstance(item, str) and item.strip():
					return item.strip()

		return None