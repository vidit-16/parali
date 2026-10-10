// Farmer view: one farmer's own field and money, in their language, what the satellite saw, questions by voice
// or text, and an appeal when they think the satellite is wrong. Phone-first.
import { $, $$, esc, icon, rupees, store, initialLang, setupHeader, fmtDate, filmstrip, kindOf, getJSON, ORBIT, countUp, drawEvidenceFrame, toGurmukhi, smokeKg } from "./shared.js";
import { Recorder } from "./voice.js";

// Punjabi (pa) and Haryanvi (hr) are drafts and need a native speaker's review.
const T = {
  en: {
    explore: "Explore", officer: "Officer", farmer: "Farmer",
    signIn: "Sign in", signNote: "Your claim, your money and your field, in your language.", mobile: "Mobile number", cont: "Continue",
    demoPick: "Pick a farmer", demoNote: "No SMS sign-in here: pick a farmer to see their app. Cases reset daily; WhatsApp is shown in the video.", demoTyped: "Pick one of the farmers below.",
    hello: (n) => `Namaste, ${n}`, switch: "Sign out", noClaim: "No claim this season yet.", acres: "acres",
    status: { clean: "Paid in full", burn: "The satellite saw a burn", review: "An officer is looking", wait: "Being checked" },
    smoke: (kg) => `≈ {kg} kg smoke avoided`, smokeNote: "PM2.5, est.", listen: "Listen", money: "Your money", passbook: "Season 2025",
    rows: { adv: "Advance before harvest", noadv: "No advance this year: last season was not clearly clean", bal: "Rest of the money",
      balHeld: "Held until the officer decides", balPaid: "Sent to your bank account", repay: "Advance to return", notpay: "Not payable this season", returned: "Advance returned" },
    pay: (a) => `Return ${a} online`, payNote: "Razorpay test mode: no real money moves.",
    total: (t) => `Full amount for your field: ${rupees(t)}`,
    saw: "What the satellite saw", colour: "Colour", infrared: "Infrared",
    sawBurn: (d) => `On ${d} your field looked burnt: dark in colour, maroon in infrared.`,
    sawClean: (n) => `No burn in ${n} clear pictures this season. The latest is shown.`,
    sawReview: "The pictures are not clear enough to decide. The officer will check.", sawWait: "Pictures appear once the check is done.",
    season: "Your field through the season",
    ask: "Ask anything", askHint: "Hold the mic and speak, or type.", send: "Send", listening: "Listening… let go to send",
    suggest: ["When will my money come?", "Why is my claim held?", "How do I appeal?"],
    thinking: "Thinking", you: "You", appeal: "I did not burn: appeal", appealTitle: "Tell the officer why the satellite is wrong",
    appealHint: "For example: used a happy seeder; the dark patch is wet soil after irrigation.", appealSend: "Send appeal",
    appealed: (d) => `Appeal sent on ${d}. The officer will look before any money is asked back.`, cancel: "Cancel",
    micErr: "The microphone is not available here. Type instead.", err: "Could not reach Saakshi. Try again.",
  },
  hi: {
    explore: "देखें", officer: "अधिकारी", farmer: "किसान",
    signIn: "साइन-इन", signNote: "आपका दावा, आपकी राशि और आपका खेत, आपकी भाषा में।", mobile: "मोबाइल नंबर", cont: "आगे",
    demoPick: "किसान चुनें", demoNote: "यहाँ SMS साइन-इन नहीं है: किसी किसान को चुनकर उनका ऐप देखें। मामले रोज़ नए होते हैं; WhatsApp वीडियो में है।", demoTyped: "नीचे से कोई किसान चुनें।",
    hello: (n) => `नमस्ते, ${n} जी`, switch: "साइन-आउट", noClaim: "इस सीज़न का कोई दावा अभी नहीं।", acres: "एकड़",
    status: { clean: "पूरी राशि मिल गई", burn: "उपग्रह को जलने का निशान दिखा", review: "अधिकारी देख रहे हैं", wait: "जाँच जारी है" },
    smoke: (kg) => `≈ {kg} kg धुआँ बचा`, smokeNote: "PM2.5, est.", listen: "सुनें", money: "आपकी राशि", passbook: "सीज़न 2025",
    rows: { adv: "कटाई से पहले अग्रिम", noadv: "इस साल अग्रिम नहीं: पिछला सीज़न साफ़ नहीं दिखा", bal: "बाकी राशि",
      balHeld: "अधिकारी के फ़ैसले तक रुकी", balPaid: "आपके बैंक खाते में भेजी", repay: "अग्रिम लौटाना होगा", notpay: "इस सीज़न देय नहीं", returned: "अग्रिम लौटा दी" },
    pay: (a) => `${a} ऑनलाइन लौटाएँ`, payNote: "Razorpay टेस्ट मोड: असली पैसा नहीं कटता।",
    total: (t) => `आपके खेत की पूरी राशि: ${rupees(t)}`,
    saw: "उपग्रह ने क्या देखा", colour: "रंगीन", infrared: "इन्फ्रारेड",
    sawBurn: (d) => `${d} को आपका खेत जला हुआ दिखा: रंगीन तस्वीर में काला, इन्फ्रारेड में मैरून।`,
    sawClean: (n) => `इस सीज़न की ${n} साफ़ तस्वीरों में कहीं जलना नहीं। सबसे नई तस्वीर दिखाई गई है।`,
    sawReview: "तस्वीरें फ़ैसले के लिए साफ़ नहीं हैं। अधिकारी देखेंगे।", sawWait: "जाँच पूरी होने पर तस्वीरें दिखेंगी।",
    season: "सीज़न भर आपका खेत",
    ask: "कुछ भी पूछें", askHint: "माइक दबाकर बोलें, या लिखें।", send: "भेजें", listening: "सुन रहे हैं… छोड़ते ही भेजेंगे",
    suggest: ["मेरा पैसा कब आएगा?", "मेरा दावा क्यों रुका है?", "अपील कैसे करूँ?"],
    thinking: "सोच रहे हैं", you: "आप", appeal: "मैंने नहीं जलाया: अपील करें", appealTitle: "अधिकारी को बताइए कि उपग्रह क्यों ग़लत है",
    appealHint: "जैसे: हैप्पी सीडर चलाया था; काला हिस्सा सिंचाई के बाद गीली मिट्टी है।", appealSend: "अपील भेजें",
    appealed: (d) => `${d} को अपील भेजी गई। पैसा वापस माँगने से पहले अधिकारी देखेंगे।`, cancel: "रहने दें",
    micErr: "यहाँ माइक नहीं चल रहा। लिखकर पूछें।", err: "साक्षी से संपर्क नहीं हो पाया। फिर कोशिश करें।",
  },
  pa: {
    explore: "ਵੇਖੋ", officer: "ਅਧਿਕਾਰੀ", farmer: "ਕਿਸਾਨ",
    signIn: "ਸਾਈਨ-ਇਨ", signNote: "ਤੁਹਾਡਾ ਦਾਅਵਾ, ਤੁਹਾਡੀ ਰਕਮ ਅਤੇ ਤੁਹਾਡਾ ਖੇਤ, ਤੁਹਾਡੀ ਭਾਸ਼ਾ ਵਿੱਚ।", mobile: "ਮੋਬਾਈਲ ਨੰਬਰ", cont: "ਅੱਗੇ",
    demoPick: "ਕਿਸਾਨ ਚੁਣੋ", demoNote: "ਇੱਥੇ SMS ਸਾਈਨ-ਇਨ ਨਹੀਂ ਹੈ: ਕਿਸੇ ਕਿਸਾਨ ਨੂੰ ਚੁਣ ਕੇ ਉਨ੍ਹਾਂ ਦੀ ਐਪ ਵੇਖੋ। ਮਾਮਲੇ ਰੋਜ਼ ਨਵੇਂ ਹੁੰਦੇ ਹਨ; WhatsApp ਵੀਡੀਓ ਵਿੱਚ ਹੈ।", demoTyped: "ਹੇਠਾਂ ਤੋਂ ਕੋਈ ਕਿਸਾਨ ਚੁਣੋ।",
    hello: (n) => `ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ${n} ਜੀ`, switch: "ਸਾਈਨ-ਆਊਟ", noClaim: "ਇਸ ਸੀਜ਼ਨ ਦਾ ਕੋਈ ਦਾਅਵਾ ਅਜੇ ਨਹੀਂ।", acres: "ਏਕੜ",
    status: { clean: "ਪੂਰੀ ਰਕਮ ਮਿਲ ਗਈ", burn: "ਸੈਟੇਲਾਈਟ ਨੂੰ ਸਾੜ ਦਾ ਨਿਸ਼ਾਨ ਦਿਸਿਆ", review: "ਅਧਿਕਾਰੀ ਵੇਖ ਰਹੇ ਹਨ", wait: "ਜਾਂਚ ਜਾਰੀ ਹੈ" },
    smoke: (kg) => `≈ {kg} kg ਧੂੰਆਂ ਬਚਿਆ`, smokeNote: "PM2.5, est.", listen: "ਸੁਣੋ", money: "ਤੁਹਾਡੀ ਰਕਮ", passbook: "ਸੀਜ਼ਨ 2025",
    rows: { adv: "ਵਾਢੀ ਤੋਂ ਪਹਿਲਾਂ ਅਗਾਊਂ", noadv: "ਇਸ ਸਾਲ ਅਗਾਊਂ ਨਹੀਂ: ਪਿਛਲਾ ਸੀਜ਼ਨ ਸਾਫ਼ ਨਹੀਂ ਦਿਸਿਆ", bal: "ਬਾਕੀ ਰਕਮ",
      balHeld: "ਅਧਿਕਾਰੀ ਦੇ ਫ਼ੈਸਲੇ ਤੱਕ ਰੁਕੀ", balPaid: "ਤੁਹਾਡੇ ਬੈਂਕ ਖਾਤੇ ਵਿੱਚ ਭੇਜੀ", repay: "ਅਗਾਊਂ ਵਾਪਸ ਕਰਨਾ ਪਵੇਗਾ", notpay: "ਇਸ ਸੀਜ਼ਨ ਦੇਣਯੋਗ ਨਹੀਂ", returned: "ਅਗਾਊਂ ਵਾਪਸ ਕੀਤੀ" },
    pay: (a) => `${a} ਆਨਲਾਈਨ ਵਾਪਸ ਕਰੋ`, payNote: "Razorpay ਟੈਸਟ ਮੋਡ: ਅਸਲ ਪੈਸਾ ਨਹੀਂ ਕੱਟਦਾ।",
    total: (t) => `ਤੁਹਾਡੇ ਖੇਤ ਦੀ ਪੂਰੀ ਰਕਮ: ${rupees(t)}`,
    saw: "ਸੈਟੇਲਾਈਟ ਨੇ ਕੀ ਵੇਖਿਆ", colour: "ਰੰਗੀਨ", infrared: "ਇਨਫ੍ਰਾਰੈੱਡ",
    sawBurn: (d) => `${d} ਨੂੰ ਤੁਹਾਡਾ ਖੇਤ ਸੜਿਆ ਹੋਇਆ ਦਿਸਿਆ: ਰੰਗੀਨ ਤਸਵੀਰ ਵਿੱਚ ਕਾਲਾ, ਇਨਫ੍ਰਾਰੈੱਡ ਵਿੱਚ ਮੈਰੂਨ।`,
    sawClean: (n) => `ਇਸ ਸੀਜ਼ਨ ਦੀਆਂ ${n} ਸਾਫ਼ ਤਸਵੀਰਾਂ ਵਿੱਚ ਕਿਤੇ ਸਾੜ ਨਹੀਂ। ਸਭ ਤੋਂ ਨਵੀਂ ਤਸਵੀਰ ਵਿਖਾਈ ਗਈ ਹੈ।`,
    sawReview: "ਤਸਵੀਰਾਂ ਫ਼ੈਸਲੇ ਲਈ ਸਾਫ਼ ਨਹੀਂ ਹਨ। ਅਧਿਕਾਰੀ ਵੇਖੇਗਾ।", sawWait: "ਜਾਂਚ ਪੂਰੀ ਹੋਣ ਤੇ ਤਸਵੀਰਾਂ ਦਿਸਣਗੀਆਂ।",
    season: "ਸੀਜ਼ਨ ਭਰ ਤੁਹਾਡਾ ਖੇਤ",
    ask: "ਕੁਝ ਵੀ ਪੁੱਛੋ", askHint: "ਮਾਈਕ ਦਬਾ ਕੇ ਬੋਲੋ, ਜਾਂ ਲਿਖੋ।", send: "ਭੇਜੋ", listening: "ਸੁਣ ਰਹੇ ਹਾਂ… ਛੱਡਦੇ ਹੀ ਭੇਜਾਂਗੇ",
    suggest: ["ਮੇਰਾ ਪੈਸਾ ਕਦੋਂ ਆਵੇਗਾ?", "ਮੇਰਾ ਦਾਅਵਾ ਕਿਉਂ ਰੁਕਿਆ ਹੈ?", "ਅਪੀਲ ਕਿਵੇਂ ਕਰਾਂ?"],
    thinking: "ਸੋਚ ਰਹੇ ਹਾਂ", you: "ਤੁਸੀਂ", appeal: "ਮੈਂ ਨਹੀਂ ਸਾੜਿਆ: ਅਪੀਲ ਕਰੋ", appealTitle: "ਅਧਿਕਾਰੀ ਨੂੰ ਦੱਸੋ ਕਿ ਸੈਟੇਲਾਈਟ ਕਿਉਂ ਗਲਤ ਹੈ",
    appealHint: "ਜਿਵੇਂ: ਹੈਪੀ ਸੀਡਰ ਚਲਾਇਆ ਸੀ; ਕਾਲਾ ਹਿੱਸਾ ਸਿੰਚਾਈ ਤੋਂ ਬਾਅਦ ਗਿੱਲੀ ਮਿੱਟੀ ਹੈ।", appealSend: "ਅਪੀਲ ਭੇਜੋ",
    appealed: (d) => `${d} ਨੂੰ ਅਪੀਲ ਭੇਜੀ ਗਈ। ਪੈਸਾ ਵਾਪਸ ਮੰਗਣ ਤੋਂ ਪਹਿਲਾਂ ਅਧਿਕਾਰੀ ਵੇਖੇਗਾ।`, cancel: "ਰਹਿਣ ਦਿਓ",
    micErr: "ਇੱਥੇ ਮਾਈਕ ਨਹੀਂ ਚੱਲ ਰਿਹਾ। ਲਿਖ ਕੇ ਪੁੱਛੋ।", err: "ਸਾਕਸ਼ੀ ਨਾਲ ਸੰਪਰਕ ਨਹੀਂ ਹੋਇਆ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
  },
  hr: {
    explore: "देक्खो", officer: "अफसर", farmer: "किसान",
    signIn: "साइन-इन", signNote: "थारा दावा, थारी रकम अर थारा खेत, थारी बोली म्ह।", mobile: "मोबाइल नंबर", cont: "आग्गै",
    demoPick: "किसान चुणो", demoNote: "उरै SMS साइन-इन कोनी: किसे किसान नै चुण कै उसका ऐप देक्खो। मामले रोज नए होवैं सैं; WhatsApp वीडियो म्ह सै।", demoTyped: "तळै तै कोए किसान चुणो।",
    hello: (n) => `राम राम, ${n} जी`, switch: "साइन-आउट", noClaim: "इस सीज़न का कोए दावा इब्ब तक कोनी।", acres: "किल्ले",
    status: { clean: "पूरी रकम मिलगी", burn: "उपग्रह नै जळण का निसान दिख्या", review: "अफसर देक्खण लाग रे सैं", wait: "जांच चालू सै" },
    smoke: (kg) => `≈ {kg} kg धुम्मा बच्या`, smokeNote: "PM2.5, est.", listen: "सुणो", money: "थारी रकम", passbook: "सीज़न 2025",
    rows: { adv: "कटाई तै पहल्यां एडवांस", noadv: "इस साल एडवांस कोनी: पाछला सीज़न साफ कोनी दिख्या", bal: "बाकी रकम",
      balHeld: "अफसर के फैसले तक रुकी", balPaid: "थारे बैंक खाते म्ह भेज दी", repay: "एडवांस उल्टा देणा पड़ैगा", notpay: "इस सीज़न देण लायक कोनी", returned: "एडवांस उल्टा दे दिया" },
    pay: (a) => `${a} ऑनलाइन उल्टा दो`, payNote: "Razorpay टेस्ट मोड: असली पीसा कोनी कटदा।",
    total: (t) => `थारे खेत की पूरी रकम: ${rupees(t)}`,
    saw: "उपग्रह नै के देख्या", colour: "रंगीन", infrared: "इन्फ्रारेड",
    sawBurn: (d) => `${d} नै थारा खेत जळया होया दिख्या: रंगीन फोटू म्ह काळा, इन्फ्रारेड म्ह मैरून।`,
    sawClean: (n) => `इस सीज़न के ${n} साफ फोटुआं म्ह कितै जळाणा कोनी। सब तै नया फोटू दिखाया सै।`,
    sawReview: "फोटू फैसले खातर साफ कोनी। अफसर देक्खैगा।", sawWait: "जांच पूरी होण पै फोटू दिक्खैंगे।",
    season: "सीज़न भर थारा खेत",
    ask: "कुछ भी पूछो", askHint: "माइक दबा कै बोलो, या लिखो।", send: "भेजो", listening: "सुणण लाग रे सां… छोड्डते ए भेजांगे",
    suggest: ["मेरा पीसा कद आवैगा?", "मेरा दावा क्यूं रुक रया सै?", "अपील क्यूकर करूं?"],
    thinking: "सोच्चण लाग रे सां", you: "थम", appeal: "मन्नै कोनी जळाई: अपील करो", appealTitle: "अफसर नै बताओ उपग्रह क्यूं गलत सै",
    appealHint: "जियां: हैप्पी सीडर चलाया था; काळा हिस्सा सिंचाई पाच्छै गीली माट्टी सै।", appealSend: "अपील भेजो",
    appealed: (d) => `${d} नै अपील भेज दी। पीसा उल्टा मांगण तै पहल्यां अफसर देक्खैगा।`, cancel: "रहण दो",
    micErr: "उरै माइक कोनी चालरा। लिख कै पूछो।", err: "साक्षी तै बात कोनी हो पाई। फेर कोसिस करो।",
  },
};
let lang = initialLang("hi");
const t = () => T[lang];
const S = { fields: [], claims: [], windows: [], me: store.get("saakshi-farmer"), chat: [], recording: null };

