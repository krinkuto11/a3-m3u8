from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import httpx

app = FastAPI(title="Extractor M3U8 Atresplayer")

# La URL de la API original que proporcionaste
API_URL = "https://api.atresplayer.com/player/v1/live/5a6a165a7ed1a834493ebf6a?usp=true&device=desktop&NODRM=true"

@app.get("/obtener-m3u8")
async def obtener_m3u8():
    """
    Hace una llamada a la API de Atresplayer, parsea el JSON 
    y devuelve la URL del M3U8 HLS TS en directo.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Hacemos la petición haciéndonos pasar por un navegador básico
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = await client.get(API_URL, headers=headers)
            response.raise_for_status() # Verifica si hay errores HTTP (404, 500, etc.)
            
            data = response.json()
            
            # Buscamos en 'sourcesLive'
            sources_live = data.get("sourcesLive", [])
            for source in sources_live:
                src = source.get("src", "")
                tipo = source.get("type", "")
                
                # Filtramos para asegurarnos de que es HLS TS y formato Apple MpegURL
                if "hlsts" in src and tipo == "application/vnd.apple.mpegurl":
                    # Opción 1: Devolver un JSON con el enlace
                    return {"m3u8_url": src}
            
            # Si el bucle termina y no encuentra nada
            raise HTTPException(status_code=404, detail="No se encontró el enlace HLS TS en la respuesta")
            
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Error al conectar con la API externa: {exc}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@app.get("/play")
async def reproducir_directamente():
    """
    (Opcional) Esta ruta hace lo mismo, pero en lugar de devolver un JSON, 
    redirige directamente al M3U8. Ideal si quieres poner `http://localhost:8000/play` 
    directamente en VLC o tu reproductor IPTV.
    """
    async with httpx.AsyncClient() as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = await client.get(API_URL, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            for source in data.get("sourcesLive", []):
                src = source.get("src", "")
                if "hlsts" in src and source.get("type") == "application/vnd.apple.mpegurl":
                    # Hacemos una redirección HTTP 302 al M3U8
                    return RedirectResponse(url=src)
                    
            raise HTTPException(status_code=404, detail="No se encontró el enlace HLS TS")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
