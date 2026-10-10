// Saakshi explorer: the season over the Patiala-Kaithal border belt, from our own Sentinel-2 tiles.
// Burn patches are burn-like ground seen by the satellite; decisions on fields come from the rules and an officer.
// This is the public view: fields carry their killa number, never the farmer's name or money.

// ?frames=timer: drive animation frames from a timer, for headless screenshots where the tab is hidden
const params = new URLSearchParams(location.search);
if (params.get("frames") === "timer") {
  window.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16);
  window.cancelAnimationFrame = (id) => clearTimeout(id);
}

const T = {
  // Punjabi (pa) and Haryanvi (hr) are drafts and need a native speaker's review.
  en: {
    loading: "Loading the season from orbit", explore: "Explore", officer: "Officer", farmer: "Farmer",
    caption: "Every November, Delhi's air turns hazardous.<small>Part of that smoke is straw burnt in the fields of Punjab and Haryana. Saakshi follows one belt of those fields, on the Patiala–Kaithal border, through the 2025 season.</small>",
    delhi: "Delhi", seasonLbl: "2025 season", skip: "Skip", km: (n) => `${n} km from the belt`, study: "Study area · Patran, Punjab",
    kicker: "Patiala–Kaithal border belt · kharif 2025",
    headline: "<em>9 in 10</em> hectares that looked burnt got no fire alert.",
    alerts: "Fire alerts", vslbl: "Clean fields wrongly flagged (lower is better)", vscap: "593 labelled fields in Punjab and Haryana, 111 of them burnt",
    play: "Play the season", explorebtn: "Explore the map",
    fine: "Burn-like: ground that turned near-black right after its plant signal collapsed, seen by Sentinel-2.",
    l_burns: "Burns", l_fires: "Fire alerts", l_fields: "Fields", l_missed: "Only burns no alert caught", ha: "ha burn-like", fa: "fire alerts",
    stages: ["Standing paddy", "Harvest begins", "Harvest", "Stubble", "Peak burning", "Burning tails off", "Wheat sowing", "Wheat up"],
    toast: "Tap a dot to open a field", refphoto: "Close-up photo: Esri, not taken this season",
    v: { clean: "Clean", review: "With the officer", burn: "Possible burn" },
    vline: { clean: (n) => `No burn in any of ${n} clear images`, burn: (d) => `Burn signature on ${d}`, review: () => "Unclear: the officer looks at it" },
    signal: "Plant signal through the season", signalNote: "A burn drops it below zero overnight.",
    clear: "Clear images", nearest: "Fire alerts within 375 m", smoke: { burn: "PM2.5 released, est.", clean: "PM2.5 kept out of the air, est.", review: "PM2.5 if burnt, est." }, none: "none", last: "Last season (2024)",
    checked: (d) => `Result saved from the live check on ${d}`, again: "Run the live check", check: "Run the satellite check",
    steps: ["Finding every clear image", "Removing clouds", "Comparing dates", "Checking fire alerts"],
    acres: "acres", err: "The check did not finish. Try again.",
    live: "CHECKING", checking: "Satellite check in progress", slow: "taking longer than usual",
    stage: { queued: "Starting", current: "Reading this season's clear images, September to December", previous: "Reading last season, for the advance" },
    imagesFound: (n) => `${n} clear images this season`, pause: "Pause", resume: "Resume", exit: "Exit",
    storySteps: (f) => ["The 2025 season over the border belt", "Into Patran, where most fields burned in early November", `${f}: run the satellite check`, `Check complete for ${f}`],
    colour: "Colour", infrared: "Infrared", irNote: "Burnt ground shows maroon, wet soil dark blue.", irWait: "Infrared frames appear once the check has run.", preparing: "Preparing the season", pm: "tonnes PM2.5", sources: "Sources",
    saved: (d) => `The check is not responding right now. Showing its result from ${d}.`, liveNow: (n) => `Checked just now · ${n} s`, rerun: "Check again",
    reading: "Reading every clear image of this field, September to December", checkNote: "Reads every clear Sentinel-2 image of this field, this season and last: the same evidence an officer reviews. About 20 seconds.",
  },
  hi: {
    loading: "उपग्रह से सीज़न ला रहे हैं", explore: "देखें", officer: "अधिकारी", farmer: "किसान",
    caption: "हर नवंबर दिल्ली की हवा ख़तरनाक हो जाती है।<small>उस धुएँ का एक हिस्सा पंजाब और हरियाणा के खेतों में जली पराली है। साक्षी पटियाला–कैथल सीमा के ऐसे ही खेतों को 2025 के पूरे सीज़न में देखता है।</small>",
    delhi: "दिल्ली", seasonLbl: "2025 सीज़न", skip: "छोड़ें", km: (n) => `क्षेत्र से ${n} किमी`, study: "अध्ययन क्षेत्र · पातड़ां, पंजाब",
    kicker: "पटियाला–कैथल सीमा क्षेत्र · खरीफ़ 2025",
    headline: "जले दिखने वाले हर <em>10 में से 9</em> हेक्टेयर पर आग का कोई अलर्ट नहीं आया।",
    alerts: "आग अलर्ट", vslbl: "साफ़ खेत जिन्हें गलती से संदिग्ध बताया (कम बेहतर)", vscap: "पंजाब और हरियाणा के 593 लेबल किए खेत, जिनमें 111 जले",
    play: "पूरा सीज़न देखें", explorebtn: "नक्शा देखें",
    fine: "जले जैसा: वह ज़मीन जो पौधों का संकेत गिरते ही लगभग काली हो गई, Sentinel-2 उपग्रह से देखी गई।",
    l_burns: "जले खेत", l_fires: "आग अलर्ट", l_fields: "खेत", l_missed: "केवल वे जले खेत जिन पर अलर्ट नहीं आया", ha: "हेक्टेयर जले जैसे", fa: "आग अलर्ट",
    stages: ["खड़ा धान", "कटाई शुरू", "कटाई", "पराली", "सबसे ज़्यादा जलना", "जलना घटा", "गेहूँ बुआई", "गेहूँ उगा"],
    toast: "खेत खोलने के लिए बिंदु पर टैप करें", refphoto: "नज़दीकी फ़ोटो: Esri, इस सीज़न की नहीं",
    v: { clean: "साफ़", review: "अधिकारी के पास", burn: "जलने की आशंका" },
    vline: { clean: (n) => `${n} साफ़ तस्वीरों में कहीं जलना नहीं`, burn: (d) => `${d} को जलने का निशान`, review: () => "साफ़ नहीं: अधिकारी देखेंगे" },
    signal: "सीज़न भर पौधों का संकेत", signalNote: "जलने पर यह एक रात में शून्य से नीचे गिरता है।",
    clear: "साफ़ तस्वीरें", nearest: "375 मीटर में आग अलर्ट", smoke: { burn: "निकला PM2.5, अनुमान", clean: "हवा में जाने से बचा PM2.5, अनुमान", review: "जलने पर PM2.5, अनुमान" }, none: "कोई नहीं", last: "पिछला सीज़न (2024)",
    checked: (d) => `${d} की लाइव जाँच का नतीजा`, again: "लाइव जाँच चलाएँ", check: "उपग्रह जाँच चलाएँ",
    steps: ["हर साफ़ तस्वीर ढूँढ रहे हैं", "बादल हटा रहे हैं", "तारीखें मिला रहे हैं", "आग अलर्ट जाँच रहे हैं"],
    acres: "एकड़", err: "जाँच पूरी नहीं हुई। फिर कोशिश करें।",
    live: "जाँच", checking: "उपग्रह जाँच चल रही है", slow: "सामान्य से ज़्यादा समय लग रहा है",
    stage: { queued: "शुरू हो रही है", current: "इस सीज़न की साफ़ तस्वीरें पढ़ रहे हैं, सितंबर से दिसंबर", previous: "अग्रिम के लिए पिछला सीज़न पढ़ रहे हैं" },
    imagesFound: (n) => `इस सीज़न की ${n} साफ़ तस्वीरें`, pause: "रोकें", resume: "जारी रखें", exit: "बंद करें",
    storySteps: (f) => ["सीमा क्षेत्र पर 2025 का सीज़न", "पातड़ां की ओर, जहाँ नवंबर की शुरुआत में सबसे ज़्यादा खेत जले", `${f}: उपग्रह जाँच चलाएँ`, `${f} की जाँच पूरी`],
    colour: "रंगीन", infrared: "इन्फ्रारेड", irNote: "जली ज़मीन मैरून दिखती है, गीली मिट्टी गहरी नीली।", irWait: "जाँच के बाद इन्फ्रारेड तस्वीरें दिखेंगी।", preparing: "सीज़न तैयार हो रहा है", pm: "टन PM2.5", sources: "स्रोत",
    saved: (d) => `जाँच अभी जवाब नहीं दे रही। ${d} का नतीजा दिखाया जा रहा है।`, liveNow: (n) => `अभी जाँचा गया · ${n} सेकंड`, rerun: "फिर जाँचें",
    reading: "इस खेत की सितंबर से दिसंबर तक की हर साफ़ तस्वीर पढ़ रहे हैं", checkNote: "इस खेत की इस और पिछले सीज़न की हर साफ़ Sentinel-2 तस्वीर पढ़ता है: वही सबूत जो अधिकारी देखते हैं। लगभग 20 सेकंड।",
  },
  pa: {
    loading: "ਉਪਗ੍ਰਹਿ ਤੋਂ ਸੀਜ਼ਨ ਲਿਆ ਰਹੇ ਹਾਂ", explore: "ਵੇਖੋ", officer: "ਅਧਿਕਾਰੀ", farmer: "ਕਿਸਾਨ",
    caption: "ਹਰ ਨਵੰਬਰ ਦਿੱਲੀ ਦੀ ਹਵਾ ਖ਼ਤਰਨਾਕ ਹੋ ਜਾਂਦੀ ਹੈ।<small>ਉਸ ਧੂੰਏਂ ਦਾ ਇੱਕ ਹਿੱਸਾ ਪੰਜਾਬ ਅਤੇ ਹਰਿਆਣਾ ਦੇ ਖੇਤਾਂ ਵਿੱਚ ਸਾੜੀ ਪਰਾਲੀ ਹੈ। ਸਾਕਸ਼ੀ ਪਟਿਆਲਾ–ਕੈਥਲ ਸਰਹੱਦ ਦੇ ਅਜਿਹੇ ਖੇਤਾਂ ਨੂੰ 2025 ਦੇ ਪੂਰੇ ਸੀਜ਼ਨ ਵਿੱਚ ਵੇਖਦਾ ਹੈ।</small>",
    delhi: "ਦਿੱਲੀ", seasonLbl: "2025 ਸੀਜ਼ਨ", skip: "ਛੱਡੋ", km: (n) => `ਖੇਤਰ ਤੋਂ ${n} ਕਿਮੀ`, study: "ਅਧਿਐਨ ਖੇਤਰ · ਪਾਤੜਾਂ, ਪੰਜਾਬ",
    kicker: "ਪਟਿਆਲਾ–ਕੈਥਲ ਸਰਹੱਦੀ ਖੇਤਰ · ਸਾਉਣੀ 2025",
    headline: "ਸੜੇ ਦਿਸਦੇ ਹਰ <em>10 ਵਿੱਚੋਂ 9</em> ਹੈਕਟੇਅਰ ਲਈ ਕੋਈ ਅੱਗ ਅਲਰਟ ਨਹੀਂ ਆਇਆ।",
    alerts: "ਅੱਗ ਅਲਰਟ", vslbl: "ਸਾਫ਼ ਖੇਤ ਜਿਨ੍ਹਾਂ ਨੂੰ ਗਲਤੀ ਨਾਲ ਸ਼ੱਕੀ ਕਿਹਾ (ਘੱਟ ਬਿਹਤਰ)", vscap: "ਪੰਜਾਬ ਅਤੇ ਹਰਿਆਣਾ ਦੇ 593 ਲੇਬਲ ਕੀਤੇ ਖੇਤ, ਜਿਨ੍ਹਾਂ ਵਿੱਚੋਂ 111 ਸੜੇ",
    play: "ਪੂਰਾ ਸੀਜ਼ਨ ਵੇਖੋ", explorebtn: "ਨਕਸ਼ਾ ਵੇਖੋ",
    fine: "ਸੜੇ ਵਰਗੀ: ਉਹ ਜ਼ਮੀਨ ਜੋ ਪੌਦਿਆਂ ਦਾ ਸੰਕੇਤ ਡਿੱਗਦੇ ਹੀ ਲਗਭਗ ਕਾਲੀ ਹੋ ਗਈ, Sentinel-2 ਉਪਗ੍ਰਹਿ ਤੋਂ ਵੇਖੀ।",
    l_burns: "ਸੜੇ ਖੇਤ", l_fires: "ਅੱਗ ਅਲਰਟ", l_fields: "ਖੇਤ", l_missed: "ਸਿਰਫ਼ ਉਹ ਸੜੇ ਖੇਤ ਜਿਨ੍ਹਾਂ ਉੱਤੇ ਅਲਰਟ ਨਹੀਂ ਆਇਆ", ha: "ਹੈਕਟੇਅਰ ਸੜੇ ਵਰਗੇ", fa: "ਅੱਗ ਅਲਰਟ",
    stages: ["ਖੜ੍ਹਾ ਝੋਨਾ", "ਵਾਢੀ ਸ਼ੁਰੂ", "ਵਾਢੀ", "ਪਰਾਲੀ", "ਸਭ ਤੋਂ ਵੱਧ ਸਾੜ", "ਸਾੜ ਘਟਿਆ", "ਕਣਕ ਦੀ ਬਿਜਾਈ", "ਕਣਕ ਉੱਗੀ"],
    toast: "ਖੇਤ ਖੋਲ੍ਹਣ ਲਈ ਬਿੰਦੂ ਉੱਤੇ ਟੈਪ ਕਰੋ", refphoto: "ਨੇੜਲੀ ਫ਼ੋਟੋ: Esri, ਇਸ ਸੀਜ਼ਨ ਦੀ ਨਹੀਂ",
    v: { clean: "ਸਾਫ਼", review: "ਅਧਿਕਾਰੀ ਕੋਲ", burn: "ਸਾੜ ਦਾ ਸ਼ੱਕ" },
    vline: { clean: (n) => `${n} ਸਾਫ਼ ਤਸਵੀਰਾਂ ਵਿੱਚ ਕਿਤੇ ਸਾੜ ਨਹੀਂ`, burn: (d) => `${d} ਨੂੰ ਸਾੜ ਦਾ ਨਿਸ਼ਾਨ`, review: () => "ਸਾਫ਼ ਨਹੀਂ: ਅਧਿਕਾਰੀ ਵੇਖੇਗਾ" },
    signal: "ਸੀਜ਼ਨ ਭਰ ਪੌਦਿਆਂ ਦਾ ਸੰਕੇਤ", signalNote: "ਸਾੜ ਨਾਲ ਇਹ ਇੱਕ ਰਾਤ ਵਿੱਚ ਸਿਫ਼ਰ ਤੋਂ ਹੇਠਾਂ ਡਿੱਗਦਾ ਹੈ।",
    clear: "ਸਾਫ਼ ਤਸਵੀਰਾਂ", nearest: "375 ਮੀਟਰ ਵਿੱਚ ਅੱਗ ਅਲਰਟ", smoke: { burn: "ਨਿਕਲਿਆ PM2.5, ਅੰਦਾਜ਼ਾ", clean: "ਹਵਾ ਵਿੱਚ ਜਾਣ ਤੋਂ ਬਚਿਆ PM2.5, ਅੰਦਾਜ਼ਾ", review: "ਸਾੜਨ ਤੇ PM2.5, ਅੰਦਾਜ਼ਾ" }, none: "ਕੋਈ ਨਹੀਂ", last: "ਪਿਛਲਾ ਸੀਜ਼ਨ (2024)",
    checked: (d) => `${d} ਦੀ ਲਾਈਵ ਜਾਂਚ ਦਾ ਨਤੀਜਾ`, again: "ਲਾਈਵ ਜਾਂਚ ਚਲਾਓ", check: "ਉਪਗ੍ਰਹਿ ਜਾਂਚ ਚਲਾਓ",
    steps: ["ਹਰ ਸਾਫ਼ ਤਸਵੀਰ ਲੱਭ ਰਹੇ ਹਾਂ", "ਬੱਦਲ ਹਟਾ ਰਹੇ ਹਾਂ", "ਤਾਰੀਖਾਂ ਮਿਲਾ ਰਹੇ ਹਾਂ", "ਅੱਗ ਅਲਰਟ ਜਾਂਚ ਰਹੇ ਹਾਂ"],
    acres: "ਏਕੜ", err: "ਜਾਂਚ ਪੂਰੀ ਨਹੀਂ ਹੋਈ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
    live: "ਜਾਂਚ", checking: "ਸੈਟੇਲਾਈਟ ਜਾਂਚ ਚੱਲ ਰਹੀ ਹੈ", slow: "ਆਮ ਨਾਲੋਂ ਵੱਧ ਸਮਾਂ ਲੱਗ ਰਿਹਾ ਹੈ",
    stage: { queued: "ਸ਼ੁਰੂ ਹੋ ਰਹੀ ਹੈ", current: "ਇਸ ਸੀਜ਼ਨ ਦੀਆਂ ਸਾਫ਼ ਤਸਵੀਰਾਂ ਪੜ੍ਹ ਰਹੇ ਹਾਂ, ਸਤੰਬਰ ਤੋਂ ਦਸੰਬਰ", previous: "ਅਗਾਊਂ ਲਈ ਪਿਛਲਾ ਸੀਜ਼ਨ ਪੜ੍ਹ ਰਹੇ ਹਾਂ" },
    imagesFound: (n) => `ਇਸ ਸੀਜ਼ਨ ਦੀਆਂ ${n} ਸਾਫ਼ ਤਸਵੀਰਾਂ`, pause: "ਰੋਕੋ", resume: "ਜਾਰੀ ਰੱਖੋ", exit: "ਬੰਦ ਕਰੋ",
    storySteps: (f) => ["ਸਰਹੱਦੀ ਖੇਤਰ ਉੱਤੇ 2025 ਦਾ ਸੀਜ਼ਨ", "ਪਾਤੜਾਂ ਵੱਲ, ਜਿੱਥੇ ਨਵੰਬਰ ਦੇ ਸ਼ੁਰੂ ਵਿੱਚ ਸਭ ਤੋਂ ਵੱਧ ਖੇਤ ਸੜੇ", `${f}: ਸੈਟੇਲਾਈਟ ਜਾਂਚ ਚਲਾਓ`, `${f} ਦੀ ਜਾਂਚ ਪੂਰੀ`],
    colour: "ਰੰਗੀਨ", infrared: "ਇਨਫ੍ਰਾਰੈੱਡ", irNote: "ਸੜੀ ਜ਼ਮੀਨ ਮੈਰੂਨ ਦਿਸਦੀ ਹੈ, ਗਿੱਲੀ ਮਿੱਟੀ ਗੂੜ੍ਹੀ ਨੀਲੀ।", irWait: "ਜਾਂਚ ਤੋਂ ਬਾਅਦ ਇਨਫ੍ਰਾਰੈੱਡ ਤਸਵੀਰਾਂ ਦਿਸਣਗੀਆਂ।", preparing: "ਸੀਜ਼ਨ ਤਿਆਰ ਹੋ ਰਿਹਾ ਹੈ", pm: "ਟਨ PM2.5", sources: "ਸਰੋਤ",
    saved: (d) => `ਜਾਂਚ ਹੁਣ ਜਵਾਬ ਨਹੀਂ ਦੇ ਰਹੀ। ${d} ਦਾ ਨਤੀਜਾ ਵਿਖਾਇਆ ਜਾ ਰਿਹਾ ਹੈ।`, liveNow: (n) => `ਹੁਣੇ ਜਾਂਚਿਆ · ${n} ਸਕਿੰਟ`, rerun: "ਦੁਬਾਰਾ ਜਾਂਚੋ",
    reading: "ਇਸ ਖੇਤ ਦੀ ਸਤੰਬਰ ਤੋਂ ਦਸੰਬਰ ਤੱਕ ਦੀ ਹਰ ਸਾਫ਼ ਤਸਵੀਰ ਪੜ੍ਹ ਰਹੇ ਹਾਂ", checkNote: "ਇਸ ਖੇਤ ਦੀ ਇਸ ਅਤੇ ਪਿਛਲੇ ਸੀਜ਼ਨ ਦੀ ਹਰ ਸਾਫ਼ Sentinel-2 ਤਸਵੀਰ ਪੜ੍ਹਦਾ ਹੈ: ਉਹੀ ਸਬੂਤ ਜੋ ਅਧਿਕਾਰੀ ਵੇਖਦਾ ਹੈ। ਲਗਭਗ 20 ਸਕਿੰਟ।",
  },
  hr: {
    loading: "उपग्रह तै सीज़न ल्यावां सां", explore: "देक्खो", officer: "अफसर", farmer: "किसान",
    caption: "हर नवंबर म्ह दिल्ली की हवा खतरनाक हो ज्यावै सै।<small>उस धुम्मे का एक हिस्सा पंजाब अर हरियाणा के खेतां म्ह जळी पराळी सै। साक्षी पटियाला–कैथल बॉर्डर के इसे खेतां नै 2025 के पूरे सीज़न म्ह देक्खै सै।</small>",
    delhi: "दिल्ली", seasonLbl: "2025 सीज़न", skip: "छोड़ें", km: (n) => `इलाके तै ${n} किमी`, study: "अध्ययन इलाका · पातड़ां, पंजाब",
    kicker: "पटियाला–कैथल बॉर्डर इलाका · खरीफ़ 2025",
    headline: "जळे दिक्खण आळे हर <em>10 म्ह तै 9</em> हेक्टेयर पै कोए आग का अलर्ट कोनी आया।",
    alerts: "आग अलर्ट", vslbl: "साफ खेत जिन पै गलती तै शक करया (कम आच्छा)", vscap: "पंजाब अर हरियाणा के 593 लेबल करे खेत, जिन म्ह 111 जळे",
    play: "पूरा सीज़न देक्खो", explorebtn: "नक्सा देक्खो",
    fine: "जळे बरगी: वा धरती जो पौधां का संकेत गिरते ए काळी हो गी, Sentinel-2 नै देक्खी।",
    l_burns: "जळे खेत", l_fires: "आग अलर्ट", l_fields: "खेत", l_missed: "सिर्फ वे जळे खेत जिन पै अलर्ट कोनी आया", ha: "हेक्टेयर जळे बरगे", fa: "आग अलर्ट",
    stages: ["खड़या धान", "कटाई शुरू", "कटाई", "पराळी", "सब तै घणा जळाणा", "जळाणा घटया", "गेहूं की बिजाई", "गेहूं उग्या"],
    toast: "खेत खोलण खातर बिंदु पै टैप करो", refphoto: "नजदीक की फोटू: Esri, इस सीज़न की कोनी",
    v: { clean: "साफ", review: "अफसर कनै", burn: "जळण का शक" },
    vline: { clean: (n) => `${n} साफ फोटुआं म्ह कितै जळाणा कोनी`, burn: (d) => `${d} नै जळण का निसान`, review: () => "साफ कोनी: अफसर देक्खैगा" },
    signal: "सीज़न भर पौधां का संकेत", signalNote: "जळण पै यो एक रात म्ह जीरो तै तळै गिरै सै।",
    clear: "साफ फोटू", nearest: "375 मीटर म्ह आग अलर्ट", smoke: { burn: "निकळ्या PM2.5, अंदाजा", clean: "हवा म्ह जाण तै बच्या PM2.5, अंदाजा", review: "जळाण पै PM2.5, अंदाजा" }, none: "कोए ना", last: "पाछला सीज़न (2024)",
    checked: (d) => `${d} की लाइव जांच का नतीजा`, again: "लाइव जांच चलाओ", check: "उपग्रह जांच चलाओ",
    steps: ["हर साफ फोटो टोहण लाग रे सां", "बादळ हटाण लाग रे सां", "तारीख मिलाण लाग रे सां", "आग अलर्ट जांचण लाग रे सां"],
    acres: "किल्ले", err: "जांच पूरी कोनी होई। फेर कोसिस करो।",
    live: "जांच", checking: "उपग्रह जांच चालू सै", slow: "आम तै घणा बखत लाग रया सै",
    stage: { queued: "शुरू होरी सै", current: "इस सीज़न की साफ फोटू पढ़ण लाग रे सां, सितंबर तै दिसंबर", previous: "एडवांस खातर पाछला सीज़न पढ़ण लाग रे सां" },
    imagesFound: (n) => `इस सीज़न के ${n} साफ फोटू`, pause: "रोक्को", resume: "चालू करो", exit: "बंद करो",
    storySteps: (f) => ["बॉर्डर इलाके पै 2025 का सीज़न", "पातड़ां कान्नी, जित नवंबर के शुरू म्ह सब तै घणे खेत जळे", `${f}: उपग्रह जांच चलाओ`, `${f} की जांच पूरी`],
    colour: "रंगीन", infrared: "इन्फ्रारेड", irNote: "जळी धरती मैरून दिक्खै, गीली माट्टी गहरी नीली।", irWait: "जांच पाच्छै इन्फ्रारेड फोटू दिक्खैंगे।", preparing: "सीज़न त्यार होरया सै", pm: "टन PM2.5", sources: "स्रोत",
    saved: (d) => `जांच इब्ब जवाब कोनी देरी। ${d} का नतीजा दिखाया जा रया सै।`, liveNow: (n) => `इब्बे जांच्या · ${n} सेकंड`, rerun: "फेर जांचो",
    reading: "इस खेत की सितंबर तै दिसंबर तक की हर साफ फोटो पढ़ण लाग रे सां", checkNote: "इस खेत की इस अर पाछले सीज़न की हर साफ Sentinel-2 फोटू पढ़ै सै: वाए सबूत जो अफसर देक्खै सै। करीब 20 सेकंड।",
  },
};
const HTML_LANG = { en: "en", hi: "hi", pa: "pa", hr: "hi" };
const LOCALE = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", hr: "hi-IN" };
const LOCAL_NAME = { en: ["साक्षी", "hi"], hi: ["साक्षी", "hi"], hr: ["साक्षी", "hi"], pa: ["ਸਾਕਸ਼ੀ", "pa"] };
const CODE = { en: "EN", hi: "हिं", pa: "ਪੰ", hr: "हरि" };
// Burn colours run orange to purple by date. Yellow is kept for NASA fire alerts only.
const BURN_RAMP = [[30, "#FF9D5C"], [50, "#FF6A3D"], [62, "#E8384F"], [80, "#C2187E"], [100, "#7B2CBF"]];
// smoke estimate per burnt hectare: 2.6 t straw an acre, 80% burnt, ~9 kg PM2.5 a tonne (see Sources)
const PM25_KG_PER_ACRE = 2.6 * 0.8 * 9;  // straw t/acre × share burnt × kg PM2.5 per t; same as season.py
const PM25_KG_PER_HA = PM25_KG_PER_ACRE * 2.4711;
const DELHI = [77.209, 28.6139];
const STUDY_BOX = [76.06, 29.86, 76.22, 30.01]; // the hand-labelled Patran area, glued to the Kaithal outline
const INDIA = { center: [78.6, 25.2], zoom: 4.35 };

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const icon = (id) => `<svg><use href="#${id}"/></svg>`;
const store = { get: (k) => { try { return localStorage.getItem(k); } catch { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* blocked */ } } };