function labelText() { $$("[data-t]").forEach((el) => { const v = t()[el.dataset.t]; if (typeof v === "string") el.textContent = v; }); }
// a name in the reader's script: Hindi names shown in Gurmukhi for Punjabi
const local = (en, hi) => (lang === "en" ? en : lang === "pa" && hi ? toGurmukhi(hi) : hi || en);
const msgOf = (m) => (!m ? "" : m[lang] || m.hi);

// ---- sign-in: the real app signs in by mobile number; the demo lets you pick a farmer ----
function renderSignIn() {
  const L = t();
  $("#phone").innerHTML = `<section class="card glass sign"><div class="sign-mark">${ORBIT}</div><h1>${esc(L.signIn)}</h1><p class="cap">${esc(L.signNote)}</p>
      <form class="mobile" id="mobile"><label>${esc(L.mobile)}<span class="tel"><b>+91</b><input inputmode="numeric" maxlength="10" autocomplete="tel-national" placeholder="98XXXXXXXX"></span></label>
        <button class="btn primary wide" type="submit">${esc(L.cont)}</button><p class="cap" id="typed" hidden>${esc(L.demoTyped)}</p></form></section>
    <section class="card glass"><h2>${esc(L.demoPick)}</h2><p class="cap">${esc(L.demoNote)}</p>
      <ul class="who">${S.fields.map((f, i) => `<li style="--i:${i}"><button data-id="${f.id}"><span class="avatar">${esc(local(f.farmer, f.farmer_hi).slice(0, 1))}</span>
        <span><b>${esc(local(f.farmer, f.farmer_hi))}</b><small>${esc(local(f.name, f.name_hi))} · ${esc(local(f.village, f.village_hi))}</small></span></button></li>`).join("")}</ul></section>`;
  $("#mobile").onsubmit = (e) => { e.preventDefault(); $("#typed").hidden = false; };
  $$("#phone [data-id]").forEach((b) => { b.onclick = () => { S.me = b.dataset.id; store.set("saakshi-farmer", S.me); S.chat = []; render(true); }; });
}

