"""Server MCP di NovaDC.

Un server per sistema, come nella realta': l'MCP Atlassian copre Jira, quello GitHub copre
GitHub. Nessuno distribuisce "github-read" e "github-write" separati.

    /wiki/mcp      wiki aziendale   — sola lettura per natura
    /tickets/mcp   ticketing        — lettura e scrittura

La superficie esposta al modello (nomi dei tool, descrizioni, parametri) e' in inglese, come
l'API del ticketing e per lo stesso motivo: e' cio' che si trova nei sistemi reali.

La distinzione fra diagnosi e intervento non passa da server separati ma da due meccanismi
nativi, che sono quelli veri:

- **tool annotations**: i tool di lettura sono marcati `read_only_hint`, quelli di scrittura
  `destructive_hint`. L'harness puo' decidere cosa approvare automaticamente
- **modalita' sola lettura**: con NOVADC_MCP_READONLY=true il server dei ticket non
  registra affatto i tool di scrittura. E' come funziona l'MCP di GitHub, e in S02 e' la
  dimostrazione che il guardrail sta nella configurazione, non nel prompt

Il token del ticketing vive **qui**, non nella configurazione dell'agent. E' la risposta
concreta alla domanda "perche' un MCP invece di far chiamare l'API direttamente": perche'
cosi' il modello usa una credenziale senza mai vederla.

Copre soltanto wiki e ticketing, e la mancanza e' il punto: log e metriche girano su
OpenSearch e Grafana, prodotti standard che hanno gia' server MCP disponibili, e la cui
lingua di interrogazione (Query DSL, PromQL) il modello conosce gia'. Costruirci sopra un
MCP proprietario sarebbe lavoro sprecato. Si costruisce solo cio' che non esiste: qui il
ticketing e il wiki interni.

In S02 questa e' una decisione da far prendere ai partecipanti, non da raccontare.

I tool sono pochi e grossolani: uno per intenzione, non uno per endpoint. `search_applied_changes` e' quello aggiunto nel LAB 4.2 di S02.
"""

import os
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

WIKI_URL = os.environ.get("WIKI_URL", "http://wiki:8000").rstrip("/")
TICKETS_URL = os.environ.get("TICKETS_URL", "http://tickets:8000").rstrip("/")
TICKETS_API_TOKEN = os.environ.get("TICKETS_API_TOKEN", "novadc-lab-token")

TIMEOUT = httpx.Timeout(30.0)

SOLA_LETTURA = os.environ.get("NOVADC_MCP_READONLY", "").lower() in ("1", "true", "yes")

wiki = MCPServer(
    "novadc-wiki",
    instructions="The NovaDC corporate wiki: runbooks, procedures, post-mortems and "
                 "scattered notes. Read-only. Pages are not always up to date — check the "
                 "last-updated date against recent changes before trusting one.",
)
tickets = MCPServer(
    "novadc-tickets",
    instructions="NovaDC ticketing: incidents, changes and service requests. "
                 "Before changing a ticket status, call available_transitions — an illegal "
                 "transition is rejected."
                 + (" This instance is running in read-only mode." if SOLA_LETTURA else ""),
)

SOLA_LETTURA_ANN = ToolAnnotations(read_only_hint=True, idempotent_hint=True)
SCRITTURA_ANN = ToolAnnotations(read_only_hint=False, destructive_hint=True)


def tool_di_scrittura(server: MCPServer):
    """Registra un tool solo se il server non e' in modalita' sola lettura.

    Non e' un controllo sul prompt: in sola lettura il tool non compare proprio
    nell'elenco, quindi il modello non sa nemmeno che esista.
    """
    def decoratore(fn):
        if SOLA_LETTURA:
            return fn
        return server.tool(annotations=SCRITTURA_ANN)(fn)
    return decoratore


