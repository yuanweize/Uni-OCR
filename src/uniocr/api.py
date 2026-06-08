"""UniOCR FastAPI service — production-ready REST API.

Start with::

    uniocr serve --port 8000

Or directly::

    uvicorn uniocr.api:app --host 0.0.0.0 --port 8000 --workers 4
"""

import logging
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import UniOCR, list_available_engines
from .models import Document

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="UniOCR API",
    description=(
        "Unified multilingual OCR service.\n\n"
        "Upload images or PDFs and receive structured text, Markdown, "
        "and layout blocks in a single JSON response."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Engine pool — one instance per engine name, created on first request
# ---------------------------------------------------------------------------

_ocr_pool: Dict[str, UniOCR] = {}


def _get_ocr(engine: str = "auto") -> UniOCR:
    if engine not in _ocr_pool:
        logger.info("Initialising OCR engine pool entry: %s", engine)
        _ocr_pool[engine] = UniOCR(engine=engine)
    return _ocr_pool[engine]


def _build_response(doc: Document, elapsed: float) -> Dict[str, Any]:
    """Build a standardised API response envelope."""
    result = doc.to_dict()
    result["elapsed_seconds"] = elapsed
    result["request_id"] = str(uuid.uuid4())
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Health / readiness probe."""
    return {
        "status": "ok",
        "version": app.version,
        "engines": list_available_engines(),
    }


@app.get("/engines", tags=["System"])
async def engines() -> Dict[str, Any]:
    """List OCR engines available in the current environment."""
    return {"available_engines": list_available_engines()}


@app.post("/extract", tags=["OCR"])
async def extract_file(
    file: UploadFile = File(..., description="Image or PDF file to process"),
    engine: str = Form("auto", description="Engine: auto | paddle | apple"),
) -> JSONResponse:
    """Extract text and layout from an uploaded file."""
    start = time.monotonic()

    suffix = Path(file.filename or "upload").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        ocr = _get_ocr(engine)
        doc = ocr.extract(tmp_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during extraction")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)

    elapsed = round(time.monotonic() - start, 3)
    return JSONResponse(content=_build_response(doc, elapsed))


@app.post("/extract/url", tags=["OCR"])
async def extract_url(
    url: str = Form(..., description="Public URL of an image or PDF"),
    engine: str = Form("auto", description="Engine: auto | paddle | apple"),
) -> JSONResponse:
    """Extract text and layout from a URL pointing to an image or PDF."""
    start = time.monotonic()

    try:
        ocr = _get_ocr(engine)
        doc = ocr.extract(url)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during extraction")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")

    elapsed = round(time.monotonic() - start, 3)
    return JSONResponse(content=_build_response(doc, elapsed))


@app.post("/extract/batch", tags=["OCR"])
async def extract_batch(
    files: List[UploadFile] = File(..., description="Multiple files to process"),
    engine: str = Form("auto"),
) -> JSONResponse:
    """Process multiple files in one request (sequential)."""
    start = time.monotonic()
    ocr = _get_ocr(engine)
    results: List[Dict[str, Any]] = []

    for file in files:
        suffix = Path(file.filename or "upload").suffix or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            if not content:
                results.append({"filename": file.filename, "error": "Empty file"})
                continue
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            doc = ocr.extract(tmp_path)
            item = doc.to_dict()
            item["filename"] = file.filename
            results.append(item)
        except Exception as exc:
            logger.warning("Error processing %s: %s", file.filename, exc)
            results.append({"filename": file.filename, "error": str(exc)})
        finally:
            tmp_path.unlink(missing_ok=True)

    elapsed = round(time.monotonic() - start, 3)
    return JSONResponse(
        content={
            "request_id": str(uuid.uuid4()),
            "file_count": len(files),
            "results": results,
            "elapsed_seconds": elapsed,
        }
    )