function moneyRows(c) {
  const R = t().rows, adv = c.advance || {}, st = c.settlement || {};
  const rows = [];
  rows.push(adv.status === "paid" ? { text: R.adv, amt: adv.amount, sign: "+", cls: "in", when: fmtDate(adv.paid_at, lang) } : { text: R.noadv, amt: null, cls: "" });
  const rest = (st.total || 0) - (adv.status === "paid" ? adv.amount : 0);
  if (st.state === "balance_due") rows.push({ text: `${R.bal}: ${R.balPaid}`, amt: st.balance, sign: "+", cls: "in", when: fmtDate(st.released_at, lang) });
  else if (st.state === "recover_advance" && c.recovery?.status === "paid") rows.push({ text: R.returned, amt: st.recover, sign: "−", cls: "out", when: fmtDate(c.recovery.paid_at, lang) });
  else if (st.state === "recover_advance") rows.push({ text: R.repay, amt: st.recover, sign: "−", cls: "out" });
  else if (st.state === "not_payable") rows.push({ text: `${R.bal}: ${R.notpay}`, amt: null, cls: "" });
  else rows.push({ text: `${R.bal}: ${R.balHeld}`, amt: rest, sign: "", cls: "held" });
  return rows;
}

// the burn date (or the latest clear date) cut from the check's evidence: colour beside infrared
async function renderSaw(c) {
  const L = t(), box = $("#saw");
  if (!box) return;
  const d = c.decision || {}, dates = c.evidence_dates;
  const k = kindOf(d.outcome);
  const line = !c.evidence_url ? L.sawWait : k === "burn" ? L.sawBurn(fmtDate(d.burn_date, lang)) : k === "clean" ? L.sawClean((d.clear_dates || []).length) : L.sawReview;
  if (!c.evidence_url || !dates) { box.innerHTML = `<p class="saw-line">${esc(line)}</p>`; return; }
  const j = d.burn_date && dates.includes(d.burn_date) ? dates.indexOf(d.burn_date) : dates.length - 1;
  box.innerHTML = `<div class="pair"><figure><canvas></canvas><figcaption>${esc(L.colour)} · ${esc(fmtDate(dates[j], lang))}</figcaption></figure>
    <figure><canvas></canvas><figcaption>${esc(L.infrared)}</figcaption></figure></div><p class="saw-line ${k}">${esc(line)}</p>`;
  const img = new Image();
  img.src = c.evidence_url;
  await img.decode().catch(() => {});
  const [a, b] = $$("canvas", box);
  drawEvidenceFrame(a, img, j, dates.length, 0, 96, 96, 3);
  drawEvidenceFrame(b, img, j, dates.length, 1, 96, 96, 3);
}

