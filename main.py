from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import asyncio, csv, io

from scraper import buscar_no_google_maps

executor = ThreadPoolExecutor(max_workers=3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    executor.shutdown(wait=False)

app = FastAPI(title="Prospecta.AI", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def raiz():
    return FileResponse("index.html")

@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}

@app.get("/buscar", tags=["Scraper"])
async def buscar(
    termo: str = Query(...),
    limite: int = Query(20, ge=1, le=500),
    estado: str = Query(None),
    cidade: str = Query(None),
):
    loop = asyncio.get_event_loop()
    try:
        resultados = await loop.run_in_executor(
            executor, lambda: buscar_no_google_maps(termo, limite, estado, cidade)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"termo": termo, "total": len(resultados), "resultados": resultados}

@app.get("/buscar/csv", tags=["Scraper"])
async def buscar_csv(
    termo: str = Query(...),
    limite: int = Query(20, ge=1, le=500),
    estado: str = Query(None),
    responsavel: str = Query(""),
    campanha: str = Query(""),
    etapa: str = Query("Prospecção"),
    fonte: str = Query("Google Maps"),
):
    loop = asyncio.get_event_loop()
    try:
        resultados = await loop.run_in_executor(
            executor, lambda: buscar_no_google_maps(termo, limite, estado)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "Nome da Oportunidade", "Nome da Organização", "Nome do contato",
        "Telefone do contato", "E-mail do contato", "Fonte da negociação",
        "Campanha", "Segmento do cliente", "Anotação", "Responsável", "Etapa",
    ])
    writer.writeheader()
    for r in resultados:
        writer.writerow({
            "Nome da Oportunidade": r.get("nome", ""),
            "Nome da Organização": r.get("nome", ""),
            "Nome do contato": "",
            "Telefone do contato": r.get("telefone", ""),
            "E-mail do contato": "",
            "Fonte da negociação": fonte,
            "Campanha": campanha,
            "Segmento do cliente": r.get("categoria", ""),
            "Anotação": r.get("endereco", ""),
            "Responsável": responsavel,
            "Etapa": etapa,
        })
    output.seek(0)
    filename = f"leads_{termo.replace(' ', '_')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
