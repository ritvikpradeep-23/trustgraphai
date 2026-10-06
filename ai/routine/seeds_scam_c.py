"""Scam seeds, part 3 of 3. Same format as seeds_scam_a.py.

Note: the "fake CAPTCHA" seeds describe the scam pattern (a "human check" that
asks you to run a command the page copied for you) WITHOUT spelling out the
exact keystrokes, so this file is not itself operational malware guidance. The
detector only needs the wording tells, not runnable steps.
"""

SCAM_C = {
    "romance": {
        "in_corpus": "yes (romance scam money request)",
        "seeds": [
            ("English", "My love, I'm stuck at the airport and customs want {amount} before they release my bags. I'll pay you back the moment I land."),
            ("English", "I've never felt like this about anyone. I want to visit you, but I need help with the ticket, can you send something?"),
            ("English", "Darling, my bank account is frozen while I'm working on the oil rig. Could you lend me a little until next week?"),
            ("English", "I'm sending you a parcel with gifts and some cash, you just need to pay the delivery charge when they contact you."),
            ("English", "Good morning sweetheart, thinking of you. Life on the base is lonely. Tell me about your day?"),
            ("Hinglish", "Jaan, main airport pe phas gaya hoon, customs wale {amount} maang rahe hain. Bhej do na, aate hi lauta dunga."),
            ("Manglish", "Darling, njan airport il kudungi, customs {amount} chodikkunnu. Ayachu tharamo? Vannal udane thirichu tharam."),
            ("English", "I don't usually ask anyone for anything, but my daughter is in hospital and my cards don't work here. You're the only one I trust."),
        ],
        "templates": [
            "My {pet}, I'm {stuck}. {who} want {amount} before {release}. Please help, I'll pay you back {when}.",
            "{pet}, I can't wait to meet you. I just need help with {need}. Could you send {amount}?",
        ],
        "slots": {
            "pet": ["love", "darling", "sweetheart", "dear"],
            "stuck": ["stuck at the airport", "held at the border", "stranded abroad"],
            "who": ["Customs", "The hotel", "The airline"],
            "release": ["they release my bags", "I can leave", "I can fly home"],
            "when": ["when I land", "next week", "as soon as my account unfreezes"],
            "need": ["the flight ticket", "the visa fee", "the hospital bill"],
        },
    },
    "prize or lottery": {
        "in_corpus": "yes (prize or lottery fee)",
        "seeds": [
            ("English", "Congratulations! Your number won {amount} in the international lucky draw. Pay the processing fee to claim your prize."),
            ("English", "You are today's winner of a brand new car in our anniversary contest. Reply with your bank details to receive it."),
            ("English", "Lucky customer! Spin the wheel at {link} and claim your free smartphone, only delivery charges apply."),
            ("English", "Your email was picked in the global promotion. To release the funds, contact the claims agent on {phone}."),
            ("English", "Lucky winner: you won a cash prize. Pay tax of {amount} first to transfer the prize money."),
            ("Hinglish", "Badhai ho! Aapne {amount} ki lottery jeeti hai. Inaam ke liye pehle processing fee bhejiye."),
            ("Manglish", "Abhinandanangal! Ningal {amount} lottery jayichu. Sammanam kittan aadyam processing fee ayakkuka."),
            ("English", "Hi, you've been selected for a loyalty reward from a shopping festival. No rush, just confirm your address and we'll arrange it."),
        ],
        "templates": [
            "Congratulations! You won {prize} in the {contest}. {ask}",
            "{contest} result: you are a winner of {prize}. To claim, {ask_short} {deadline}.",
        ],
        "slots": {
            "prize": ["a car", "a smartphone", "a cash prize", "a holiday package", "a gold coin"],
            "contest": ["lucky draw", "anniversary contest", "festival bumper", "global promotion"],
            "ask": ["Pay the processing fee to claim it.", "Reply with your bank details.", "Claim at [LINK] before it expires."],
            "ask_short": ["pay the release fee", "share your account number", "pay the delivery charge"],
            "deadline": ["today", "within 24 hours", "before midnight"],
        },
    },
    "fake CAPTCHA paste-command": {
        "in_corpus": "no",
        "seeds": [
            ("English", "Verify you are human: follow the 3 steps shown and run the command this page has copied for you to continue to the document."),
            ("English", "To view the shared invoice, complete the robot check by running the verification command we copied to your clipboard."),
            ("English", "Robot check failed. Open your system's run tool and paste the fix we copied, then it will restore your access."),
            ("English", "Your browser needs a manual update to show this file. Run the copied script to finish the update."),
            ("English", "Security verification required: complete the on-screen steps and run the copied command to prove you are not a bot."),
            ("Hinglish", "Aap insaan ho ye verify karne ke liye screen ke steps follow karo aur copy kiya hua command chalao."),
            ("Manglish", "Ningal bot alla ennu verify cheyyan screen il kaanunna steps cheythu copy cheyta command run cheyyuka."),
            ("English", "Human check: this site copied a short code for you. Run it in your device's command tool to unlock the page."),
        ],
        "templates": [
            "{check}: to continue, run the command this page copied for you. {reason}",
            "To {goal}, complete the verification by running the copied {thing}. It only takes a second.",
        ],
        "slots": {
            "check": ["Human verification", "Robot check", "Security check", "Are you human?"],
            "reason": ["It confirms you are not a bot.", "This unlocks the document.", "The page won't load otherwise."],
            "goal": ["view the file", "watch the video", "open the invoice", "join the meeting"],
            "thing": ["command", "code", "script", "fix"],
        },
    },
    "deepfake CEO video call": {
        "in_corpus": "no",
        "seeds": [
            ("English", "You'll get a short video call from me now, don't worry it's really me. I need an urgent wire transfer handled quietly before the deal leaks."),
            ("English", "As you saw on our video call, this acquisition is confidential. Transfer {amount} to the vendor account I shared and tell no one."),
            ("English", "Join the quick video briefing. Afterwards process the payment to the new supplier, the board has already approved it."),
            ("English", "This is the MD. The call dropped, but as I said on screen, send the funds today, I'm authorising it personally."),
            ("English", "Confidential: finance must release {amount} before 4pm for the merger. I confirmed this with you face to face just now."),
            ("Hinglish", "Abhi video call pe maine bola tha na, wo payment urgent hai. {amount} naye vendor account mein bhej do, kisi ko mat batana."),
            ("Manglish", "Ippo video call il njan paranja pole, aa payment urgent aanu. {amount} puthiya vendor account ilekku ayakku, aarodum parayalle."),
            ("English", "Hi, the chairman here. After our video chat, please action the transfer we discussed. Keep it off the group email for now."),
        ],
        "templates": [
            "As we discussed on the video call, {task}. Transfer {amount} to {account} {when} and keep it confidential.",
            "This is {role}. {reason} Process the payment of {amount} {when}; I've authorised it personally.",
        ],
        "slots": {
            "task": ["the deal must close today", "the vendor needs paying", "the merger is confidential"],
            "account": ["the new supplier account", "the account I shared", "the escrow account"],
            "when": ["today", "before 4pm", "in the next hour"],
            "role": ["the MD", "the chairman", "the finance director", "your CEO"],
            "reason": ["The acquisition is confidential.", "The board already approved it.", "The deal leaks if we wait."],
        },
    },
    "crypto airdrop or wallet drainer": {
        "in_corpus": "partly (investment or crypto scam)",
        "seeds": [
            ("English", "Free airdrop! You are eligible for {amount} in tokens. Connect your wallet at {link} to claim before today's deadline."),
            ("English", "Your wallet qualifies for an exclusive NFT drop. Verify it by connecting at {link} and approve the transaction."),
            ("English", "Claim your staking rewards now. Link your wallet at {link}, the pool closes tonight."),
            ("English", "Support team: we noticed a failed transfer. To restore your balance, share your wallet recovery phrase with our agent."),
            ("English", "Limited airdrop for early users. Connect your wallet and sign the message to receive your coins."),
            ("Hinglish", "Free crypto airdrop! {link} pe wallet connect karo aur coins claim karo, aaj last din hai."),
            ("Manglish", "Free crypto airdrop! {link} il wallet connect cheythu coins claim cheyyuka, innu avasana divasam."),
            ("English", "Congrats, you were selected for a token giveaway. Just connect your wallet and approve to receive them."),
        ],
        "templates": [
            "{offer} Connect your wallet at {link} and {action} to receive {amount}.",
            "To restore your wallet, {recovery} with our support agent. {urgency}",
        ],
        "slots": {
            "offer": ["Free airdrop!", "Exclusive NFT drop!", "Staking rewards unlocked!", "Early-user token giveaway!"],
            "action": ["approve the transaction", "sign the message", "verify your balance"],
            "recovery": ["share your recovery phrase", "enter your seed words at [LINK]", "confirm your private key"],
            "urgency": ["The pool closes tonight.", "Offer ends today.", "Only the first 500 wallets qualify."],
        },
    },
    "fake scholarship or exam results": {
        "in_corpus": "no",
        "seeds": [
            ("English", "Congratulations, you qualified for the national merit scholarship of {amount}. Pay the application fee to confirm your seat."),
            ("English", "Your exam results are ready. Download the official result app and pay {amount} to unlock your scorecard."),
            ("English", "Government scholarship approved for your course. Share your bank OTP so we can deposit the grant directly."),
            ("English", "Last date to claim your education grant is today. Register at {link} with your card details."),
            ("English", "You've been selected for a study-abroad scholarship. A refundable processing fee of {amount} secures your offer."),
            ("Hinglish", "Aapko scholarship mili hai. Seat confirm karne ke liye {amount} application fee bhejein."),
            ("Manglish", "Ningalkku scholarship kitti. Seat urappikkan {amount} application fee adakkuka."),
            ("English", "Hi, the results portal shows you passed with distinction. Verify your identity by sharing the OTP we just sent."),
        ],
        "templates": [
            "{body}: you qualified for {award} of {amount}. {ask}",
            "Your {thing} is ready. {ask_short} at {link} to view it.",
        ],
        "slots": {
            "body": ["Scholarship cell", "Education board", "Grants office", "University admissions"],
            "award": ["a merit scholarship", "a study-abroad grant", "an education grant", "a fee waiver"],
            "ask": ["Pay the application fee to confirm.", "Share your bank OTP to receive it.", "Register with your card details."],
            "thing": ["exam result", "scorecard", "merit certificate", "admission letter"],
            "ask_short": ["Pay the unlock fee", "Verify your card", "Share the OTP"],
        },
    },
    "rental or booking deposit": {
        "in_corpus": "no",
        "seeds": [
            ("English", "Great, the flat is available for your dates. To hold it, send the deposit of {amount} now; I have other interested tenants."),
            ("English", "I'm abroad so I can't show the apartment, but pay the first month via the agency link and I'll courier the keys: {link}"),
            ("English", "Your holiday villa booking is confirmed once you transfer the security deposit today. The listing site will refund it later."),
            ("English", "Thanks for your interest in the room. The landlord asks for a token advance to block it before the weekend."),
            ("English", "To confirm your cab/hotel booking, pay the refundable deposit to this account; you'll get a confirmation code."),
            ("Hinglish", "Flat available hai. Hold karne ke liye {amount} deposit abhi bhej do, aur log bhi puchh rahe hain."),
            ("Manglish", "Flat available aanu. Hold cheyyan {amount} deposit ippo ayakku, vere aalukalum chodikkunnu."),
            ("English", "Hi, saw you liked the apartment. I'm out of town for work, but if you send a small holding deposit I'll reserve it for you."),
        ],
        "templates": [
            "The {place} is available. To hold it, send the {fee} of {amount} {when}; {pressure}.",
            "I'm {away}, so pay the {fee} via {link} and I'll {deliver}.",
        ],
        "slots": {
            "place": ["flat", "room", "holiday villa", "studio", "PG"],
            "fee": ["deposit", "token advance", "security amount", "holding fee"],
            "when": ["now", "today", "before the weekend"],
            "pressure": ["I have other tenants interested", "it won't last long", "several people asked"],
            "away": ["abroad for work", "out of town", "travelling this month"],
            "deliver": ["courier the keys", "send the agreement", "arrange the handover"],
        },
    },
    "social-media verify-your-account DM": {
        "in_corpus": "no",
        "seeds": [
            ("English", "Your account has been flagged for review. Verify now at {link} within 24 hours or it will be permanently disabled."),
            ("English", "We noticed a copyright complaint on your page. Appeal here to avoid suspension: {link}"),
            ("English", "You're eligible for the blue verification badge! Confirm your login details at {link} to activate it."),
            ("English", "Unusual login detected on your profile. Secure it by confirming your password and the code we sent."),
            ("English", "Your page violated community guidelines. Submit a review form with your login to restore it."),
            ("Hinglish", "Aapka account review mein hai. 24 ghante mein {link} pe verify karo warna permanently band ho jayega."),
            ("Manglish", "Ningalude account review il aanu. 24 manikkoor il {link} il verify cheyyuka, illenkil permanent aayi block aakum."),
            ("English", "Hi, this is page support. To keep your verified status, re-confirm your email and password through our secure form."),
        ],
        "templates": [
            "{problem} on your account. {action} at {link} {deadline} or it will be {consequence}.",
            "You're eligible for {perk}! Confirm your {detail} at {link} to activate it.",
        ],
        "slots": {
            "problem": ["A copyright complaint", "An unusual login", "A guidelines violation", "A review flag"],
            "action": ["Verify now", "Appeal here", "Secure your account", "Submit the form"],
            "deadline": ["within 24 hours", "today", "before it's locked"],
            "consequence": ["permanently disabled", "suspended", "deleted"],
            "perk": ["the verification badge", "creator monetisation", "a blue tick"],
            "detail": ["login details", "email and password", "account information"],
        },
    },
}