function render(animate = false) {
  const L = t(), f = S.fields.find((x) => x.id === S.me);
  if (!f) return renderSignIn();
  const c = S.claims.find((x) => x.field_id === f.id);
  const k = c ? kindOf(c.status) : "wait";
  const d = c?.decision || {};
  const bw = d.burn_date ? S.windows.findIndex((w) => w.start <= d.burn_date && d.burn_date <= w.end) : -1;
  const audio = c && ((lang !== "hi" && c[`audio_url_${lang}`]) || c.audio_url);
  const canAppeal = c && ["possible_burn", "needs_review", "officer_confirmed_burnt"].includes(c.status);
  const rows = c ? moneyRows(c) : [];
  $("#phone").innerHTML = `<section class="hello ${animate ? "enter" : ""}"><span class="avatar big">${esc(local(f.farmer, f.farmer_hi).slice(0, 1))}</span>
      <div><h1>${esc(L.hello(local(f.farmer, f.farmer_hi)))}</h1><p class="cap">${esc(local(f.name, f.name_hi))} · ${f.acres} ${esc(L.acres)} · ${esc(local(f.village, f.village_hi))}</p></div>
      <button class="link" id="switch">${esc(L.switch)}</button></section>
    ${c ? `<section class="card glass status-card ${k} ${animate ? "enter" : ""}" style="--i:1"><div class="st-top"><span class="st-ic ${k}">${icon(k === "clean" ? "i-check" : k === "burn" ? "i-flame" : "i-eye")}</span><b>${esc(L.status[k])}</b></div>
        <p class="st-msg">${esc(msgOf(c.message))}</p>
        ${k === "clean" ? `<p class="smoke-chip" title="2.6 t straw an acre, 80% burnt, ~9 kg PM2.5 a tonne">🌫 ${esc(L.smoke(smokeKg(f.acres)))} <small>${esc(L.smokeNote)}</small></p>` : ""}
        ${audio ? `<button class="btn ghost small listen" id="listen">${icon("i-play")}<span>${esc(L.listen)}</span><i class="wave"><i></i><i></i><i></i><i></i><i></i></i></button><audio id="audio" src="${esc(audio)}" preload="none"></audio>` : ""}
        ${c.recovery?.status === "issued" ? `<a class="btn primary wide" href="${esc(c.recovery.url)}">${esc(L.pay(rupees(c.recovery.amount)))}</a><p class="cap">${esc(L.payNote)}</p>` : ""}
        ${c.appeal ? `<p class="cap appealed">${esc(L.appealed(fmtDate(c.appeal.at, lang)))}</p>` : canAppeal ? `<button class="btn ghost wide" id="appeal">${esc(L.appeal)}</button>` : ""}
        <div id="appeal-box"></div></section>
      <section class="card glass ${animate ? "enter" : ""}" style="--i:2"><h2>${esc(L.saw)}</h2><div id="saw"></div></section>
      <section class="card glass passbook ${animate ? "enter" : ""}" style="--i:3"><div class="pb-head"><h2>${esc(L.money)}</h2><small>${esc(L.passbook)}</small></div>
        <ol class="book">${rows.map((r, i) => `<li class="${r.cls}" style="--i:${i}"><span class="tx">${esc(r.text)}${r.when ? `<small>${esc(r.when)}</small>` : ""}</span><b data-amt="${r.amt ?? ""}" data-sign="${r.sign || ""}">${r.amt === null ? "—" : esc((r.sign || "") + rupees(r.amt))}</b></li>`).join("")}</ol>
        <p class="cap">${esc(L.total(c.settlement?.total || 0))}</p></section>`
    : `<section class="card glass"><p>${esc(L.noClaim)}</p></section>`}
    <section class="card glass ${animate ? "enter" : ""}" style="--i:4"><h2>${esc(L.season)}</h2><div id="film"></div></section>
    <section class="card glass ask ${animate ? "enter" : ""}" style="--i:5"><h2>${esc(L.ask)}</h2><p class="cap">${esc(L.askHint)}</p>
      <div class="chat" id="chat"></div>
      <div class="chips">${L.suggest.map((q) => `<button class="chipq">${esc(q)}</button>`).join("")}</div>
      <form class="composer" id="composer"><button type="button" class="mic" id="mic" aria-label="Hold to speak">${micSvg}</button>
        <input id="q" autocomplete="off" placeholder="${esc(L.ask)}…"><button class="btn primary small" type="submit">${esc(L.send)}</button></form>
      <p class="cap" id="mic-note" hidden></p></section>`;
  filmstrip($("#film"), S.windows, f.geometry, lang, bw);
  if (c) renderSaw(c);
  if (animate) $$(".book b[data-amt]").forEach((b) => { const v = Number(b.dataset.amt); if (b.dataset.amt !== "" && v) countUp(b, v, (x) => b.dataset.sign + rupees(x), 900); });
  renderChat();
  watchPay();
  $("#switch").onclick = () => { store.del("saakshi-farmer"); S.me = null; S.chat = []; render(); };
  const au = $("#audio");
  if (au) {
    $("#listen").onclick = () => (au.paused ? au.play() : au.pause());
    au.onplay = () => $("#listen").classList.add("playing");
    au.onpause = au.onended = () => $("#listen").classList.remove("playing");
  }
  $("#appeal")?.addEventListener("click", () => openAppeal(c));
  $$(".chipq").forEach((b) => { b.onclick = () => ask({ text: b.textContent }); });
  $("#composer").onsubmit = (e) => { e.preventDefault(); const q = $("#q").value.trim(); if (q) { $("#q").value = ""; ask({ text: q }); } };
  wireMic();
}
const micSvg = `<svg viewBox="0 0 24 24"><rect x="9" y="3.5" width="6" height="11" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V20.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`;

