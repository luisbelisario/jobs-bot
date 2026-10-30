"""
Scraper base — interface comum para todas as fontes de vagas.
Inclui retry automático e timeout para resiliência.
"""
from abc import ABC, abstractmethod
from typing import Optional
import asyncio
import httpx
from config import USER_AGENT, REQUEST_TIMEOUT

# Constantes de retry
MAX_RETRIES = 2
RETRY_DELAY = 2  # segundos entre tentativas
RETRY_STATUSES = {429, 500, 502, 503, 504}  # status que justificam retry


class BaseScraper(ABC):
    """Classe base com cliente HTTP compartilhado."""

    def __init__(self, name: str = "base"):
        self.name = name
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Cliente HTTP lazy com headers padrão."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, url: str, **kwargs) -> httpx.Response:
        """
        GET com retry automático em falhas transitórias.
        Tenta até MAX_RETRIES vezes com backoff.
        """
        client = await self._get_client()
        last_exc = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = await client.get(url, **kwargs)
                if resp.status_code in RETRY_STATUSES and attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * (attempt + 1)
                    print(f"[{self.name}] HTTP {resp.status_code} — retry em {delay}s (tentativa {attempt + 2}/{MAX_RETRIES + 1})")
                    await asyncio.sleep(delay)
                    continue
                resp.raise_for_status()
                return resp
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                last_exc = e
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * (attempt + 1)
                    print(f"[{self.name}] Erro de rede: {e} — retry em {delay}s")
                    await asyncio.sleep(delay)
                else:
                    raise
            except httpx.HTTPStatusError as e:
                if e.response.status_code in RETRY_STATUSES and attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * (attempt + 1)
                    await asyncio.sleep(delay)
                    continue
                raise

        raise last_exc  # type: ignore[misc]

    @abstractmethod
    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        """
        Busca vagas nesta fonte.

        Args:
            skills: Lista de skills do usuário.
            roles: Cargos desejados (separados por vírgula).
            locations: Localizações preferidas.

        Returns:
            Lista de vagas no formato:
            {
                "id": str,
                "title": str,
                "company": str,
                "location": str,
                "url": str,
                "description": str,
                "source": str,
            }
        """
        ...