let lang = store.get("saakshi-lang") || (navigator.language.startsWith("hi") ? "hi" : navigator.language.startsWith("pa") ? "pa" : "en");
if (!T[lang]) lang = "en";
const t = () => T[lang];

const state = { day: 0, playing: false, raf: 0, layers: { burns: true, fires: true, fields: true, missed: false }, intro: true, field: null, check: null, visible: new Set() };
const dotKinds = {};
let refreshDots = () => {};
let map, manifest, windows = [], day0, D0, D1, centers = [], cumHa = [], cumFires = [], beltFires = [], demo = {}, fieldsById = {}, syncPins = () => {};

// ---- language ----
function applyLang() {
  document.documentElement.lang = HTML_LANG[lang];
  $$("[data-i18n]").forEach((el) => { const v = t()[el.dataset.i18n]; if (typeof v === "string") el.innerHTML = v; });
  const [local, script] = LOCAL_NAME[lang];
  $("#name-local").textContent = local;
  $("#name-local").lang = script;
  $("#lang-cur").textContent = CODE[lang];
  $$("#lang-menu li").forEach((li) => { li.classList.toggle("on", li.dataset.lang === lang); li.setAttribute("aria-selected", li.dataset.lang === lang); });
  $$(".layers [data-tip]").forEach((b) => b.setAttribute("aria-label", t()[b.dataset.tip]));
  if (windows.length) { buildTicks(); renderTimeline(); }
  if (state.field) renderPanel();
  syncPins();
  if (map && map.getLayer && delhiMarker) delhiMarker.getElement().innerHTML = delhiHtml();
  if (studyMarker) studyMarker.getElement().textContent = t().study;
}