async def _get(url: str, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(url, params=params)
        r.raise_for_status()
        return r.json()


async def _post(url: str, payload: dict, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(url, json=payload, params=params,
                         headers={"Authorization": f"Bearer {TICKETS_API_TOKEN}"})
        if r.status_code >= 400:
            return {"error": r.status_code, "detail": r.json().get("detail", r.text)}
        return r.json()


# --- wiki ---------------------------------------------------------------------

@wiki.tool(annotations=SOLA_LETTURA_ANN)
async def search_wiki(query: str, limit: int = 10) -> list[dict]:
    """Search the NovaDC corporate wiki by keyword.

    Returns title, space, last-updated date and an excerpt. The date matters: the wiki
    contains pages that were never updated after a change, so an old page may describe a
    configuration that no longer exists. Always read the full page with read_page before
    drawing a conclusion.
    """
    return await _get(f"{WIKI_URL}/api/search", {"q": query, "limit": limit})


@wiki.tool(annotations=SOLA_LETTURA_ANN)
async def read_page(slug: str) -> dict:
    """Read one wiki page by slug, with its full text and metadata.

    Get the slug from search_wiki or list_pages.
    """
    return await _get(f"{WIKI_URL}/api/pages/{slug}")


@wiki.tool(annotations=SOLA_LETTURA_ANN)
async def list_pages(space: str | None = None) -> list[dict]:
    """List wiki pages, optionally restricted to one space.

    Spaces: RUN (operations), CHG (change), INFRA (infrastructure), PM (post-mortems),
    PROJ (projects), COMM (commercial), GEN (miscellaneous).
    """
    return await _get(f"{WIKI_URL}/api/pages", {"space": space} if space else None)


# --- ticket (lettura) ---------------------------------------------------------

@tickets.tool(annotations=SOLA_LETTURA_ANN)
async def search_tickets(
    type: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    service: str | None = None,
    host: str | None = None,
    q: str | None = None,
    created_after: str | None = None,
    resolved_after: str | None = None,
    open_only: bool = False,
    limit: int = 25,
) -> dict:
    """Search tickets in NovaDC ticketing.

    type: Incident, Change or Service Request. severity: SEV1..SEV4 (incidents only).
    Dates accept ISO 8601, 'now', or a relative offset such as '-72h' or '-7d'.

    Mind the difference between the two date filters: created_after matches when a ticket
    was RAISED, resolved_after when it was CLOSED. For a change, closed means applied in
    production — and a change is raised days before it is executed.
    """
    params = {k: v for k, v in {
        "type": type, "status": status, "severity": severity, "service": service,
        "host": host, "q": q, "created_after": created_after,
        "resolved_after": resolved_after, "limit": limit,
    }.items() if v is not None}
    if open_only:
        params["open_only"] = "true"
    return await _get(f"{TICKETS_URL}/api/issues", params)


@tickets.tool(annotations=SOLA_LETTURA_ANN)
async def read_ticket(key: str) -> dict:
    """Read a full ticket: fields, comments in chronological order, and links.

    Comments are written by people during the emergency and may contain wrong guesses.
    They are testimony, not conclusions.
    """
    return await _get(f"{TICKETS_URL}/api/issues/{key}")


@tickets.tool(annotations=SOLA_LETTURA_ANN)
async def available_transitions(key: str) -> dict:
    """List the legal status changes for a ticket, given its type and current status.

    Call this before update_ticket: a transition not listed here is rejected.
    """
    return await _get(f"{TICKETS_URL}/api/issues/{key}/transitions")


@tickets.tool(annotations=SOLA_LETTURA_ANN)
async def search_applied_changes(service: str, since: str = "-7d", limit: int = 25) -> dict:
    """Changes APPLIED in production on a service since a date: what actually went live.

    Use this, not search_tickets(created_after=...), to answer "what changed recently".
    A change is raised days before it is executed, so filtering on the creation date misses
    exactly the changes applied inside the window. This tool filters on the closing date,
    which for a change is when it was applied (or rolled back).

    since accepts ISO 8601, 'now', or a relative offset such as '-72h' or '-7d'.
    """
    return await _get(f"{TICKETS_URL}/api/issues", {
        "type": "Change", "service": service, "resolved_after": since, "limit": limit,
    })


@tickets.tool(annotations=SOLA_LETTURA_ANN)
async def ticket_stats(days: int = 30) -> dict:
    """Aggregates over ticketing: counts by type, status, severity and assignee, mean
    time to resolution, and a daily series. Useful for reports and dashboards."""
    return await _get(f"{TICKETS_URL}/api/stats", {"days": days})


# --- ticket (scrittura) -------------------------------------------------------

@tool_di_scrittura(tickets)
async def add_comment(key: str, body: str, author: str = "agent") -> dict:
    """Add a comment to an existing ticket.

    Use it to record evidence and conclusions on the ticket, so they are there for whoever
    picks up the next shift.
    """
    return await _post(f"{TICKETS_URL}/api/issues/{key}/comments",
                       {"author": author, "body": body})


@tool_di_scrittura(tickets)
async def update_ticket(key: str, status: str | None = None, assignee: str | None = None,
                          priority: str | None = None, severity: str | None = None) -> dict:
    """Update a ticket's status, assignee, priority or severity.

    A status change must follow the workflow: call available_transitions before this tool.
    An illegal transition is rejected together with the list of legal targets.
    """
    payload = {k: v for k, v in {"status": status, "assignee": assignee,
                                 "priority": priority, "severity": severity}.items()
               if v is not None}
    if not payload:
        return {"error": 400, "detail": "no fields to update"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.put(f"{TICKETS_URL}/api/issues/{key}", json=payload,
                        headers={"Authorization": f"Bearer {TICKETS_API_TOKEN}"})
        if r.status_code >= 400:
            return {"error": r.status_code, "detail": r.json().get("detail", r.text)}
        return r.json()


@tool_di_scrittura(tickets)
async def create_ticket(summary: str, type: str = "Incident", description: str = "",
                      priority: str = "Medium", severity: str | None = None,
                      risk: str | None = None, reporter: str = "agent",
                      services: list[str] | None = None,
                      hosts: list[str] | None = None,
                      labels: list[str] | None = None) -> dict:
    """Open a new ticket. The key is assigned by the system.

    type: Incident (uses severity), Change (uses risk) or Service Request.

    For a Change the description must carry the execution plan, a verified rollback plan
    and the expected impact: that is what the internal change procedure requires, and a
    change without a rollback does not get approved.
    """
    return await _post(f"{TICKETS_URL}/api/issues", {
        "type": type, "summary": summary, "description": description,
        "priority": priority, "severity": severity, "risk": risk, "reporter": reporter,
        "services": services or [], "hosts": hosts or [], "labels": labels or [],
    })


@tool_di_scrittura(tickets)
async def link_tickets(key: str, to: str, type: str = "relates to") -> dict:
    """Link two tickets. The link is visible from both ends.

    Types: 'caused by', 'causes', 'relates to', 'duplicates', 'blocks', 'resolved by'.
    Typical use: linking an incident to the change that caused it.
    """
    return await _post(f"{TICKETS_URL}/api/issues/{key}/links", {"to": to, "type": type})


# --- applicazione -------------------------------------------------------------

async def healthz(request):
    return JSONResponse({
        "status": "ok",
        "servers": {"wiki": "/wiki/mcp", "tickets": "/tickets/mcp"},
        "read_only": SOLA_LETTURA,
        "tools": {"wiki": len(await wiki.list_tools()),
                  "tickets": len(await tickets.list_tools())},
    })


# host="0.0.0.0": con il default 127.0.0.1 l'SDK attiva la protezione DNS rebinding e
# accetta solo Host localhost, quindi dal tunnel ogni richiesta prende 421.
app_wiki = wiki.streamable_http_app(stateless_http=True, host="0.0.0.0")
app_tickets = tickets.streamable_http_app(stateless_http=True, host="0.0.0.0")


@asynccontextmanager
async def lifespan(_):
    """Avvia i session manager dei due server MCP.

    Starlette non propaga il lifespan alle app montate con Mount: senza questo, ogni
    richiesta fallisce con "Task group is not initialized".
    """
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(wiki.session_manager.run())
        await stack.enter_async_context(tickets.session_manager.run())
        yield


app = Starlette(
    routes=[
        Route("/healthz", healthz),
        Mount("/wiki", app=app_wiki),
        Mount("/tickets", app=app_tickets),
    ],
    lifespan=lifespan,
)
