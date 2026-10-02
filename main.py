from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import httpx

app = FastAPI(title="Extractor M3U8 Atresplayer")

# Plantilla de la API de Atresplayer; se rellena con el ID de cada canal
API_URL = "https://api.atresplayer.com/player/v1/live/{channel_id}?usp=true&device=desktop&NODRM=true"

# IDs de canal (https://api.atresplayer.com/client/v1/info/channels)
CHANNELS = {
    "antena3": "5a6a165a7ed1a834493ebf6a",
    "lasexta": "5a6a172c7ed1a834493ebf6b",
}
DEFAULT_CHANNEL = "antena3"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


async def fetch_m3u8(channel: str) -> str:
    """
    Llama a la API de Atresplayer para el canal indicado, parsea el JSON
    y devuelve la URL del M3U8 HLS TS en directo.
    """
    channel_id = CHANNELS.get(channel)
    if channel_id is None:
        raise HTTPException(
            status_code=404,
            detail=f"Canal desconocido: {channel}. Disponibles: {', '.join(CHANNELS)}",
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                API_URL.format(channel_id=channel_id), headers=HEADERS
            )
            response.raise_for_status()  # Verifica si hay errores HTTP (404, 500, etc.)
            data = response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Error al conectar con la API externa: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"La API externa respondió {exc.response.status_code}")
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=f"Respuesta no válida de la API externa: {exc}")

    # Filtramos para asegurarnos de que es HLS TS y formato Apple MpegURL
    for source in data.get("sourcesLive", []):
        src = source.get("src", "")
        if "hlsts" in src and source.get("type") == "application/vnd.apple.mpegurl":
            return src

    raise HTTPException(status_code=404, detail="No se encontró el enlace HLS TS en la respuesta")


@app.get("/obtener-m3u8/{channel}")
async def obtener_m3u8(channel: str = DEFAULT_CHANNEL):
    """Devuelve un JSON con el enlace M3U8 del canal (antena3, lasexta)."""
    return {"m3u8_url": await fetch_m3u8(channel)}


@app.get("/play/{channel}")
async def reproducir_directamente(channel: str = DEFAULT_CHANNEL):
    """
    Redirige (302) directamente al M3U8 del canal. Ideal para poner
    `http://localhost:8000/play/lasexta` en VLC o tu reproductor IPTV.
    """
    return RedirectResponse(url=await fetch_m3u8(channel))


# Rutas sin canal: mantienen la compatibilidad y apuntan a Antena 3
@app.get("/obtener-m3u8")
async def obtener_m3u8_default():
    return await obtener_m3u8(DEFAULT_CHANNEL)


@app.get("/play")
async def reproducir_default():
    return await reproducir_directamente(DEFAULT_CHANNEL)