// ---- dates ----
const dayNum = (iso) => Math.round((new Date(iso) - day0) / 864e5);
const dateOf = (d) => new Date(day0.getTime() + d * 864e5);
const MONTH = () => (lang === "en" ? "short" : "long");
const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const PA_MONTHS = ["ਜਨਵਰੀ", "ਫ਼ਰਵਰੀ", "ਮਾਰਚ", "ਅਪ੍ਰੈਲ", "ਮਈ", "ਜੂਨ", "ਜੁਲਾਈ", "ਅਗਸਤ", "ਸਤੰਬਰ", "ਅਕਤੂਬਰ", "ਨਵੰਬਰ", "ਦਸੰਬਰ"];  // browsers often lack Punjabi month names
const fmtDay = (d, month = MONTH()) => {
  const x = dateOf(d);
  return lang === "en" ? `${x.getDate()} ${MONTHS_EN[x.getMonth()]}` : lang === "pa" ? `${x.getDate()} ${PA_MONTHS[x.getMonth()]}` : x.toLocaleDateString(LOCALE[lang], { day: "numeric", month });
};
const fmtIso = (iso) => { const x = new Date(iso); return lang === "pa" ? `${x.getDate()} ${PA_MONTHS[x.getMonth()]}` : x.toLocaleDateString(LOCALE[lang], { day: "numeric", month: "long" }); };
const fmtRange = (w) => {
  const s = new Date(w.start), e = new Date(w.end);
  const m = lang === "en" ? MONTHS_EN[e.getMonth()] : lang === "pa" ? PA_MONTHS[e.getMonth()] : e.toLocaleDateString(LOCALE[lang], { month: MONTH() });
  return `${s.getDate()}–${e.getDate()} ${m}`;
};
const windowIndex = (d) => { let k = 0; windows.forEach((w, j) => { if (dayNum(w.start) <= d) k = j; }); return k; };

