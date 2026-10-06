"""Scam seeds, part 1 of 3 (written fresh for the fast routine; not the eval/ seeds).

Each category: about 8 hand-written seeds as (language, text) plus 2 slot
templates. Every seed and every template becomes one template_family, kept
inside a single round. {slots} are filled with fake placeholders only:
reserved-domain links or [LINK], [PHONE], fictional names and brands.

"in_corpus" says whether similarity/corpus.py already has a matching
category ("yes", "partly" (a related one), or "no").
"""

SCAM_A = {
    "AI voice-clone family emergency": {
        "in_corpus": "partly (family emergency or new-number scam)",
        "seeds": [
            ("English", "Mum it's me, I'm calling from a friend's phone, the police stopped me and I need {amount} for a fine right now. Please don't call Dad."),
            ("English", "Dad, this is the voice note I promised, I'm stuck at the station without my wallet. Send {amount} to my friend's account, I'll explain later."),
            ("English", "Hi Grandma, it's {name}. I had a small accident with the car, I'm okay but the other driver wants cash today. Can you help?"),
            ("English", "Aunty it's me, my voice sounds odd because I've got a cold. I need a small loan till Friday, could you transfer it to this new account?"),
            ("English", "It's me, please listen to the voice message. I'm in hospital and they won't start treatment until {amount} is paid. Don't tell anyone yet."),
            ("Hinglish", "Papa main bol raha hoon, mera phone toot gaya. Police ne pakda hai, abhi {amount} bhejo is number pe, mummy ko mat batana."),
            ("Manglish", "Amma, njan aanu, ente phone poyi. Oru accident undayi, ippo thanne {amount} venam, ee account ilekku ayakku, achanodu parayalle."),
            ("English", "Hey, it's your nephew. Recording this quickly, I've lost my bag abroad. Can you send something for a ticket home? I'll pay back next week."),
        ],
        "templates": [
            "{relative}, it's me, {name}. My phone {problem}, so I'm on a friend's number. I need {amount} for {reason}, can you send it {when}?",
            "Voice message from {name}: {relative}, I'm in trouble, {reason}. Please transfer {amount} to the account I'll text you and keep it between us.",
        ],
        "slots": {
            "relative": ["Mum", "Dad", "Grandma", "Grandpa", "Aunty", "Uncle"],
            "problem": ["got smashed", "fell in the river", "was stolen", "stopped working"],
            "reason": ["a hospital deposit", "a lawyer", "bail", "a fine at the airport", "a tow truck"],
            "when": ["now", "in the next hour", "before tonight", "today"],
        },
    },
    "digital arrest": {
        "in_corpus": "partly (tax or government threat)",
        "seeds": [
            ("English", "This is Inspector {name} from the Cyber Crime Cell. A parcel in your name contained illegal items. Stay on this video call and do not disconnect or you will be arrested."),
            ("English", "Your Aadhaar number has been linked to a money-laundering case. You are under digital arrest until verification. Do not speak to family members."),
            ("English", "Notice from the investigation bureau: a warrant has been issued against you. To avoid arrest, transfer your savings to the RBI verification account for checking."),
            ("English", "Sir, I am calling from customs and the narcotics team. Keep your camera on. Any attempt to call a lawyer will be treated as obstruction."),
            ("English", "You must remain at home on this call while we verify your accounts. Move your funds to the secure government account; it will be returned in 24 hours."),
            ("Hinglish", "Main CBI officer bol raha hoon. Aapke naam pe case darj hai. Video call band mat karna, warna turant giraftari hogi. Kisi ko kuch mat batana."),
            ("Manglish", "Njan cyber police il ninnu aanu. Ningalude per il oru case undu. Video call cut cheyyaruthu, illenkil arrest cheyyum. Veettil aarodum parayaruthu."),
            ("English", "Final warning from the cyber police: your number was used in a fraud. Pay the security deposit of {amount} to clear your name today."),
        ],
        "templates": [
            "This is {officer} from the {agency}. {accusation} Stay on this call, do not tell anyone, and transfer {amount} to the verification account.",
            "{agency} notice: {accusation} You are under digital arrest. Keep the video on and follow instructions or a warrant will be issued.",
        ],
        "slots": {
            "officer": ["Inspector Rao", "Officer Mehta", "Agent Kumar", "Sub-inspector Das"],
            "agency": ["Cyber Crime Cell", "narcotics bureau", "customs investigation team", "central investigation agency"],
            "accusation": ["A parcel in your name contained drugs.", "Your bank account was used for money laundering.",
                           "Your SIM card is linked to a fraud case.", "Your ID was used to open fake accounts."],
        },
    },
    "fake e-challan": {
        "in_corpus": "no",
        "seeds": [
            ("English", "Traffic e-challan: your vehicle was caught over-speeding. Pay the fine of {amount} at {link} within 24 hours to avoid court."),
            ("English", "Your challan is pending for signal jumping. Download the attached e-challan app to view the photo and pay."),
            ("English", "RTO notice: unpaid parking fine on your car. Clear it today at {link} or your licence will be suspended."),
            ("English", "Hi, a traffic camera recorded your vehicle without a helmet. View and settle the challan here: {link}"),
            ("English", "Dear vehicle owner, a fine is registered against your number plate. To check details, reply with your registration and card number."),
            ("Hinglish", "Aapki gaadi ka challan pending hai. Aaj hi {link} pe {amount} bharein warna licence block ho jayega."),
            ("Manglish", "Ningalude vandikku oru challan undu. Innu thanne {link} il {amount} adakkuka, illenkil licence suspend aakum."),
            ("English", "We noticed an unpaid toll violation linked to your vehicle. A small late fee applies after today. Settle it when you get a moment: {link}"),
        ],
        "templates": [
            "{authority}: e-challan {challan_no} for {offence}. Pay {amount} at {link} {deadline}.",
            "Your vehicle has a pending fine for {offence}. Open {link} to view the camera photo and pay {deadline}.",
        ],
        "slots": {
            "authority": ["Traffic Police", "RTO", "Transport Department", "City traffic cell"],
            "challan_no": ["no. 48213", "ref 77120", "no. 30951"],
            "offence": ["over-speeding", "jumping a red light", "no seat belt", "wrong parking", "no helmet"],
            "deadline": ["within 24 hours", "today", "before midnight", "to avoid court"],
        },
    },
    "QR-code scam": {
        "in_corpus": "no",
        "seeds": [
            ("English", "Hi, I'm buying your sofa from the listing. I've sent a QR code, just scan it and enter your UPI PIN to receive the payment."),
            ("English", "Parking meter notice: this machine is out of order. Scan the QR sticker to pay and register your card."),
            ("English", "To get your cashback of {amount}, scan the QR code in this message and approve the request."),
            ("English", "Your restaurant bill can be split here, just scan the QR code and enter your card details to confirm."),
            ("English", "Scan this code to confirm delivery of your parcel and pay a small handling charge."),
            ("Hinglish", "Bhaiya maine QR bheja hai, scan karke UPI PIN daal do, paise aapke account mein aa jayenge."),
            ("Manglish", "Chetta, njan QR ayachittundu, scan cheythu UPI PIN adichal paisa ningalude account il varum."),
            ("English", "EV charging point upgrade: the old payment reader is gone. Scan the new code on the charger to start and save your card."),
        ],
        "templates": [
            "I'm interested in your {item}. I've sent you a QR code, scan it and enter your PIN to receive {amount}.",
            "{place} notice: scan the QR code to {action}. Enter your card or UPI PIN to confirm.",
        ],
        "slots": {
            "item": ["bicycle", "old phone", "dining table", "guitar", "fridge"],
            "place": ["Parking", "Car wash", "Charging station", "Hostel mess"],
            "action": ["pay for your session", "claim your refund", "get your deposit back", "unlock the service"],
        },
    },
    "task or like-and-earn": {
        "in_corpus": "partly (job or advance-fee scam)",
        "seeds": [
            ("English", "Earn {amount} a day by liking videos from home! Just 15 minutes. Message us on the app to start your first task."),
            ("English", "Congratulations, you completed 3 tasks. To unlock the next level and withdraw your earnings, deposit {amount} first."),
            ("English", "Part-time job: rate hotels online and earn commission. No experience needed. Join our group: {link}"),
            ("English", "Your task balance is frozen because of a wrong rating. Recharge {amount} to restore it and get your profit back."),
            ("English", "We pay for every product review you post. Join today, the first 3 tasks are free and paid instantly."),
            ("Hinglish", "Ghar baithe video like karo aur roz {amount} kamao. Pehle task ke baad thoda recharge karna hoga, phir bada profit."),
            ("Manglish", "Veettil irunnu video like cheythu divasavum {amount} undaakkam. Next task nu munpu cheriya recharge venam."),
            ("English", "Hi, I'm a recruiter for a digital marketing team. Simple online tasks, paid daily. Interested? No fees mentioned until you reach VIP."),
        ],
        "templates": [
            "Earn {amount} daily by {task}. {hook} Join here: {link}",
            "Task {task_no} done! Your earnings are on hold. Deposit {amount} to {unlock} and withdraw everything.",
        ],
        "slots": {
            "task": ["liking videos", "rating hotels", "writing short reviews", "following pages", "watching ads"],
            "hook": ["No experience needed.", "Only 20 minutes a day.", "Paid every evening.", "Students welcome."],
            "task_no": ["3", "5", "8", "12"],
            "unlock": ["unlock VIP level", "release your commission", "complete the merchant task", "restore your account"],
        },
    },
    "fake job offer with upfront fee": {
        "in_corpus": "yes (job or advance-fee scam)",
        "seeds": [
            ("English", "Congratulations! You are shortlisted for the data entry role, {amount} a month. Pay the registration fee to receive your offer letter."),
            ("English", "Your interview is cleared. Please deposit the refundable laptop security amount before joining on Monday."),
            ("English", "We are hiring for an airline ground staff position. Selection is confirmed; send {amount} for uniform and training kit."),
            ("English", "Hello, overseas job opening in a hotel. Visa processing fee of {amount} is required before we book your interview."),
            ("English", "You've been selected for work from home. To activate your employee ID, pay the onboarding charge at {link}."),
            ("Hinglish", "Aapka selection ho gaya hai. Joining ke liye {amount} document verification fee jama karna hoga, phir offer letter milega."),
            ("Manglish", "Ningale joliku select cheythu. Offer letter kittan {amount} verification fee adakkanam."),
            ("English", "Good news, your profile matches a remote assistant job. Small background check fee first, then we schedule the call."),
        ],
        "templates": [
            "You are selected for the {role} role at {company}. Pay the {fee} of {amount} {when} to confirm your joining.",
            "{company} HR: your offer for {role} is ready. A {fee} is needed before the first day. Pay at {link}.",
        ],
        "slots": {
            "role": ["data entry", "customer support", "warehouse supervisor", "content writer", "receptionist"],
            "company": ["Brightpath Services", "Northstar Staffing", "Clearview Jobs", "Summit Hiring"],
            "fee": ["registration fee", "security deposit", "training fee", "ID card fee", "verification charge"],
            "when": ["today", "within 48 hours", "before joining", "by Friday"],
        },
    },
    "wrong-number crypto investment": {
        "in_corpus": "partly (investment or crypto scam)",
        "seeds": [
            ("English", "Hi, is this Mr {name}? Sorry, wrong number! Anyway, you seem nice. I do some crypto trading as a hobby, want me to show you?"),
            ("English", "Oops, sent to the wrong person. Since we're chatting, my uncle taught me a trading method that made me {amount} last month."),
            ("English", "Sorry, I thought this was my yoga teacher's number. What do you do for work? I invest in digital currency on the side."),
            ("English", "Hello, are we still meeting for golf on Sunday? Oh, wrong number. Nice to meet you anyway, I'm in finance."),
            ("English", "I made a deposit on the platform I told you about and already doubled it. Start small, just {amount}, I'll guide you."),
            ("Hinglish", "Sorry galat number lag gaya. Waise aap kya karte ho? Main crypto trading karti hoon, achha profit hai, sikhaun?"),
            ("Manglish", "Sorry, wrong number aayi. Ningal enthu cheyyunnu? Njan crypto trading cheyyunnu, nalla laabham undu, padippikkatte?"),
            ("English", "Good morning! You probably don't remember me, we chatted by mistake last week. My platform showed 30% today, want the link?"),
        ],
        "templates": [
            "Hi, is this {name}? Sorry, wrong number. {smalltalk} I trade {asset} and made {amount} last month, want to see how?",
            "{smalltalk} My mentor's {asset} platform is giving {returns}. Start with just {amount}, I'll send the link.",
        ],
        "slots": {
            "smalltalk": ["You seem friendly!", "Where are you based?", "Funny how these mistakes happen.", "Do you like travelling?"],
            "asset": ["crypto", "gold futures", "digital currency", "forex"],
            "returns": ["20% a week", "steady daily profit", "guaranteed returns", "double in a month"],
        },
    },
    "AI trading-bot group": {
        "in_corpus": "partly (investment or crypto scam)",
        "seeds": [
            ("English", "Welcome to the AI Quant Signals group! Our trading bot made 300% this quarter. Deposit {amount} to get the VIP signals."),
            ("English", "Our artificial intelligence robot trades for you 24/7. Members withdraw profit daily. Minimum entry {amount}."),
            ("English", "Join our stock tips group led by a famous market professor. Free today, limited seats: {link}"),
            ("English", "Screenshot from member: made {amount} in one week with the bot! Ask the admin how to open your account."),
            ("English", "Your trial account shows a profit. To withdraw, upgrade to the institutional plan with a one-time payment."),
            ("Hinglish", "AI trading bot se roz profit kamao. Group join karo, admin aapka account khol denge. Minimum {amount}."),
            ("Manglish", "AI trading bot divasavum laabham tharum. Group il join cheyyu, admin account open cheythu tharum. Minimum {amount}."),
            ("English", "Hi, you were added to our learning community for investors. No pressure, we share market lessons and a smart bot's picks every morning."),
        ],
        "templates": [
            "Welcome to {group}! Our AI bot returned {returns}. Deposit {amount} to unlock {tier}.",
            "{group} update: the bot closed another winning week. Members in {tier} earned {returns}. Message the admin to join.",
        ],
        "slots": {
            "group": ["AI Quant Club", "Smart Signals VIP", "RoboTrade Circle", "Alpha Bot Investors"],
            "returns": ["40% this month", "300% this quarter", "steady daily profit", "guaranteed weekly gains"],
            "tier": ["VIP signals", "the institutional plan", "premium access", "the gold tier"],
        },
    },
    "instant-loan harassment": {
        "in_corpus": "no",
        "seeds": [
            ("English", "Instant loan of {amount} approved, no documents! Install the app and allow access to contacts and gallery to receive the money."),
            ("English", "Your loan is overdue by 1 day. Pay {amount} now or we will send your photos to everyone in your contact list."),
            ("English", "Final reminder from the loan app: repay today or we will call your family and employer about your default."),
            ("English", "You took a loan of 3,000 and must repay 6,500 within 7 days. Late fees apply every hour."),
            ("English", "Pre-approved personal loan, credited in 5 minutes. Pay a small processing fee first to release it."),
            ("Hinglish", "Aapka loan due hai. Aaj {amount} nahi bhara to aapke saare contacts ko message bhej denge."),
            ("Manglish", "Ningalude loan due aanu. Innu {amount} adachillenkil ningalude ella contacts num message ayakkum."),
            ("English", "Hi, quick loans for students available, no credit check. Just download the app and give the permissions it asks for."),
        ],
        "templates": [
            "{lender}: {offer} Install the app and allow {permission} to receive {amount}.",
            "{lender} recovery team: your repayment is {late}. Pay {amount} now or we will {threat}.",
        ],
        "slots": {
            "lender": ["QuickCash", "LoanNow", "RupeeFast", "EasyCredit"],
            "offer": ["Instant loan approved!", "Pre-approved loan, no documents.", "Get money in 5 minutes."],
            "permission": ["contacts access", "gallery and contacts", "SMS and contacts"],
            "late": ["1 day late", "overdue", "overdue by 2 hours", "in default"],
            "threat": ["message all your contacts", "call your employer", "share your photos", "post your details online"],
        },
    },
}