function renderChat() {
  const L = t();
  $("#chat").innerHTML = S.chat.map((m) => m.me
    ? `<div class="msg me"><small>${esc(L.you)}</small><p>${esc(m.text)}</p></div>`
    : m.pending ? `<div class="msg bot typing" aria-label="${esc(L.thinking)}"><i></i><i></i><i></i></div>`
    : `<div class="msg bot"><p>${esc(m[lang] || m.hi)}</p>${m.audio ? `<button class="link" data-audio="${esc(m.audio)}">${icon("i-play")} ${esc(L.listen)}</button>` : ""}</div>`).join("");
  $$("#chat [data-audio]").forEach((b) => { b.onclick = () => new Audio(b.dataset.audio).play(); });
  const el = $("#chat");
  el.scrollTop = el.scrollHeight;
}
async function ask(payload) {
  const L = t();
  if (payload.text) S.chat.push({ me: true, text: payload.text });
  S.chat.push({ pending: true });
  renderChat();
  try {
    const r = await getJSON("/api/agent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ farmer_id: S.me, lang, ...payload }) });
    S.chat.pop();
    if (r.transcript) S.chat.push({ me: true, text: r.transcript });
    S.chat.push({ hi: r.hi, en: r.en, pa: r.pa, hr: r.hr, audio: r.audio_url });
    renderChat();
    if (r.audio_url) new Audio(r.audio_url).play().catch(() => {});
    if ((r.tools || []).some((x) => x === "contest" || x === "file_claim")) refresh();
  } catch {
    S.chat.pop();
    S.chat.push({ hi: L.err, en: L.err });
    renderChat();
  }
}
function wireMic() {
  const mic = $("#mic"), note = $("#mic-note");
  const start = async (e) => {
    e.preventDefault();
    if (S.recording) return;
    try {
      S.recording = new Recorder();
      await S.recording.start();
      mic.classList.add("on");
      note.textContent = t().listening; note.hidden = false;
    } catch { S.recording = null; note.textContent = t().micErr; note.hidden = false; }
  };
  const end = async () => {
    if (!S.recording) return;
    const rec = S.recording; S.recording = null;
    mic.classList.remove("on"); note.hidden = true;
    const { b64, seconds } = await rec.stop();
    if (seconds > 0.6) ask({ audio_b64: b64 });
  };
  mic.addEventListener("pointerdown", start);
  ["pointerup", "pointerleave", "pointercancel"].forEach((ev) => mic.addEventListener(ev, end));
}
function openAppeal(c) {
  const L = t();
  $("#appeal").hidden = true;
  $("#appeal-box").innerHTML = `<div class="appeal-form"><h3>${esc(L.appealTitle)}</h3><textarea id="appeal-note" rows="3" placeholder="${esc(L.appealHint)}"></textarea>
    <p class="err" id="appeal-err" hidden></p><div class="d-btns"><button class="btn primary" id="appeal-send">${esc(L.appealSend)}</button><button class="btn ghost" id="appeal-cancel">${esc(L.cancel)}</button></div></div>`;
  $("#appeal-cancel").onclick = () => { $("#appeal-box").innerHTML = ""; $("#appeal").hidden = false; };
  $("#appeal-send").onclick = async () => {
    const note = $("#appeal-note").value.trim();
    if (!note) { $("#appeal-note").focus(); return; }
    try {
      await getJSON(`/api/claims/${c.id}/appeal`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ note }) });
      await refresh();
    } catch (e) { $("#appeal-err").textContent = e.message; $("#appeal-err").hidden = false; }
  };
}
async function refresh() { S.claims = await getJSON("/api/claims"); render(); }