// ---- timeline: one stop per day ----
function buildSpark() {
  const svg = $("#spark"), W = 1000, H = 26, n = D1 - D0;
  const daily = Array.from({ length: n + 1 }, (_, i) => manifest.burn_ha_by_day[D0 + i] || 0);
  const smooth = daily.map((_, i) => (daily[i - 1] || 0) * 0.25 + daily[i] * 0.5 + (daily[i + 1] || 0) * 0.25);
  const max = Math.max(...smooth);
  const pts = smooth.map((v, i) => [(i / n) * W, H - Math.sqrt(v / max) * H]);
  const path = `M0,${H} ` + pts.map(([x, y]) => `L${x.toFixed(1)},${y.toFixed(1)}`).join(" ") + ` L${W},${H} Z`;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.innerHTML = `<defs><clipPath id="sparkclip"><rect id="sparkcut" x="0" y="-2" width="0" height="${H + 4}"/></clipPath></defs>
    <path class="all" d="${path}"/><path class="past" d="${path}" clip-path="url(#sparkclip)"/>`;
  $("#scrub").insertAdjacentHTML("beforeend", `<div class="thumb" id="thumb"></div>`);
  const slider = $("#slider");
  slider.min = D0; slider.max = D1; slider.step = 0.1;  // fine steps so dragging glides; the map snaps to days
}
function buildTicks() {
  const marks = [D0];
  for (let d = D0 + 1; d <= D1; d++) { const x = dateOf(d); if (x.getDate() === 1 || x.getDate() === 15) marks.push(d); }
  $("#ticks").innerHTML = marks.map((d) => {
    const x = dateOf(d);
    // the season starts on the 21st, ten days before the next month: the first label keeps only its day, or the two collide
    const lab = x.getDate() === 15 || (d === D0 && marks[1] - D0 < 14 && innerWidth < 1200) ? String(x.getDate()) : fmtDay(d, "short");
    return `<span style="left:${((d - D0) / (D1 - D0)) * 100}%">${esc(lab)}</span>`;
  }).join("");
}
function renderProgress(x) {
  const frac = Math.max(0, Math.min(1, (x - D0) / (D1 - D0)));
  $("#sparkcut")?.setAttribute("width", (frac * 1000).toFixed(1));
  const th = $("#thumb");
  if (th) th.style.transform = `translateX(${(frac * $("#scrub").clientWidth).toFixed(1)}px)`;
  $("#ring").style.strokeDashoffset = (151 * (1 - frac)).toFixed(1);
}
function renderTimeline(x = state.day) {
  renderProgress(x);
  $("#when").textContent = fmtDay(state.day);
  $("#stage").textContent = t().stages[windowIndex(state.day)];
  if (document.activeElement !== $("#slider")) $("#slider").value = state.day;
  $("#ha").textContent = Math.round(cumHa[state.day - D0] || 0).toLocaleString("en-IN");
  $("#fa").textContent = (cumFires[state.day - D0] || 0).toLocaleString("en-IN");
  $("#pm").textContent = Math.round(((cumHa[state.day - D0] || 0) * PM25_KG_PER_HA) / 1000).toLocaleString("en-IN");
}

const zoomFade = (v) => ["interpolate", ["linear"], ["zoom"], 14.3, v, 15.3, 0];
function setDay(d, x = null) {
  d = Math.max(D0, Math.min(D1, Math.round(d)));
  if (d === state.day && state.ready) { renderProgress(x ?? d); return; }
  state.ready = true;
  state.day = d;
  // between the middles of two ten-day windows, fade from one picture to the next
  let j = 0;
  centers.forEach((c, m) => { if (c <= d) j = m; });
  const k = Math.min(j + 1, windows.length - 1);
  const f = k === j ? 0 : Math.max(0, Math.min(1, (d - centers[j]) / (centers[k] - centers[j])));
  // with the whole belt in view all eight pictures stay loaded, so playing never waits on a tile;
  // zoomed in, only the two pictures in play fetch tiles
  const want = state.wide ? new Set(windows.map((_, m) => m)) : new Set([j, k]);
  state.opacity = state.opacity || {};
  windows.forEach((w, m) => {
    const id = `img-${w.id}`, o = !state.revealed ? 0 : m === j ? 1 : m === k ? Math.round(f * 20) / 20 : 0;
    if (want.has(m) !== state.visible.has(m)) map.setLayoutProperty(id, "visibility", want.has(m) ? "visible" : "none");
    if (state.opacity[id] !== o) { map.setPaintProperty(id, "raster-opacity", zoomFade(o)); state.opacity[id] = o; }
  });
  state.visible = want;
  map.setFilter("burns", ["<=", ["get", "d"], d]);
  map.setFilter("burns-new", ["all", [">", ["get", "d"], d - 4], ["<=", ["get", "d"], d]]);
  map.setFilter("burn-pts", ["<=", ["get", "d"], d]);
  map.setFilter("fires", ["<=", ["get", "d"], d]);
  map.setFilter("fires-states", ["<=", ["get", "d"], d]);
  const fresh = (big, small) => ["case", [">", ["get", "d"], d - 3], big, small];
  map.setPaintProperty("fires", "circle-radius", ["interpolate", ["linear"], ["zoom"], 8, fresh(4, 2.4), 12, fresh(8, 5), 15, fresh(15, 10)]);
  renderTimeline(x ?? d);
}

function play(speed = 6, onEnd = null, from = null) {
  if (!state.loadedAll) return;
  stop();
  reveal();
  if (from !== null) setDay(from);
  else if (state.day >= D1) setDay(D0);
  state.playing = true;
  $("#play-glyph").setAttribute("href", "#i-pause");
  $("#play").setAttribute("aria-label", "Pause");
  let last = performance.now(), acc = state.day;
  const tick = (now) => {
    acc += ((now - last) / 1000) * (reduced ? speed / 2 : speed);
    last = now;
    const before = state.day;
    setDay(acc, acc);
    if (state.day !== before && state.onDay) state.onDay(state.day);
    if (state.day >= D1) { stop(); onEnd && onEnd(); return; }
    state.raf = requestAnimationFrame(tick);
  };
  state.raf = requestAnimationFrame(tick);
}
function stop() {
  cancelAnimationFrame(state.raf);
  state.playing = false;
  $("#play-glyph").setAttribute("href", "#i-play");
  $("#play").setAttribute("aria-label", "Play");
}

// ---- hero, captions, hints ----
function showHero() {
  state.intro = false;
  const h = $("#hero");
  h.hidden = false;
  document.body.classList.add("hero-open");
  requestAnimationFrame(() => requestAnimationFrame(() => h.classList.add("show")));
}
function hideHero() { $("#hero").hidden = true; document.body.classList.remove("hero-open"); }
function toast(text, ms = 4200) {
  const el = $("#toast");
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toast.t);
  toast.t = setTimeout(() => { el.hidden = true; }, ms);
}

const regionBounds = () => { const [w, s, e, n] = manifest.bounds; return [[w, s], [e, n]]; };
// on wide screens the belt sits to the right of the headline card, never under it
// with neither the card nor the field panel open, the belt is centred
const fitPadding = () => {
  const wide = innerWidth > 900, bottom = innerWidth <= 640 ? Math.round(innerHeight * 0.52) : 120;
  const hero = document.body.classList.contains("hero-open") || state.intro;
  const panel = document.body.classList.contains("panel-open");
  const side = wide ? 90 : 24;
  return { top: 90, bottom, left: wide && hero ? Math.min(520, innerWidth * 0.36) : side, right: wide && panel ? 430 : side };
};
function fitRegion(duration = 1200) {
  map.fitBounds(regionBounds(), { padding: fitPadding(), duration: reduced ? 0 : duration });
}

function playSeason() {
  hideHero();
  closePanel();
  fitRegion();
  story.on = true;
  story.paused = false;
  storyStep(0);
  state.onDay = (d) => {
    if (d === 58) { storyStep(1); map.flyTo({ center: [76.15, 29.935], zoom: 11.8, duration: reduced ? 0 : 2600, essential: true }); }
  };
  setTimeout(() => {
    if (!story.on) return;
    play(5, () => {
      state.onDay = null;
      if (!story.on) return;
      const f = fieldsById["f-baljeet"];
      if (!f) return endStory();
      storyStep(2);
      openField(f, { auto: params.get("auto") === "1" });  // ?auto=1 runs it by itself, for recordings
    }, D0);
  }, reduced ? 0 : 1300);
}

// ---- the opening: India, the smoke, then into the belt ----
let delhiMarker = null, studyMarker = null, stateFireCount = 0;
function haversineKm([lon1, lat1], [lon2, lat2]) {
  const r = Math.PI / 180, a = Math.sin(((lat2 - lat1) * r) / 2) ** 2 + Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin(((lon2 - lon1) * r) / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(a));
}
function delhiHtml() {
  const [w, s, e, n] = manifest.bounds, km = Math.round(haversineKm(DELHI, [(w + e) / 2, (s + n) / 2]) / 10) * 10;
  return `<i></i><b>${esc(t().delhi)}</b><span>${esc(t().km(km))}</span>`;
}
function fadeOut(el) {
  if (el.hidden) return;
  el.classList.add("out");
  setTimeout(() => { el.hidden = true; el.classList.remove("out"); }, 600);
}
// The opening: India, Delhi and the belt, no season data. While the camera flies in, every picture and
// layer of the season loads, so pressing Play never waits on the network and nothing pops in afterwards.
function runIntro() {
  document.body.classList.add("intro");  // phones hide the map controls while the caption speaks
  const cap = $("#caption"), [title, sub] = t().caption.split("<small>");
  cap.innerHTML = `<b>${title}</b><span>${sub.replace("</small>", "")}</span>`;
  cap.hidden = false;
  const skipBtn = $("#skip");
  skipBtn.hidden = false;
  let done = false;
  const events = ["mousedown", "wheel", "touchstart", "keydown"];
  const finish = () => {
    if (done) return;
    done = true;
    document.body.classList.remove("intro");
    events.forEach((ev) => removeEventListener(ev, skip));
    fadeOut(skipBtn);
    fadeOut(cap);
    showHero();
    preload();
  };
  const skip = () => { if (done) return; map.stop(); fitRegion(0); finish(); };
  skipBtn.onclick = skip;
  events.forEach((ev) => addEventListener(ev, skip, { once: true, passive: true }));
  setTimeout(() => {
    if (done) return;
    map.fitBounds(regionBounds(), { padding: fitPadding(), duration: 5200, curve: 1.4, essential: true });
    map.once("moveend", finish);
  }, 2200);
}

