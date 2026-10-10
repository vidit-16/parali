"""Hindi voice assistant for farmers.

The model's job is narrow: work out what the farmer is asking and call a tool. Tools read the farmer's own
records, file a claim, or log a contest / call-back request. None of them can approve, reject, pay or
penalise. Whenever a tool ran, the reply the farmer hears is composed here from the tool results, not
from the model's own words, so the model cannot announce a decision the system did not make.

Two backends with the same tools:
- ScriptedBackend: keyword intents in Hindi, Hinglish and English. Runs without any model; used for tests,
  the local demo, and as the fallback when Bedrock is unavailable or the daily cap is reached.
- BedrockBackend: Strands Agents SDK on Amazon Bedrock (Nova 2 Lite).
"""
import os
import re
import time
from dataclasses import dataclass, field
from typing import Callable

from parali import service
from parali.messages import advance_text, farmer_text, to_gurmukhi
from parali.store import Store

MODEL_ID = os.environ.get("AGENT_MODEL_ID", "us.amazon.nova-2-lite-v1:0")
DAILY_MODEL_TURNS = int(os.environ.get("AGENT_DAILY_TURNS", "400"))
MODEL_TIMEOUT_S = float(os.environ.get("AGENT_TIMEOUT_S", "15"))


@dataclass
class Context:
    store: Store
    farmer_id: str                     # the field owner the session belongs to
    dispatch: Callable[[str], None]    # start processing a newly filed claim
    effects: list = field(default_factory=list)   # (tool, result) pairs this turn


@dataclass
class Reply:
    hi: str
    en: str
    tools: list
    mode: str                          # "bedrock" | "scripted" | "scripted-fallback"
    note: str = ""
    pa: str = ""                       # set when the reply came from templates; empty for the model's own words
    hr: str = ""                       # Haryanvi, likewise


# ---------- tools: the only things the assistant can do ----------

def _fields(ctx: Context) -> list[dict]:
    return [f for f in ctx.store.list("fields") if f.get("owner", f["id"]) == ctx.farmer_id or f["id"] == ctx.farmer_id]


def _claims(ctx: Context) -> list[dict]:
    ids = {f["id"] for f in _fields(ctx)}
    return [c for c in ctx.store.list("claims") if c["field_id"] in ids]


def tool_my_fields(ctx: Context) -> dict:
    r = {"fields": [{"id": f["id"], "name": f.get("name"), "name_hi": f.get("name_hi"), "acres": f.get("acres")}
                    for f in _fields(ctx)]}
    ctx.effects.append(("my_fields", r))
    return r


def tool_claim_status(ctx: Context) -> dict:
    cs = _claims(ctx)
    r = {"claims": [{"id": c["id"], "field": c.get("field_name"), "status": c["status"],
                     "settlement": c.get("settlement"), "advance": c.get("advance"),
                     "rule": (c.get("decision") or {}).get("rule"), "burn_date": (c.get("decision") or {}).get("burn_date")}
                    for c in cs]}
    ctx.effects.append(("claim_status", {"claims": cs}))
    return r


def tool_advance_status(ctx: Context) -> dict:
    cs = _claims(ctx)
    ctx.effects.append(("advance_status", {"claims": cs}))
    return {"advances": [{"field": c.get("field_name"), **(c.get("advance") or {})} for c in cs]}


def tool_file_claim(ctx: Context) -> dict:
    filed, skipped = [], []
    for f in _fields(ctx):
        try:
            c = service.create_claim(ctx.store, f["id"], *service.season.SEASON)
            ctx.dispatch(c["id"])
            filed.append(c)
        except service.WorkflowError:
            skipped.append(f)
    r = {"filed": filed, "already_filed": skipped}
    ctx.effects.append(("file_claim", r))
    return {"filed": [c["field_name"] for c in filed], "already_filed": [f.get("name") for f in skipped]}


def tool_explain(ctx: Context) -> dict:
    cs = _claims(ctx)
    ctx.effects.append(("explain", {"claims": cs}))
    return {"claims": [{"field": c.get("field_name"), "status": c["status"],
                        "reason": (c.get("decision") or {}).get("reason")} for c in cs]}