// a payment link is open: show the payment as soon as it lands, even if it was paid in another tab or from WhatsApp
let payTimer = null, payN = 0;
function watchPay(now = false) {
  clearTimeout(payTimer);
  const c = S.me && S.claims.find((x) => x.field_id === S.me && x.recovery?.status === "issued");
  if (!c) return;
  payTimer = setTimeout(async () => {
    if (++payN % 3 === 0) await getJSON(`/api/claims/${c.id}/recovery/check`, { method: "POST" }).catch(() => null);
    const claims = await getJSON("/api/claims").catch(() => null);
    if (claims && claims.find((x) => x.id === c.id)?.recovery?.status === "paid") { S.claims = claims; render(); return; }
    watchPay();
  }, now ? 0 : 5000);
}
document.addEventListener("visibilitychange", () => { if (!document.hidden) watchPay(true); });

async function load() {
  const [fields, claims, mf] = await Promise.all([getJSON("/api/fields"), getJSON("/api/claims"), getJSON("/tiles/manifest.json")]);
  S.fields = fields.sort((a, b) => a.farmer.localeCompare(b.farmer)); S.claims = claims; S.windows = mf.windows;
  // back from a Razorpay payment link: ask Razorpay too, in case the return was missed
  const paid = new URLSearchParams(location.search).get("paid");
  if (paid && /^[0-9a-f]{6,32}$/.test(paid)) {
    await getJSON(`/api/claims/${paid}/recovery/check`, { method: "POST" }).catch(() => {});
    S.claims = await getJSON("/api/claims");
  }
  if (paid) history.replaceState(null, "", location.pathname);
  render(true);
}
setupHeader(lang, (l) => { lang = l; labelText(); render(); });
labelText();
load();