const DATA_LAYERS = ["burns", "burns-new", "burn-pts", "fires", "fires-states"];
function setPreparing(frac) {
  frac = Math.max(frac, state.prepared || 0);  // never goes backwards
  state.prepared = frac;
  const pct = Math.round(frac * 100);
  const b = $("#play-season");
  b.disabled = frac < 1;
  b.querySelector("span").textContent = frac < 1 ? t().preparing : t().play;
  let p = b.querySelector(".pct");
  if (!p) { p = document.createElement("i"); p.className = "pct"; b.append(p); }
  p.textContent = frac < 1 ? `${pct}%` : "";
  b.style.setProperty("--p", frac.toFixed(3));
  $("#explore").disabled = frac < 1;
  $("#play").disabled = frac < 1;
  if (!state.revealed) $("#ring").style.strokeDashoffset = (151 * (1 - frac)).toFixed(1);
}
function preload() {
  if (state.preloading) return;
  state.preloading = true;
  state.fitZoom = map.getZoom();
  state.wide = true;
  windows.forEach((w) => map.setLayoutProperty(`img-${w.id}`, "visibility", "visible"));
  state.visible = new Set(windows.map((_, m) => m));
  const ids = [...windows.map((w) => `img-${w.id}`), "burns", "burn-pts", "fires", "fires-states"];
  const loaded = (id) => { try { return map.isSourceLoaded(id); } catch { return false; } };
  const tick = () => {
    if (state.loadedAll) return;
    const n = ids.filter(loaded).length;
    setPreparing(n / ids.length);
    if (n === ids.length) done();
  };
  const done = () => { map.off("sourcedata", tick); clearInterval(poll); state.loadedAll = true; setPreparing(1); };
  map.on("sourcedata", tick);
  const poll = setInterval(tick, 400);
  setTimeout(() => { if (!state.loadedAll) done(); }, 15000);  // never hold the viewer longer than this
  tick();
}
// the season's layers appear only once someone starts it
function reveal() {
  if (state.revealed) return;
  state.revealed = true;
  const on = { burns: state.layers.burns, "burns-new": state.layers.burns, "burn-pts": state.layers.burns, fires: state.layers.fires, "fires-states": state.layers.fires };
  DATA_LAYERS.forEach((id) => map.setLayoutProperty(id, "visibility", on[id] ? "visible" : "none"));
  state.ready = false;
  setDay(state.day);
}

// ---- fields and the case file ----
function centroid(g) {
  const ring = g.coordinates[0], n = ring.length - 1;
  return ring.slice(0, n).reduce((a, [x, y]) => [a[0] + x / n, a[1] + y / n], [0, 0]);
}
const kindOf = (o) => (o === "auto_approved" || o === "officer_approved" ? "clean" : o === "possible_burn" ? "burn" : "review");
const ICON = { clean: "i-check", burn: "i-flame", review: "i-eye" };
// names written in Hindi, shown in Gurmukhi (same rules as messages.to_gurmukhi on the server)
const NO_GURMUKHI = { "ष": "ਸ਼", "ऋ": "ਰਿ", "ृ": "ਿ", "ॉ": "ੋ", "ऑ": "ਓ", "ॅ": "ੈ", "ऍ": "ਐ", "ः": "", "ऽ": "" };
function toGurmukhi(text) {
  let s = [...(text || "").normalize("NFC").replace(/ड\u093c/g, "ੜ").replace(/ढ\u093c/g, "ੜ")].map((ch) => {
    if (ch in NO_GURMUKHI) return NO_GURMUKHI[ch];
    const c = ch.codePointAt(0);
    return c >= 0x900 && c <= 0x97f && ch !== "।" && ch !== "॥" ? String.fromCodePoint(c + 0x100) : ch;
  }).join("");
  s = s.replace(/([\u0a15-\u0a39])\u0a4d\1/g, "\u0a71$1")
    .replace(/([\u0a15-\u0a39\u0a3f\u0a41\u0a42])\u0a02/g, "$1\u0a70")
    .replace(/\u0a4d(?![ਰਵਹ])/g, "")
    .replace(/\u0a4dਰ(?![\u0a3e-\u0a4c\u0a70\u0a71\u0a02\u0a15-\u0a39])/g, "ਰ")
    .replace(/ਿਯਾ/g, "ਿਆ")
    .replace(/ਸਿੰਹ(?![\u0a00-\u0a7f])/g, "ਸਿੰਘ");
  return s;
}
const local = (s) => (lang === "pa" ? toGurmukhi(s) : s);
const fieldName = (p) => (lang === "en" ? p.name : local(p.name_hi || p.name));

function setFieldState(id, st) { if (id) map.setFeatureState({ source: "fields", id }, st); }
function openField(f, { auto = false } = {}) {
  stop();
  if (state.field && state.field !== f) setFieldState(state.field.properties.id, { veil: false, checking: false });
  state.field = f;
  state.check = null;  // the answer comes from running the check, not from opening the card
  state.frame = 0;
  state.view = "colour";
  const id = f.properties.id;
  setFieldState(id, { veil: !dotKinds[id], checking: false });
  const narrow = innerWidth <= 640;
  map.flyTo({ center: centroid(f.geometry), zoom: 15.2, duration: reduced ? 0 : 2200, essential: true,
    offset: narrow ? [0, -innerHeight * 0.22] : [-200, 0] });
  hideHero();
  renderPanel();
  $("#panel").hidden = false;
  document.body.classList.add("panel-open");
  playFrames();
  if (auto) setTimeout(() => { if (state.field === f) runCheck(); }, reduced ? 0 : 2400);
}
function closePanel() {
  clearInterval(state.frameTimer);
  if (state.field) setFieldState(state.field.properties.id, { veil: false, checking: false });
  state.field = null; state.check = null;
  if (story.on) endStory();  // the story's last steps are about this field
  $("#panel").hidden = true;
  $("#panel").classList.remove("busy");
  document.body.classList.remove("panel-open");
}

// the field cut out of our own tiles, one picture per ten-day window
function lonLatToPx([lon, lat], z) {
  const s = 256 * 2 ** z, y = Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
  return [((lon + 180) / 360) * s, (1 - y / Math.PI) / 2 * s];
}
async function drawCut(canvas, windowId, geom, W = 128, H = 80, scale = 3) {
  const z = 14;
  const pts = geom.coordinates[0].map((c) => lonLatToPx(c, z));
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const x0 = cx - W / 2, y0 = cy - H / 2;
  canvas.width = W * scale; canvas.height = H * scale;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  const tiles = [];
  for (let tx = Math.floor(x0 / 256); tx <= Math.floor((x0 + W) / 256); tx++)
    for (let ty = Math.floor(y0 / 256); ty <= Math.floor((y0 + H) / 256); ty++) tiles.push([tx, ty]);
  await Promise.all(tiles.map(([tx, ty]) => new Promise((ok) => {
    const img = new Image();
    img.onload = () => { ctx.drawImage(img, (tx * 256 - x0) * scale, (ty * 256 - y0) * scale, 256 * scale, 256 * scale); ok(); };
    img.onerror = ok;
    img.src = `/tiles/${windowId}/${z}/${tx}/${ty}.webp`;
  })));
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = Math.max(1.5, scale * 0.7);
  ctx.beginPath();
  pts.forEach(([x, y], i) => (i ? ctx.lineTo : ctx.moveTo).call(ctx, (x - x0) * scale, (y - y0) * scale));
  ctx.closePath();
  ctx.stroke();
}
function irData() {
  const c = state.check;
  if (!c || c.status !== "done") return null;
  const cur = c.result.current;
  return cur.evidence_url ? { url: cur.evidence_url, dates: cur.evidence_dates || null, burn: cur.decision.burn_date } : null;
}
// the evidence image has one column per date: a label row, the colour picture, then the infrared picture
function drawIr(canvas, img, j, n, W = 128, H = 64, scale = 3) {
  const fw = img.width / n, w = fw - 4, h = (img.height - 16 - 8) / 2, y = 16 + h + 4;
  canvas.width = W * scale; canvas.height = H * scale;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const k = Math.min(canvas.width / w, canvas.height / h);  // the whole frame, field and its surroundings
  ctx.drawImage(img, j * fw, y, w, h, (canvas.width - w * k) / 2, (canvas.height - h * k) / 2, w * k, h * k);
}
async function renderViewer() {
  const f = state.field, ir = state.view === "ir" ? irData() : null;
  const viewer = $("#viewer"), strip = $("#strip");
  if (!viewer) return;
  $$(".vtabs button").forEach((b) => b.classList.toggle("on", b.dataset.v === (ir ? "ir" : "colour")));
  $("#irnote").hidden = !ir;
  if (ir && ir.dates) {
    const img = new Image();
    img.src = ir.url;
    await img.decode().catch(() => {});
    if (state.view !== "ir" || state.field !== f) return;
    const n = ir.dates.length;
    viewer.innerHTML = ir.dates.map(() => "<canvas></canvas>").join("") + `<span class="tag"></span>`;
    strip.style.setProperty("--n", n);
    const short = (d, j) => { const x = new Date(d); return j === 0 || d === ir.burn || x.getDate() <= 10 && j && new Date(ir.dates[j - 1]).getMonth() !== x.getMonth() ? fmtDay(dayNum(d), "short") : String(x.getDate()); };
    strip.innerHTML = ir.dates.map((d, j) => `<button class="${d === ir.burn ? "burnt" : ""}"><canvas></canvas><span>${esc(short(d, j))}</span></button>`).join("");
    $$("canvas", viewer).forEach((c, j) => drawIr(c, img, j, n));
    $$("canvas", strip).forEach((c, j) => drawIr(c, img, j, n, 128, 64, 1));
    $$("button", strip).forEach((b, j) => { b.onclick = () => showFrame(j); });
    state.frames = ir.dates.map((d) => fmtIso(d));
    showFrame(Math.max(0, ir.dates.indexOf(ir.burn)));
    return;
  }
  if (ir) {  // an older saved result without frame dates: show the evidence image as it is
    viewer.innerHTML = `<img class="whole" src="${esc(ir.url)}" alt="">`;
    strip.innerHTML = "";
    return;
  }
  viewer.innerHTML = windows.map(() => "<canvas></canvas>").join("") + `<span class="tag"></span><span class="tag burnt" id="burntag" hidden></span>`;
  strip.style.setProperty("--n", windows.length);
  strip.innerHTML = windows.map((w, j) => `<button aria-label="${esc(fmtRange(w))}"><canvas></canvas><span>${esc(j === 0 || new Date(w.start).getDate() === 1 ? fmtDay(dayNum(w.start), "short") : String(new Date(w.start).getDate()))}</span></button>`).join("");
  const big = $$("canvas", viewer), small = $$("canvas", strip);
  windows.forEach((w, j) => { drawCut(big[j], w.id, f.geometry, 128, 64); drawCut(small[j], w.id, f.geometry, 128, 64, 1); });
  $$("button", strip).forEach((b, j) => { b.onclick = () => { clearInterval(state.frameTimer); showFrame(j); }; });
  state.frames = null;
  const bw = burnWindow();
  $$("button", strip).forEach((b, j) => b.classList.toggle("burnt", j === bw));
  showFrame(state.frame || 0);
  renderBurnTag();
}
function renderBurnTag() {
  const tag = $("#burntag"), bw = burnWindow();
  if (!tag) return;
  if (bw >= 0) { tag.textContent = t().vline.burn(fmtIso(state.check.result.current.decision.burn_date)); tag.hidden = false; } else tag.hidden = true;
}
function burnWindow() {
  const d = state.check?.status === "done" ? state.check.result.current.decision.burn_date : null;
  return d ? windowIndex(dayNum(d)) : -1;
}
function showFrame(i) {
  state.frame = i;
  $$("#viewer canvas").forEach((c, j) => c.classList.toggle("on", j === i));
  $$("#strip button").forEach((b, j) => b.classList.toggle("on", j === i));
  const tag = $("#viewer .tag");
  if (tag) tag.textContent = state.frames ? state.frames[i] : fmtRange(windows[i]);
}
function playFrames(endAt = null) {
  clearInterval(state.frameTimer);
  if (state.view === "ir") return;
  if (reduced) { showFrame(endAt ?? windows.length - 1); return; }
  let i = 0;
  showFrame(0);
  const last = endAt ?? windows.length - 1;
  state.frameTimer = setInterval(() => {
    if (i >= last) { clearInterval(state.frameTimer); return; }
    showFrame(++i);
  }, 520);
}