def tool_contest(ctx: Context, note: str = "") -> dict:
    done = []
    for c in _claims(ctx):
        c["contest"] = {"note": note[:300], "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        ctx.store.put("claims", c["id"], c)
        ctx.store.add_event(c["id"], {"type": "contest", "by": "farmer", "note": note[:300]})
        done.append(c)
    ctx.effects.append(("contest", {"claims": done}))
    return {"contested": [c["field_name"] for c in done]}


def tool_request_callback(ctx: Context) -> dict:
    done = []
    for c in _claims(ctx):
        ctx.store.add_event(c["id"], {"type": "callback_requested", "by": "farmer"})
        done.append(c)
    ctx.effects.append(("callback", {"claims": done}))
    return {"requested_for": [c["field_name"] for c in done]}


TOOLS = {
    "my_fields": tool_my_fields,
    "claim_status": tool_claim_status,
    "advance_status": tool_advance_status,
    "file_claim": tool_file_claim,
    "explain": tool_explain,
    "contest": tool_contest,
    "request_callback": tool_request_callback,
}


# ---------- what the farmer hears: composed from tool results ----------

def _join(parts):
    return " ".join(p for p in parts if p).strip()


def _pa(hi_name, name):
    return to_gurmukhi(hi_name) if hi_name else name


def compose(effects: list) -> tuple[str, str, str, str]:
    """(hi, en, pa, hr) for what the tools did this turn. Haryanvi is a draft for native review."""
    hi, en, pa, hr = [], [], [], []

    def say(h, e, p, r):
        hi.append(h)
        en.append(e)
        pa.append(p)
        hr.append(r)

    for name, r in effects:
        if name == "my_fields":
            if r["fields"]:
                names_hi = ", ".join(f.get("name_hi") or f.get("name") for f in r["fields"])
                say(f"आपके नाम पर ये खेत दर्ज हैं: {names_hi}।",
                    f"Your registered fields: {', '.join(f.get('name') for f in r['fields'])}.",
                    f"ਤੁਹਾਡੇ ਨਾਮ ਉੱਤੇ ਇਹ ਖੇਤ ਦਰਜ ਹਨ: {', '.join(_pa(f.get('name_hi'), f.get('name')) for f in r['fields'])}।",
                    f"थारे नाम पै ये खेत दर्ज सैं: {names_hi}।")
            else:
                say("आपके नाम पर कोई खेत दर्ज नहीं मिला।", "No field is registered in your name.",
                    "ਤੁਹਾਡੇ ਨਾਮ ਉੱਤੇ ਕੋਈ ਖੇਤ ਦਰਜ ਨਹੀਂ ਮਿਲਿਆ।", "थारे नाम पै कोए खेत दर्ज कोनी मिल्या।")
        elif name in ("claim_status", "explain"):
            if not r["claims"]:
                say("अभी आपका कोई दावा दर्ज नहीं है। कहें तो मैं दावा दर्ज कर दूँ।",
                    "You have no claim yet. I can file one if you want.",
                    "ਹਾਲੇ ਤੁਹਾਡਾ ਕੋਈ ਦਾਅਵਾ ਦਰਜ ਨਹੀਂ ਹੈ। ਕਹੋ ਤਾਂ ਮੈਂ ਦਾਅਵਾ ਦਰਜ ਕਰ ਦਿਆਂ।",
                    "इब्ब तक थारा कोए दावा दर्ज कोनी। कहो तो मैं दावा दर्ज कर द्यूं।")
            for c in r["claims"]:
                t = farmer_text(c)
                say(t["hi"], t["en"], t["pa"], t["hr"])
        elif name == "advance_status":
            if not r["claims"]:
                say("अग्रिम राशि की जाँच दावा दर्ज होने पर होती है।", "The advance is checked when a claim is filed.",
                    "ਅਗਾਊਂ ਰਕਮ ਦੀ ਜਾਂਚ ਦਾਅਵਾ ਦਰਜ ਹੋਣ ਉੱਤੇ ਹੁੰਦੀ ਹੈ।", "एडवांस की जांच दावा दर्ज होण पै होवै सै।")
            for c in r["claims"]:
                t = advance_text(c)
                say(t["hi"], t["en"], t["pa"], t["hr"])
        elif name == "file_claim":
            for c in r["filed"]:
                fh = c.get("field_name_hi") or c["field_name"]
                say(f"{fh} खेत का दावा दर्ज हो गया। पिछले और इस सीज़न की "
                    "उपग्रह तस्वीरें जाँची जा रही हैं, नतीजा कुछ ही देर में मिलेगा।",
                    f"Claim filed for {c['field_name']}. Last season's and this season's satellite images are "
                    "being checked; the result will be ready shortly.",
                    f"{_pa(c.get('field_name_hi'), c['field_name'])} ਖੇਤ ਦਾ ਦਾਅਵਾ ਦਰਜ ਹੋ ਗਿਆ। ਪਿਛਲੇ ਅਤੇ ਇਸ ਸੀਜ਼ਨ ਦੀਆਂ "
                    "ਸੈਟੇਲਾਈਟ ਤਸਵੀਰਾਂ ਦੀ ਜਾਂਚ ਹੋ ਰਹੀ ਹੈ, ਨਤੀਜਾ ਕੁਝ ਹੀ ਦੇਰ ਵਿੱਚ ਮਿਲੇਗਾ।",
                    f"{fh} खेत का दावा दर्ज हो गया। पाछले अर इस सीज़न के उपग्रह फोटुआं की जांच होरी सै, नतीजा थोड़ी देर म्ह मिलैगा।")
            for f in r["already_filed"]:
                fh = f.get("name_hi") or f.get("name")
                say(f"{fh} खेत का दावा पहले से दर्ज है।",
                    f"A claim for {f.get('name')} is already filed.",
                    f"{_pa(f.get('name_hi'), f.get('name'))} ਖੇਤ ਦਾ ਦਾਅਵਾ ਪਹਿਲਾਂ ਹੀ ਦਰਜ ਹੈ।",
                    f"{fh} खेत का दावा पहल्यां तै दर्ज सै।")
        elif name == "contest":
            if r["claims"]:
                say("आपकी आपत्ति दर्ज कर ली गई है और उपग्रह तस्वीरों के साथ ग्राम अधिकारी को भेज दी गई है।",
                    "Your objection is recorded and sent to the village officer with the satellite images.",
                    "ਤੁਹਾਡਾ ਇਤਰਾਜ਼ ਦਰਜ ਕਰ ਲਿਆ ਗਿਆ ਹੈ ਅਤੇ ਸੈਟੇਲਾਈਟ ਤਸਵੀਰਾਂ ਸਮੇਤ ਪਿੰਡ ਦੇ ਅਧਿਕਾਰੀ ਨੂੰ ਭੇਜ ਦਿੱਤਾ ਗਿਆ ਹੈ।",
                    "थारी आपत्ति दर्ज कर ली गई सै अर उपग्रह के फोटुआं गेल्यां गाम के अफसर कनै भेज दी सै।")
            else:
                say("आपत्ति दर्ज करने के लिए पहले दावा होना चाहिए।", "A claim is needed before an objection can be recorded.",
                    "ਇਤਰਾਜ਼ ਦਰਜ ਕਰਨ ਲਈ ਪਹਿਲਾਂ ਦਾਅਵਾ ਹੋਣਾ ਚਾਹੀਦਾ ਹੈ।", "आपत्ति दर्ज करण खातर पहल्यां दावा होणा चाहिए।")
        elif name == "callback":
            if r["claims"]:
                say("ग्राम अधिकारी को आपको फ़ोन करने के लिए कह दिया गया है।", "The village officer has been asked to call you.",
                    "ਪਿੰਡ ਦੇ ਅਧਿਕਾਰੀ ਨੂੰ ਤੁਹਾਨੂੰ ਫ਼ੋਨ ਕਰਨ ਲਈ ਕਹਿ ਦਿੱਤਾ ਗਿਆ ਹੈ।", "गाम के अफसर नै थारे तै फोन करण खातर कह दिया सै।")
            else:
                say("पहले दावा दर्ज करना होगा।", "A claim is needed first.", "ਪਹਿਲਾਂ ਦਾਅਵਾ ਦਰਜ ਕਰਨਾ ਪਵੇਗਾ।", "पहल्यां दावा दर्ज करणा पड़ैगा।")
    return _join(hi), _join(en), _join(pa), _join(hr)


HELP = ("मैं आपके खेत की पराली जाँच के बारे में बता सकती हूँ: दावा दर्ज करना, दावे की स्थिति, अग्रिम राशि, "
        "फ़ैसले का कारण, या गलत फ़ैसले पर आपत्ति। बोलिए, क्या जानना है?",
        "I can file your no-burn claim, tell you its status, the advance, why it was decided, or record an "
        "objection. What would you like?",
        "ਮੈਂ ਤੁਹਾਡੇ ਖੇਤ ਦੀ ਪਰਾਲੀ ਜਾਂਚ ਬਾਰੇ ਦੱਸ ਸਕਦੀ ਹਾਂ: ਦਾਅਵਾ ਦਰਜ ਕਰਨਾ, ਦਾਅਵੇ ਦੀ ਸਥਿਤੀ, ਅਗਾਊਂ ਰਕਮ, "
        "ਫ਼ੈਸਲੇ ਦਾ ਕਾਰਨ, ਜਾਂ ਗ਼ਲਤ ਫ਼ੈਸਲੇ ਉੱਤੇ ਇਤਰਾਜ਼। ਦੱਸੋ, ਕੀ ਜਾਣਨਾ ਹੈ?",
        "मैं थारे खेत की पराळी जांच के बारे म्ह बता सकूं सूं: दावा दर्ज करणा, दावे की हालत, एडवांस, फैसले का कारण, "
        "या गलत फैसले पै आपत्ति। बोलो, के जाणणा सै?")


def _help(mode, tools=(), note=""):
    return Reply(HELP[0], HELP[1], list(tools), mode, note=note, pa=HELP[2], hr=HELP[3])


def _from_effects(effects, mode, note=""):
    hi, en, pa, hr = compose(effects)
    return Reply(hi, en, [n for n, _ in effects], mode, note=note, pa=pa, hr=hr)


# ---------- scripted backend ----------

INTENTS = [
    ("contest", r"गलत|आपत्ति|रेड\s*एंट्री|red\s*entry|wrong|appeal|objection|galat|aapatti|ਗ਼?ਲਤ|ਗ਼ਲਤ|ਇਤਰਾਜ਼?|कोनी जळाई"),
    ("request_callback", r"फ़?फोन|कॉल|call\s*me|बात\s*कर|अधिकारी\s*से|officer|ਫ਼?ਫੋਨ|ਫ਼ੋਨ|ਕਾਲ|ਅਧਿਕਾਰੀ\s*ਨਾਲ"),
    ("advance_status", r"अग्रिम|एडवांस|advance|pehle\s*paise|पहले\s*पैसे|ਅਗਾਊਂ|ਐਡਵਾਂਸ|ਪਹਿਲਾਂ\s*ਪੈਸੇ"),
    ("explain", r"क्यों|कारण|why|\bheld\b|reason|kyun|kyon|ਕਿਉਂ|ਕਾਰਨ|क्यूं"),
    ("file_claim", r"दर्ज|आवेदन|अप्लाई|apply|file|register|दावा\s*कर|claim\s*kar|ਦਰਜ|ਅਪਲਾਈ|ਦਾਅਵਾ\s*ਕਰ"),
    ("claim_status", r"दावा|स्थिति|स्टेटस|status|क्या\s*हुआ|कहाँ\s*तक|पैसे|राशि|payment|money|paid|\bwhen\b|paisa|kab\s*milega|claim|ਦਾਅਵ|ਸਥਿਤੀ|ਸਟੇਟਸ|ਕੀ\s*ਹੋਇਆ|ਪੈਸੇ|ਰਕਮ|ਕਦੋਂ\s*ਮਿਲ|पीसा|कद\s*आवैगा|के\s*होया"),
    ("my_fields", r"मेरे\s*खेत|कौन\s*से\s*खेत|\bfields?\b|my\s*land|khet|ਮੇਰੇ\s*ਖੇਤ|ਕਿਹੜੇ\s*ਖੇਤ"),
]


def scripted_intents(text: str) -> list[str]:
    t = text.lower()
    hits = [name for name, pat in INTENTS if re.search(pat, t)]
    # "file" and "status" both match "दावा"; filing wins only if a filing word is present
    if "file_claim" in hits and "claim_status" in hits:
        hits.remove("claim_status")
    return hits[:2]


class ScriptedBackend:
    mode = "scripted"

    def respond(self, ctx: Context, text: str, history: list) -> Reply:
        intents = scripted_intents(text)
        for name in intents:
            if name == "contest":
                TOOLS[name](ctx, note=text)
            else:
                TOOLS[name](ctx)
        if not ctx.effects:
            return _help(self.mode)
        return _from_effects(ctx.effects, self.mode)


# ---------- Bedrock backend (Strands Agents SDK) ----------

SYSTEM = """You are the assistant inside Saakshi, a Punjab and Haryana government-style app that verifies farmers'
no-burn (crop residue) incentive claims with satellite images. The user is a farmer, usually speaking Hindi
or Hinglish, sometimes Punjabi.

Your only job is to understand what the farmer wants and call the right tool:
- claim_status: status of their claim / payment / what happened
- advance_status: whether they get the advance before harvest, and why
- file_claim: they want to file / apply for the no-burn incentive
- explain: why the decision was made
- contest: they say the decision or a fire alert is wrong, or mention a red entry
- request_callback: they want the officer to call
- my_fields: which fields are registered to them

Rules:
- You cannot approve, reject, pay or penalise anything, and must never say a claim is approved, rejected or
  burnt unless a tool result says so. Decisions are made by fixed rules and the village officer.
- If the request is unclear, ask one short question in simple Hindi.
- Never ask for bank details, Aadhaar, OTPs or passwords.
- Keep any text you write to one or two short sentences in Hindi."""


class BedrockBackend:
    mode = "bedrock"

    def __init__(self, model_id: str = MODEL_ID, region: str | None = None):
        self.model_id = model_id
        self.region = region or os.environ.get("AWS_REGION", "us-west-2")

    def _agent(self, ctx: Context, history: list):
        from strands import Agent, tool
        from strands.models import BedrockModel

        @tool
        def claim_status() -> dict:
            """Status of the farmer's no-burn claim and payment."""
            return tool_claim_status(ctx)

        @tool
        def advance_status() -> dict:
            """Whether the farmer gets the 50% advance before harvest, and why."""
            return tool_advance_status(ctx)

        @tool
        def file_claim() -> dict:
            """File the no-burn incentive claim for the farmer's registered fields."""
            return tool_file_claim(ctx)

        @tool
        def explain() -> dict:
            """Why the satellite check decided what it did."""
            return tool_explain(ctx)

        @tool
        def contest(note: str = "") -> dict:
            """Record the farmer's objection to a decision or a fire alert / red entry.

            Args:
                note: the farmer's own words about why it is wrong.
            """
            return tool_contest(ctx, note)

        @tool
        def request_callback() -> dict:
            """Ask the village officer to phone the farmer."""
            return tool_request_callback(ctx)

        @tool
        def my_fields() -> dict:
            """The fields registered to this farmer."""
            return tool_my_fields(ctx)

        from botocore.config import Config
        try:
            from strands import ModelRetryStrategy
        except ImportError:
            from strands.event_loop._retry import ModelRetryStrategy

        # Fail fast: a farmer waiting on a phone gets the rule-based answer instead of a minute of backoff.
        model = BedrockModel(model_id=self.model_id, region_name=self.region, temperature=0.0, max_tokens=300,
                             boto_client_config=Config(retries={"max_attempts": 1}, connect_timeout=3, read_timeout=12))
        return Agent(model=model, system_prompt=SYSTEM, messages=list(history),
                     tools=[claim_status, advance_status, file_claim, explain, contest, request_callback, my_fields],
                     callback_handler=None, retry_strategy=ModelRetryStrategy(max_attempts=1))

    def respond(self, ctx: Context, text: str, history: list) -> Reply:
        result = self._agent(ctx, history)(text)
        tools = [n for n, _ in ctx.effects]
        if ctx.effects:
            return _from_effects(ctx.effects, self.mode)
        said = str(result).strip()
        if DECISION_WORDS.search(said):   # the model tried to state a decision without a tool result
            return _help(self.mode, tools, note="model reply dropped: stated a decision")
        return Reply(said[:400], "", tools, self.mode)


DECISION_WORDS = re.compile(r"स्वीकृत|मंज़ूर|मंजूर|अस्वीकृत|खारिज|approved|rejected|जलाई\s*गई|burnt|पास\s*हो", re.I)


# ---------- entry point ----------

def respond(store: Store, farmer_id: str, text: str, dispatch: Callable[[str], None],
            backend=None, history: list | None = None) -> Reply:
    text = (text or "").strip()[:500]
    if not text:
        return _help("scripted")
    backend = backend or ScriptedBackend()
    ctx = Context(store, farmer_id, dispatch)
    if isinstance(backend, BedrockBackend):
        if not _take_model_turn(store):
            r = ScriptedBackend().respond(ctx, text, [])
            r.mode, r.note = "scripted-fallback", "daily model limit reached"
            return r
        from concurrent.futures import ThreadPoolExecutor
        from concurrent.futures import TimeoutError as Timeout
        pool = ThreadPoolExecutor(1)
        try:
            return pool.submit(backend.respond, ctx, text, history or []).result(timeout=MODEL_TIMEOUT_S)
        except Exception as e:  # model unavailable or slow: the farmer still gets an answer, and the mode says so
            if ctx.effects:  # a tool already ran: answer from what it did, never run it twice
                return _from_effects(list(ctx.effects), "bedrock", note="model did not finish its reply")
            fresh = Context(store, farmer_id, dispatch)
            r = ScriptedBackend().respond(fresh, text, [])
            r.mode = "scripted-fallback"
            r.note = "model too slow" if isinstance(e, Timeout) else f"model unavailable: {type(e).__name__}"
            return r
        finally:
            pool.shutdown(wait=False)
    return backend.respond(ctx, text, history or [])


def _take_model_turn(store: Store) -> bool:
    day = time.strftime("%Y%m%d", time.gmtime())
    rec = store.get("usage", day) or {"model_turns": 0}
    if rec["model_turns"] >= DAILY_MODEL_TURNS:
        return False
    rec["model_turns"] += 1
    store.put("usage", day, rec)
    return True