const ORBIT = `<div class="orbit" aria-hidden="true"><svg class="o-mark" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="url(#sky)"/><use href="#sa" fill="#fff" transform="translate(32 30) scale(.8) translate(-32 -33)"/></svg>
  <svg class="o-ring" viewBox="0 0 120 120"><ellipse cx="60" cy="60" rx="56" ry="16"/></svg><div class="o-path"><i class="o-sat"></i></div></div>`;

function actionHtml() {
  const L = t(), c = state.check;
  if (c && c.status === "done") {
    const d = c.result.current.decision, k = kindOf(d.outcome);
    const vline = k === "burn" ? L.vline.burn(fmtIso(d.burn_date)) : k === "clean" ? L.vline.clean(d.clear_dates.length) : L.vline.review();
    const meta = c.saved ? L.saved(fmtIso(c.checked_at)) : L.liveNow(c.seconds);
    const kg = Math.round((state.field?.properties.acres || 0) * PM25_KG_PER_ACRE);
    return `<div class="band ${k}"><div class="ic">${icon(ICON[k])}</div><div class="bt"><b>${esc(L.v[k])}</b><p>${esc(vline)}</p>
      <p class="smoke-l" title="2.6 t straw an acre, 80% burnt, ~9 kg PM2.5 a tonne">≈ ${kg} kg ${esc(L.smoke[k])}</p>
      <small>${esc(meta)} · <button class="link" id="run-check">${esc(L.rerun)}</button></small></div></div>`;
  }
  if (c && !c.failed) {
    const st = L.stage[c.stage] || L.stage.queued;
    const found = c.images ? ` · ${L.imagesFound(c.images)}` : "";
    return `<div class="status">${ORBIT}<div><p class="st1">${esc(L.checking)}</p>
      <p class="st2">${esc(st + found)}</p><p class="st3"><span class="elapsed">${c.elapsed || 0} s</span>${c.slow ? ` · ${esc(L.slow)}` : ""}</p></div></div>`;
  }
  return `<div class="act">${c && c.failed ? `<p class="err">${esc(L.err)}</p>` : ""}
    <button class="btn primary wide${story.on ? " pulse" : ""}" id="run-check">${icon("i-scan")}<span>${esc(L.check)}</span></button>
    <p class="cap">${esc(L.checkNote)}</p></div>`;
}
function detailsHtml() {
  const L = t(), c = state.check;
  if (!c || c.status !== "done") return "";
  const cur = c.result.current, d = cur.decision, kp = kindOf(c.result.previous.decision.outcome);
  return `<div class="sec"><dl class="facts"><div><dt>${esc(L.clear)}</dt><dd>${d.clear_dates.length}</dd></div>
      <div><dt>${esc(L.nearest)}</dt><dd>${cur.fires.length || esc(L.none)}</dd></div></dl></div>
    <div class="sec"><div class="last"><span class="mini ${kp}">${icon(ICON[kp])}</span><span>${esc(L.last)}: <b>${esc(L.v[kp])}</b></span></div></div>`;
}
// the parts that change while a check runs are redrawn alone, so the pictures do not reload
function renderAction() {
  const el = $("#action");
  if (!el) return;
  el.innerHTML = actionHtml();
  $("#details").innerHTML = detailsHtml();
  $("#run-check")?.addEventListener("click", runCheck);
  const busy = state.check && state.check.status !== "done" && !state.check.failed;
  $("#panel").classList.toggle("busy", !!busy);
  const ir = $(".vtabs [data-v=ir]");
  if (ir) { ir.disabled = !irData(); ir.title = irData() ? "" : t().irWait; }
  if (state.view !== "ir") {
    const bw = burnWindow();
    $$("#strip button").forEach((b, j) => b.classList.toggle("burnt", j === bw));
    renderBurnTag();
  }
  requestAnimationFrame(() => { const pn = $("#panel"); pn.classList.toggle("scrolls", pn.scrollHeight > pn.clientHeight + 4); });
}
function renderPanel() {
  const f = state.field, p = f.properties, L = t();
  const village = lang === "en" ? p.village : local(p.village_hi || p.village);
  $("#panel-body").innerHTML = `<div class="head"><h2>${esc(fieldName(p))}</h2><p class="sub">${p.acres} ${esc(L.acres)} · ${esc(village)}</p></div>
    <div id="action"></div>
    <div class="vtabs" role="tablist"><button role="tab" data-v="colour">${esc(L.colour)}</button><button role="tab" data-v="ir">${esc(L.infrared)}</button></div>
    <div class="viewer" id="viewer"></div>
    <div class="strip" id="strip"></div>
    <p class="cap irnote" id="irnote" hidden>${esc(L.irNote)}</p>
    <div id="details"></div>`;
  $$(".vtabs button").forEach((b) => { b.onclick = () => { if (b.disabled) return; state.view = b.dataset.v; clearInterval(state.frameTimer); renderViewer(); }; });
  renderViewer();
  renderAction();
}

function glowLoop(f) {
  const id = f.properties.id;
  const tick = (now) => {
    if (!state.check || state.check.status === "done" || state.check.failed || state.field !== f) {
      map.setPaintProperty("field-glow", "line-opacity", ["case", ["boolean", ["feature-state", "checking"], false], 0.6, 0]);
      return;
    }
    const o = 0.35 + 0.35 * Math.sin(now / 300);
    map.setPaintProperty("field-glow", "line-opacity", ["case", ["boolean", ["feature-state", "checking"], false], o, 0]);
    requestAnimationFrame(tick);
  };
  setFieldState(id, { checking: true });
  requestAnimationFrame(tick);
}

async function runCheck() {
  const f = state.field, id = f.properties.id, t0 = performance.now();
  state.check = { status: "queued", stage: "queued", elapsed: 0 };
  renderAction();
  playFrames();
  glowLoop(f);
  const tick = setInterval(() => {
    if (!state.check || state.check.status === "done" || state.check.failed || state.field !== f) return clearInterval(tick);
    state.check.elapsed = Math.round((performance.now() - t0) / 1000);
    state.check.slow = state.check.elapsed >= 30;
    const el = $("#panel .elapsed");
    if (el) el.textContent = `${state.check.elapsed} s`;
    if (state.check.slow && !$("#panel .st3").textContent.includes("·")) renderAction();
  }, 1000);
  const finish = (check) => {
    clearInterval(tick);
    if (state.field !== f) return;
    state.check = check;
    setFieldState(id, { checking: false, veil: false });
    const d = check.status === "done" ? check.result.current.decision : null;
    if (d) {
      dotKinds[id] = kindOf(d.outcome);
      setFieldState(id, { k: dotKinds[id] });
      refreshDots();
      if (d.burn_date) { reveal(); setDay(dayNum(d.burn_date) + 1); }
      clearInterval(state.frameTimer);
      if (state.view !== "ir") showFrame(d.burn_date ? windowIndex(dayNum(d.burn_date)) : windows.length - 1);
    }
    renderAction();
    if (story.on) storyStep(3);
  };
  try {
    const r = await fetch("/api/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ geometry: f.geometry }) });
    if (!r.ok) throw new Error(String(r.status));
    const { id: cid } = await r.json();
    for (let k = 0; k < 20 && state.field === f; k++) {   // 40 s, then the saved result
      await new Promise((ok) => setTimeout(ok, 2000));
      const item = await (await fetch(`/api/check/${cid}`)).json();
      if (item.status === "done") return finish({ ...item, status: "done", checked_at: item.done_at, seconds: Math.round((performance.now() - t0) / 1000) });
      if (item.status === "error") throw new Error(item.error || "error");
      if (state.check && state.field === f && (item.stage !== state.check.stage || item.clear_images !== state.check.images)) {
        state.check.stage = item.stage || "queued";
        state.check.images = item.clear_images;
        renderAction();
      }
    }
    throw new Error("timeout");
  } catch {
    // the live check could not finish: fall back to the result this field got from an earlier live run, said as such
    const saved = demo[f.properties.id];
    finish(saved ? { status: "done", saved: true, ...saved } : { failed: true });
  }
}

// ---- the guided story ("Play the season"): a bar says where it is and lets the viewer pause or leave ----
const story = { on: false, paused: false };
function storyStep(i) {
  const bar = $("#story"), L = t();
  const name = fieldsById["f-baljeet"] ? fieldName(fieldsById["f-baljeet"].properties) : "";
  $("#story-step").textContent = L.storySteps(name)[i];
  $("#story-pause").hidden = i >= 2;
  if (i === 3) setTimeout(() => { if (story.on) endStory(); }, 6000);
  bar.hidden = false;
}
function endStory() {
  story.on = false;
  state.onDay = null;
  fadeOut($("#story"));
}

// ---- map ----
async function init() {
  const [mf, demoChecks] = await Promise.all([
    fetch("/tiles/manifest.json").then((r) => r.json()),
    fetch("data/demo_checks.json").then((r) => (r.ok ? r.json() : {})).catch(() => ({})),
  ]);
  manifest = mf; demo = demoChecks;
  windows = manifest.windows;
  day0 = new Date(manifest.day0);
  D0 = dayNum(windows[0].start); D1 = dayNum(windows.at(-1).end);
  centers = windows.map((w) => (dayNum(w.start) + dayNum(w.end)) / 2);
  let acc = 0;
  cumHa = Array.from({ length: D1 - D0 + 1 }, (_, i) => (acc += manifest.burn_ha_by_day[D0 + i] || 0));
  state.day = D0;
  buildSpark();

  const intro = params.get("intro") !== "0" && !reduced;  // every visit; any click, key or the Skip button skips it
  map = new maplibregl.Map({
    container: "map", attributionControl: false, fadeDuration: 0, maxZoom: 17.5, minZoom: 3,
    ...(intro ? INDIA : { bounds: regionBounds(), fitBoundsOptions: { padding: fitPadding() } }),
    style: {
      version: 8,
      sources: {
        esri: { type: "raster", tileSize: 256, maxzoom: 18,
          tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"] },
        labels: { type: "raster", tileSize: 256, maxzoom: 13,
          tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"] },
      },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": "#0D0E11" } },
        { id: "esri", type: "raster", source: "esri", paint: {
          "raster-saturation": ["interpolate", ["linear"], ["zoom"], 9, -0.7, 13, -0.55, 15, 0],
          "raster-brightness-max": ["interpolate", ["linear"], ["zoom"], 5, 0.62, 9, 0.42, 13, 0.4, 15, 1],
          "raster-contrast": ["interpolate", ["linear"], ["zoom"], 13, -0.15, 15, 0] } },
      ],
    },
  });
  window.saakshi = { map, state };
  const data = Promise.all([
    fetch("data/region.geojson").then((r) => r.json()),
    fetch("data/states.geojson").then((r) => r.json()),
    fetch("/tiles/fires.geojson").then((r) => r.json()),
    fetch("/tiles/fires_states.geojson").then((r) => r.json()).catch(() => ({ type: "FeatureCollection", features: [] })),
    fetch("/api/fields").then((r) => (r.ok ? r.json() : [])).catch(() => []),
  ]);
  map.addControl(new maplibregl.ScaleControl({ unit: "metric", maxWidth: 110 }), "bottom-left");

  // isStyleLoaded() also waits for basemap tiles, and style.load can fire before we listen: poll the style itself
  while (!(map.style && map.style._loaded)) await new Promise((ok) => setTimeout(ok, 30));
  const [region, states, firesFc, stateFires, fieldsList] = await data;
  beltFires = firesFc.features;
  stateFireCount = stateFires.features.length;
  let fa = 0;
  const byDay = {};
  beltFires.forEach((f) => { byDay[f.properties.d] = (byDay[f.properties.d] || 0) + 1; });
  cumFires = Array.from({ length: D1 - D0 + 1 }, (_, i) => (fa += byDay[D0 + i] || 0));

  // high-density screens and in-between zooms stretch 256 px tiles: ask for the next zoom's tiles instead
  windows.forEach((w) => {
    map.addSource(`img-${w.id}`, { type: "raster", tileSize: devicePixelRatio >= 1.5 ? 128 : 256, minzoom: manifest.minzoom, maxzoom: manifest.maxzoom, bounds: manifest.bounds,
      tiles: [`${location.origin}/tiles/${w.id}/{z}/{x}/{y}.webp`] });
    map.addLayer({ id: `img-${w.id}`, type: "raster", source: `img-${w.id}`, layout: { visibility: "none" },
      paint: { "raster-opacity": 0, "raster-opacity-transition": { duration: 0 }, "raster-fade-duration": 120 } });
  });
  map.addSource("region", { type: "geojson", data: region });
  map.addLayer({ id: "region", type: "line", source: "region", paint: { "line-color": "#FFFFFF", "line-opacity": 0.55, "line-width": 1.1 } });
  const [bw, bs, be, bn] = STUDY_BOX;
  map.addSource("study", { type: "geojson", data: { type: "Feature", geometry: { type: "Polygon", coordinates: [[[bw, bs], [be, bs], [be, bn], [bw, bn], [bw, bs]]] } } });
  map.addLayer({ id: "study", type: "line", source: "study", minzoom: 8, paint: { "line-color": "#FFFFFF", "line-opacity": 0.8, "line-width": 1.2, "line-dasharray": [3, 3] } });

  map.addSource("burns", { type: "geojson", data: "/tiles/burns.geojson", tolerance: 0.1 });
  map.addLayer({ id: "burns", type: "fill", source: "burns", layout: { visibility: "none" }, paint: {
    "fill-color": ["interpolate", ["linear"], ["get", "d"], ...BURN_RAMP.flat()],
    "fill-opacity": ["interpolate", ["linear"], ["zoom"], 9, 0.95, 14, 0.7, 16, 0.3] } });
  map.addLayer({ id: "burns-new", type: "line", source: "burns", layout: { visibility: "none" }, paint: { "line-color": "#FFFFFF",
    "line-width": ["interpolate", ["linear"], ["zoom"], 9, 1, 14, 2.2], "line-blur": 0.6, "line-opacity": 0.85 } });
  // across the whole belt a 20 m patch is under a pixel: one dot per patch, sized by its area
  map.addSource("burn-pts", { type: "geojson", data: "/tiles/burn_points.geojson" });
  map.addLayer({ id: "burn-pts", type: "circle", source: "burn-pts", maxzoom: 12.2, layout: { visibility: "none" }, paint: {
    "circle-color": ["interpolate", ["linear"], ["get", "d"], ...BURN_RAMP.flat()],
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, ["+", 0.9, ["*", 1.5, ["sqrt", ["get", "ha"]]]], 11.5, ["+", 1.6, ["*", 4, ["sqrt", ["get", "ha"]]]]],
    "circle-opacity": ["interpolate", ["linear"], ["zoom"], 11, 0.9, 12.2, 0] } });

  map.addSource("fires-states", { type: "geojson", data: stateFires });
  map.addLayer({ id: "fires-states", type: "circle", source: "fires-states", maxzoom: 8.2, layout: { visibility: "none" }, paint: {
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 1.5, 5, 1.8, 7, 2.1],
    "circle-color": "#F5C542", "circle-blur": 0.25, "circle-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.85, 7.7, 0.8, 8.2, 0] } });
  map.addSource("fires", { type: "geojson", data: firesFc });
  map.addLayer({ id: "fires", type: "circle", source: "fires", minzoom: 7.7, layout: { visibility: "none" }, paint: {
    "circle-radius": 3, "circle-color": "rgba(245,197,66,0.18)", "circle-stroke-color": "#F5C542",
    "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 8, 1.3, 12, 1.7, 15, 2.4],
    "circle-opacity": ["interpolate", ["linear"], ["zoom"], 7.7, 0, 8.2, 1], "circle-stroke-opacity": ["interpolate", ["linear"], ["zoom"], 7.7, 0, 8.2, 1] } });

  map.addLayer({ id: "labels", type: "raster", source: "labels", paint: {
    "raster-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.95, 11, 0.85, 12.5, 0] } });
  map.addSource("states", { type: "geojson", data: states });
  map.addLayer({ id: "states", type: "line", source: "states", maxzoom: 11, paint: { "line-color": "#FFFFFF", "line-opacity": 0.35, "line-width": 1, "line-dasharray": [4, 3] } });

  const fieldsFc = { type: "FeatureCollection", features: fieldsList.map(({ geometry, ...p }) => ({ type: "Feature", id: p.id, properties: p, geometry })) };
  fieldsFc.features.forEach((f) => { fieldsById[f.properties.id] = f; });
  // dots stay neutral until a field is checked in this visit, so the map does not give the answer away
  const kindFor = (id) => dotKinds[id] || "none";
  const dotsFc = { type: "FeatureCollection", features: fieldsFc.features.map((f) => ({ type: "Feature", properties: { id: f.properties.id, k: kindFor(f.properties.id) }, geometry: { type: "Point", coordinates: centroid(f.geometry) } })) };
  // no simplification: a field drawn on a 20 m grid must keep its steps at every zoom, even mid-flight
  map.addSource("fields", { type: "geojson", data: fieldsFc, promoteId: "id", tolerance: 0, maxzoom: 16 });
  map.addSource("field-dots", { type: "geojson", data: dotsFc });
  refreshDots = () => {
    dotsFc.features.forEach((d) => { d.properties.k = kindFor(d.properties.id); });
    map.getSource("field-dots").setData(dotsFc);
    syncPins();
  };
  map.addLayer({ id: "fields-hit", type: "fill", source: "fields", minzoom: 12.5, paint: { "fill-color": "#FFFFFF", "fill-opacity": 0.04 } });
  // an open, unchecked field is veiled so the burn map does not answer before the check does
  map.addLayer({ id: "field-veil", type: "fill", source: "fields", paint: { "fill-color": "#0D0E11",
    "fill-opacity": ["case", ["boolean", ["feature-state", "veil"], false], 0.45, 0] } });
  map.addLayer({ id: "field-verdict", type: "fill", source: "fields", paint: {
    "fill-color": ["match", ["feature-state", "k"], "clean", "#43C485", "burn", "#FF6A3D", "review", "#F5C542", "#000000"],
    "fill-opacity": ["case", ["==", ["typeof", ["feature-state", "k"]], "string"], 0.3, 0] } });
  map.addLayer({ id: "field-glow", type: "line", source: "fields", paint: { "line-color": "#9FE3FF", "line-blur": 5,
    "line-width": ["interpolate", ["linear"], ["zoom"], 11, 4, 15, 10],
    "line-opacity": ["case", ["boolean", ["feature-state", "checking"], false], 0.6, 0] } });
  map.addLayer({ id: "fields", type: "line", source: "fields", minzoom: 12.5, paint: { "line-color": "#FFFFFF", "line-width": ["interpolate", ["linear"], ["zoom"], 12.5, 1.2, 15, 2.5] } });
  const dotColor = ["match", ["get", "k"], "clean", "#43C485", "burn", "#FF6A3D", "review", "#F5C542", "#FFFFFF"];
  map.addLayer({ id: "field-dots-halo", type: "circle", source: "field-dots", minzoom: 7.5, maxzoom: 12.5, paint: {
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 7, 12, 12], "circle-color": dotColor, "circle-opacity": 0.22, "circle-blur": 0.4 } });
  map.addLayer({ id: "field-dots", type: "circle", source: "field-dots", minzoom: 7.5, maxzoom: 12.5, paint: {
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3.5, 12, 5.5], "circle-color": dotColor,
    "circle-stroke-color": "#0D0E11", "circle-stroke-width": 1.5 } });

  const pins = fieldsFc.features.map((f) => {
    const el = document.createElement("button");
    el.className = "pin";
    el.onclick = (e) => { e.stopPropagation(); openField(f); };
    const ring = f.geometry.coordinates[0], east = ring.reduce((a, c) => (c[0] > a[0] ? c : a), ring[0]);
    return { f, el, m: new maplibregl.Marker({ element: el, anchor: "left", offset: [10, 0] }).setLngLat([east[0], centroid(f.geometry)[1]]) };
  });
  syncPins = () => pins.forEach(({ f, el, m }) => {
    // classList, not className: the map keeps its own positioning classes on the marker element
    el.classList.remove("clean", "burn", "review", "none");
    el.classList.add("pin", kindFor(f.properties.id));
    el.lang = HTML_LANG[lang];
    el.innerHTML = `<i></i>${esc(fieldName(f.properties))}`;
    if (map.getZoom() >= 12.5 && state.layers.fields) m.addTo(map); else m.remove();
  });
  Object.assign(window.saakshi, { pins, syncPins });

  delhiMarker = new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "delhi" }), anchor: "left", offset: [-6, 0] }).setLngLat(DELHI).addTo(map);
  delhiMarker.getElement().innerHTML = delhiHtml();
  studyMarker = new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "study-label" }), anchor: "bottom-left", offset: [0, -4] }).setLngLat([bw, bn]);
  const stateLabels = [["PUNJAB", [75.35, 30.95]], ["HARYANA", [76.25, 29.0]]].map(([name, at]) =>
    new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "state-label", textContent: name }) }).setLngLat(at));
  const onZoom = () => {
    const z = map.getZoom();
    syncPins();
    delhiMarker.getElement().style.display = z < 10.5 ? "" : "none";
    if (z >= 8.5 && z < 12.5) studyMarker.addTo(map); else studyMarker.remove();
    stateLabels.forEach((m) => (z >= 5.5 && z < 9.5 ? m.addTo(map) : m.remove()));
  };
  map.on("zoom", onZoom);
  applyLang();
  onZoom();

  const tip = $("#tip");
  map.on("click", "fields-hit", (e) => openField(fieldsById[e.features[0].properties.id]));
  map.on("click", "field-dots", (e) => openField(fieldsById[e.features[0].properties.id]));
  map.on("mousemove", "field-dots", (e) => {
    map.getCanvas().style.cursor = "pointer";
    const p = fieldsById[e.features[0].properties.id].properties;
    tip.textContent = `${fieldName(p)} · ${p.acres} ${t().acres}`;
    tip.hidden = false;
    tip.style.left = `${e.originalEvent.clientX + 14}px`;
    tip.style.top = `${e.originalEvent.clientY - 12}px`;
  });
  map.on("mouseleave", "field-dots", () => { map.getCanvas().style.cursor = ""; tip.hidden = true; });
  map.on("mouseenter", "fields-hit", () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", "fields-hit", () => { map.getCanvas().style.cursor = ""; });

  // controls
  $("#play").onclick = () => { if (!state.loadedAll) return; state.intro = false; hideHero(); state.playing ? stop() : play(6); };
  $("#slider").oninput = (e) => { if (!state.loadedAll) return; state.intro = false; reveal(); stop(); const x = Number(e.target.value); setDay(x, x); };
  $("#slider").onchange = (e) => setDay(Number(e.target.value));
  $("#play-season").onclick = playSeason;
  $("#story-exit").onclick = () => { stop(); endStory(); };
  $("#story-pause").onclick = () => {
    story.paused = !story.paused;
    $("#story-pause").textContent = story.paused ? t().resume : t().pause;
    if (story.paused) stop(); else play(5, () => {
      state.onDay = null;
      if (!story.on) return;
      storyStep(2);
      openField(fieldsById["f-baljeet"], { auto: params.get("auto") === "1" });
    });
  };
  $("#explore").onclick = () => { if (!state.loadedAll) return; hideHero(); reveal(); setDay(D1); toast(t().toast); };
  $("#src-btn").onclick = (e) => { e.stopPropagation(); $("#sources").hidden = !$("#sources").hidden; };
  addEventListener("click", (e) => { if (!e.target.closest("#sources")) $("#sources").hidden = true; });
  // zoomed out over the belt keep every picture loaded; zoomed in fetch only the two in play
  map.on("zoomend", () => {
    if (!state.preloading) return;
    const wide = map.getZoom() <= (state.fitZoom || 9) + 1.3;
    if (wide !== state.wide) { state.wide = wide; state.ready = false; setDay(state.day); }
  });
  $("#panel-close").onclick = closePanel;
  $("#zoom-in").onclick = () => map.zoomIn();
  $("#zoom-out").onclick = () => map.zoomOut();
  $("#zoom-fit").onclick = () => { closePanel(); fitRegion(900); };
  const setLayer = (k, on) => {
    state.layers[k] = on;
    const b = $(`.layers [data-layer="${k}"]`);
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", on);
    if (k === "missed") {
      // dim the patches a fire alert came within 375 m of; what stays lit is what the alerts missed
      map.setPaintProperty("burns", "fill-opacity", on ? ["case", ["==", ["get", "a"], 1], 0.12, 0.95]
        : ["interpolate", ["linear"], ["zoom"], 9, 0.95, 14, 0.7, 16, 0.3]);
      map.setPaintProperty("burn-pts", "circle-opacity", on ? ["case", ["==", ["get", "a"], 1], 0.12, 0.95]
        : ["interpolate", ["linear"], ["zoom"], 11, 0.9, 12.2, 0]);
      if (on && !state.layers.burns) setLayer("burns", true);
      return;
    }
    const ids = k === "burns" ? ["burns", "burns-new", "burn-pts"] : k === "fires" ? ["fires", "fires-states"] : ["fields", "fields-hit", "field-dots", "field-dots-halo"];
    if (k !== "fields" && !state.revealed) return;
    ids.forEach((id) => map.setLayoutProperty(id, "visibility", on ? "visible" : "none"));
    syncPins();
  };
  $$(".layers button").forEach((b) => {
    b.onclick = () => setLayer(b.dataset.layer, !state.layers[b.dataset.layer]);
    b.onmouseenter = () => { const r = b.getBoundingClientRect(); tip.textContent = t()[b.dataset.tip]; tip.hidden = false; tip.style.left = `${r.left - tip.offsetWidth - 10}px`; tip.style.top = `${r.top + 6}px`; requestAnimationFrame(() => { tip.style.left = `${r.left - tip.offsetWidth - 10}px`; }); };
    b.onmouseleave = () => { tip.hidden = true; };
  });
  const menu = $("#lang-menu"), btn = $("#lang-btn");
  const openMenu = (open) => { menu.hidden = !open; btn.setAttribute("aria-expanded", open); };
  btn.onclick = (e) => { e.stopPropagation(); openMenu(menu.hidden); };
  $$("#lang-menu li").forEach((li) => {
    li.tabIndex = 0;
    li.onclick = () => { lang = li.dataset.lang; store.set("saakshi-lang", lang); applyLang(); openMenu(false); };
    li.onkeydown = (e) => { if (e.key === "Enter") li.click(); };
  });
  addEventListener("click", () => openMenu(false));
  addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea")) return;
    if (e.key === " ") { e.preventDefault(); $("#play").click(); }
    if (!state.loadedAll) return;
    if (e.key === "ArrowRight") { stop(); reveal(); setDay(state.day + (e.shiftKey ? 10 : 1)); }
    if (e.key === "ArrowLeft") { stop(); reveal(); setDay(state.day - (e.shiftKey ? 10 : 1)); }
    if (e.key === "Escape") { closePanel(); openMenu(false); }
  });
  addEventListener("resize", () => { if (state.intro && !intro) fitRegion(0); });

  setDay(D0);
  setPreparing(0);
  // the basemap and outlines are enough to begin; the season loads while the camera flies in
  $("#loader").classList.add("gone");
  setTimeout(() => $("#loader")?.remove(), 700);
  if (intro) { setTimeout(runIntro, 300); return; }
  showHero();
  preload();
}

init().catch((e) => {
  document.body.insertAdjacentHTML("beforeend", `<p class="err" style="position:fixed;top:90px;left:16px;z-index:9">Map failed to load: ${esc(e.message)}</p>`);
});
