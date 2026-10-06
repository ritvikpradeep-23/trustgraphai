"""Hand-written scam seeds for the evaluation set.

Every message is fictional. Placeholders in {braces} are filled by the
generator with safe fakes: reserved-domain links (example.com, .test,
.invalid), [PHONE], fictional names and brands, and amounts.

"seen" categories exist in the engine's reference corpus
(src/trustgraph/similarity/corpus.py) under the same name; their wording here
is new. "unseen" categories have no reference examples at all.
"""

SCAM = {
    # ---------------------------------------------------------------- seen
    "bank safe-account scam": {
        "novelty": "seen",
        "seeds": [
            "Hi, {name} from {bank}'s security desk. Someone has tried to log in from overseas. We've opened a protected account for you, please move your balance there now.",
            "{bank} alert: your savings are at risk. Our fraud officer will call you to help transfer funds into a secure holding account.",
            "We've frozen suspicious payments on your account. To stop further loss, shift your money to the new safe account number we text you.",
            "This is the fraud prevention line. A staff member at your branch is under investigation, so don't speak to them. Transfer your savings to the account I give you.",
            "Your debit card was cloned an hour ago. Please keep your money safe by moving it to a temporary vault account until the investigation ends.",
            "Urgent from {bank}: unusual activity detected. Call {phone} so we can secure your funds in a protected account today.",
            "I'm calling from your bank's investigations team. For your protection, withdraw your savings and deposit them into the safe account we've set up.",
            "Security notice: hackers are inside your online banking. Move everything to the protected account below before they empty it.",
        ],
        "hinglish": [
            "Namaste, main {bank} fraud team se bol raha hoon. Aapke account mein hacking hui hai, apna paisa abhi safe account mein transfer kar dijiye.",
            "Sir aapke account se suspicious transaction ho raha hai, paise turant hamare secure account mein bhejo warna sab chala jayega.",
        ],
        "manglish": [
            "Sir, njan {bank} security team il ninnaanu vilikkunnathu. Ningalude account hack aayi, paisa ippo thanne safe account ilekku maattanam.",
            "Ningalude card clone cheythittundu. Paisa surakshithamaayi vekkan njangal tharunna account ilekku transfer cheyyuka.",
        ],
        "templates": [
            "{greet} this is {bank}'s {team}. {problem} Please {move} into the {safe} we've {setup}.",
            "{bank}: {problem} To protect your money, {move} to a {safe} today. Questions: {phone}",
        ],
        "slots": {
            "greet": ["Hello,", "Good evening,", "Hi there,", "Dear customer,"],
            "team": ["fraud team", "security department", "investigations unit", "account protection desk"],
            "problem": ["Your account has been accessed from a new device.", "We blocked a payment of {amount} to an unknown merchant.",
                        "Criminals have your login details.", "Your card details were found on a fraud list."],
            "move": ["transfer your balance", "move your savings", "shift your funds", "send your money"],
            "safe": ["safe account", "secure account", "protected account", "holding account"],
            "setup": ["opened for you", "set up in your name", "prepared", "created this morning"],
        },
    },
    "gift-card request from a boss or colleague": {
        "novelty": "seen",
        "seeds": [
            "Hey, are you around? I'm stuck in a board meeting and need you to grab some gift cards for a client. I'll explain later.",
            "Quick favour please, buy three {store} cards of {amount} each and send me the codes. Can't take calls right now.",
            "It's {name}. I need some store cards for staff awards today, keep it between us, it's a surprise. Send pictures of the backs.",
            "Are you free? I need you to purchase {store} gift cards urgently, I'll reimburse you tonight. Reply ASAP.",
            "Can you do something for me discreetly? Pick up gift cards on your way in and text me the redemption numbers.",
            "I'm travelling and my card isn't working. Could you buy two {store} vouchers and send me the codes? Thanks, {name}",
            "Need a hand with a client thank-you. Get {amount} in {store} cards, scratch the silver panel and send me photos.",
            "Hi, it's your manager. Are you at your desk? Small errand: gift cards for a supplier, I'll pay you back by Friday.",
        ],
        "hinglish": [
            "Hi, main meeting mein hoon, call nahi kar sakta. {store} ke gift cards le lo aur codes mujhe WhatsApp kar do, please urgent hai.",
            "Ek kaam karo, 4 gift cards kharid lo client ke liye, aur scratch karke photo bhejo. Kisi ko mat batana abhi.",
        ],
        "manglish": [
            "Hi, njan meeting il aanu, vilikkan pattilla. Kurachu {store} gift cards vaangi codes ayachu tharamo? Urgent aanu.",
        ],
        "templates": [
            "{opener} {busy} Could you {buy} {count} {store} gift cards {purpose}? {send}",
            "{opener} it's {name}. {busy} I need {count} {store} cards {purpose}. {send} {secret}",
        ],
        "slots": {
            "opener": ["Hi,", "Hey,", "Are you free?", "Quick one,"],
            "busy": ["I'm in back-to-back meetings.", "I'm on a call with the board.", "I'm at the airport.", "Can't talk right now."],
            "buy": ["buy", "pick up", "get", "grab"],
            "count": ["two", "three", "four", "five"],
            "purpose": ["for a client", "for staff rewards", "for a supplier", "for a charity event"],
            "send": ["Send me the codes.", "Text me photos of the backs.", "Email me the card numbers.", "Reply with the codes."],
            "secret": ["Keep it quiet for now.", "Don't mention it to the team.", "It's a surprise.", ""],
        },
    },
    "invoice or bank-details change": {
        "novelty": "seen",
        "seeds": [
            "Hello, following a change of banking partner, please send all future payments to our new account. Updated details attached.",
            "Please be advised our old account is no longer active. Kindly pay invoice {code} to the replacement account below.",
            "Our accounts team has moved to a new bank this month. Use the sort code and account number in this email for the outstanding balance.",
            "Due to an internal audit, payments to our usual account are paused. Please remit to the alternative account we've provided.",
            "Update your supplier records: our bank details changed on Monday. Today's payment should go to the new account.",
            "Reminder: invoice {code} is overdue. Note we've switched banks, so please don't use the account on file.",
            "Hi, quick admin note from {company} finance. We've changed our receiving account; please confirm once you've updated it.",
            "For security reasons we've rotated our bank account. Kindly settle the attached invoice to the new details today.",
        ],
        "hinglish": [
            "Sir hamara bank account change ho gaya hai, is mahine ki payment naye account mein bhejiye. Details neeche hain.",
        ],
        "manglish": [
            "Sir, njangalude bank account maari. Ee maasathe payment puthiya account ilekku ayakkanam, details thazhe undu.",
        ],
        "templates": [
            "{opener} {reason} Please {pay} invoice {code} to {newacct}. {closer}",
            "{company} accounts: {reason} {pay_cap} all payments to {newacct} from today.",
        ],
        "slots": {
            "opener": ["Hello,", "Dear partner,", "Hi team,", "Good morning,"],
            "reason": ["Our bank details have changed.", "We've moved to a new bank.", "Our previous account is closing.", "Our finance department changed banks."],
            "pay": ["pay", "settle", "remit", "transfer"],
            "pay_cap": ["Please send", "Kindly make", "Route", "Direct"],
            "newacct": ["the new account below", "our updated account", "the account in the attachment", "the details in this email"],
            "closer": ["Thanks, Accounts.", "Regards, Finance.", "Many thanks.", "Best wishes."],
        },
    },
    "family emergency or new-number scam": {
        "novelty": "seen",
        "seeds": [
            "Mum it's me, I broke my phone so this is my new number. I'm in a bit of trouble, can you help me pay something today?",
            "Dad, please don't be angry. I'm stuck and need money for a bill, my banking app won't work on this new phone.",
            "Hi it's me, lost my phone, using this number now. Can you send me {amount}? I'll explain when I see you.",
            "Grandpa it's your grandson, I had an accident and the police are here. I need money for the fine, please don't tell anyone.",
            "Mom, I'm calling from a friend's phone. I need help urgently, can you transfer some money to this account?",
            "Hey it's your daughter, new number! I need to pay my rent today and my card's been blocked. Can you cover it?",
            "It's me, I know my voice sounds weird, bad signal. I'm in hospital abroad and they want payment before treatment.",
            "Hiya, this is my new number, delete the old one. Can you do me a favour and pay a bill for me today? I'll pay you back Friday.",
        ],
        "hinglish": [
            "Mummy main hoon, mera phone toot gaya, ye naya number hai. Ek urgent payment karni hai, thode paise bhej do please.",
            "Papa mera accident ho gaya hai, abhi paisa chahiye, kisi ko mat batana, is account mein bhej do.",
        ],
        "manglish": [
            "Amma, njan aanu, ente phone poyi, ithu puthiya number aanu. Oru urgent payment undu, kurachu paisa ayachu tharamo?",
            "Achaa, oru problem undu, ippo thanne kurachu paisa venam. Aarodum parayalle, ee account ilekku ayakku.",
        ],
        "templates": [
            "{who} it's me, {phonestory}. {need} {pay} {reassure}",
            "{who}, {phonestory}. {need} Can you {pay_low}? {reassure}",
        ],
        "slots": {
            "who": ["Mum", "Dad", "Hi Mum", "Hey Dad", "Nan", "Grandma"],
            "phonestory": ["this is my new number", "my phone fell in the river", "I'm on a friend's phone", "my old phone died"],
            "need": ["I need to pay a bill today.", "I'm short for rent.", "My card got blocked.", "I've got an urgent payment to make."],
            "pay": ["Can you send {amount}?", "Could you transfer it for me?", "Can you pay it to this account?"],
            "pay_low": ["send it for me", "pay it to this account", "help me out with {amount}"],
            "reassure": ["I'll pay you back tomorrow.", "Explain later x", "Please hurry.", "Love you."],
        },
    },
    "tech support remote-access scam": {
        "novelty": "seen",
        "seeds": [
            "This is the technical support centre. Your computer has been sending virus alerts to our server. Please install the support app so we can clean it.",
            "Warning: your device is infected. Call {phone} immediately and allow our technician to connect to your screen.",
            "Your internet subscription will be cancelled today because your router was hacked. Let me take control of your PC to fix it.",
            "Hello, I'm from the software licence team. Your licence expired and your files are at risk. Download the remote tool I send you.",
            "We noticed hackers using your IP address. Open the screen-sharing app and give me the six-digit session number.",
            "Your refund of {amount} is ready, but I need remote access to your laptop to process it. Please log in to your banking while connected.",
            "System alert: your PC is locked due to suspicious activity. Do not turn it off. Call our certified engineers on {phone}.",
            "Hi, calling about your antivirus renewal. To cancel the charge I'll need to connect to your computer remotely.",
        ],
        "hinglish": [
            "Sir aapke computer mein virus aa gaya hai, main remote se fix kar dunga, bas ye app install karke code bata dijiye.",
        ],
        "manglish": [
            "Sir, ningalude computer il virus undu. Ee app install cheythu code paranju tharoo, njan remote aayi fix cheyyam.",
        ],
        "templates": [
            "{alert} {threat} Please {install} so our {tech} can {fix}.",
            "{alert} {threat} Call {phone} and {allow}.",
        ],
        "slots": {
            "alert": ["Security warning:", "Support notice:", "Important:", "Device alert:"],
            "threat": ["Your computer is infected.", "Your router has been hacked.", "Your licence has expired and data is at risk.", "Hackers are using your account."],
            "install": ["install the remote support app", "download the screen-sharing tool", "open the remote desktop link {link}"],
            "tech": ["technician", "engineer", "support agent"],
            "fix": ["remove the virus", "secure your device", "restore your files"],
            "allow": ["let our engineer connect to your screen", "give us remote access", "share your screen with our technician"],
        },
    },
    "tax or government threat": {
        "novelty": "seen",
        "seeds": [
            "Final notice from the tax office: you owe back taxes and a legal case has been opened. Pay today to stop proceedings.",
            "Your tax ID has been flagged for fraud. Officers will visit your address unless you call {phone} within 2 hours.",
            "This is the revenue department. A penalty of {amount} is due immediately or a warrant will be issued.",
            "Notice of unpaid duty: settle the outstanding balance now at {link} to avoid court action.",
            "Your social security number has been suspended for suspicious activity. Press 1 to speak with an officer.",
            "The government has detected errors in your filing. Pay the fine by bank transfer today to avoid arrest.",
            "Immigration office: your residence permit has a problem. You must pay the processing charge today or face removal.",
            "Pension department alert: your payments will stop unless you confirm your details and pay the verification fee.",
        ],
        "hinglish": [
            "Income tax department se notice: aapka tax baaki hai, aaj payment nahi kiya to legal action hoga. Call karein {phone}.",
        ],
        "manglish": [],
        "templates": [
            "{office}: {issue} {deadline} {consequence}",
            "{office} notice. {issue} Pay at {link} {deadline}.",
        ],
        "slots": {
            "office": ["Tax office", "Revenue department", "Government notice", "Customs authority"],
            "issue": ["You have unpaid tax of {amount}.", "Your tax return contains a serious error.", "Your ID has been used in a fraud case.", "A penalty is outstanding on your file."],
            "deadline": ["Pay within 24 hours.", "Respond today.", "before 6pm today", "within 2 hours"],
            "consequence": ["A warrant will follow.", "Legal action will begin.", "Officers will visit you.", "Your accounts will be frozen."],
        },
    },
    "parcel or delivery fee": {
        "novelty": "seen",
        "seeds": [
            "{courier}: your parcel is waiting at our depot. A small redelivery charge is required, pay at {link}",
            "We couldn't deliver your package because of an incomplete address. Update it and pay {amount} here: {link}",
            "Customs has held your item. Import duty of {amount} must be paid within 48 hours or it will be returned.",
            "Your order is on hold. Confirm your card details to release the shipment: {link}",
            "{courier} notice: delivery failed. Reschedule now for a {amount} handling fee {link}",
            "Final reminder: your parcel will be destroyed tomorrow unless the storage fee is paid {link}",
            "Hi, your package from overseas needs a clearance payment before we can deliver it. Pay securely here {link}",
            "Your parcel has been returned to the warehouse. Pay the re-dispatch fee to receive it today: {link}",
        ],
        "hinglish": [
            "Aapka parcel hold par hai, address galat hai. {amount} delivery charge pay karke update karein: {link}",
        ],
        "manglish": [
            "Ningalude parcel depot il undu. Delivery cheyyan {amount} charge adakkanam, ee link il pay cheyyuka {link}",
        ],
        "templates": [
            "{courier}: {problem} {fee} {link}",
            "{problem} {fee} Pay here: {link} {urgency}",
        ],
        "slots": {
            "problem": ["Your parcel could not be delivered.", "Your package is held at customs.", "Delivery failed due to an address issue.", "Your shipment is on hold."],
            "fee": ["A fee of {amount} is due.", "Pay the {amount} redelivery charge.", "Import duty of {amount} applies.", "Confirm payment of {amount} to release it."],
            "urgency": ["within 24 hours", "today", "or it will be returned", ""],
        },
    },
    "investment or crypto scam": {
        "novelty": "seen",
        "seeds": [
            "Sorry, wrong number! Is this Lisa? ... Well, nice to meet you anyway. I actually work in crypto trading, my uncle taught me a strategy that never loses.",
            "Join our AI trading bot group, members made 40% this week. Start with {amount} and the bot does the rest.",
            "My mentor's platform gives guaranteed daily returns. I'll help you open an account, just deposit USDT to start.",
            "Hi, we met at the conference last year? I've been doing really well with a gold trading app, want me to show you?",
            "Exclusive signal group: we only accept 20 new investors this month. Double your money in 30 days, no risk.",
            "Your trading account shows {amount} profit. To withdraw it you need to pay the release tax first.",
            "I can't believe how much I've made on this new coin. Send me some crypto and I'll buy in for you before launch.",
            "Our quant fund uses artificial intelligence to beat the market. Minimum deposit {amount}, returns paid weekly.",
        ],
        "hinglish": [
            "Bhai ek trading app hai, roz 10% return deta hai, guaranteed. {amount} se start karo, main group mein add kar deta hoon.",
            "Hello, galti se message ho gaya, sorry. Waise main crypto trading karti hoon, aapko bhi sikha sakti hoon.",
        ],
        "manglish": [
            "Chetta, oru trading app undu, daily 10% profit kittum. {amount} invest cheythaal mathi, njan group il add cheyyam.",
        ],
        "templates": [
            "{hook} {platform} {returns} {ask}",
            "{hook} {returns} {ask}",
        ],
        "slots": {
            "hook": ["Sorry, wrong number!", "Hi, long time no see!", "I have exciting news.", "Are you interested in passive income?"],
            "platform": ["My uncle's trading platform", "Our AI bot", "This private investment group", "A new crypto exchange"],
            "returns": ["makes 30% a week.", "has guaranteed profits.", "never loses money.", "doubled my savings last month."],
            "ask": ["Deposit {amount} to start.", "Send USDT to the wallet I give you.", "Let me open an account for you.", "Join before spaces run out."],
        },
    },
    "romance scam money request": {
        "novelty": "seen",
        "seeds": [
            "Good morning my love. The base is quiet today. I wish I could leave this deployment early and finally hold you.",
            "Darling, my bank card was blocked overseas and I need to pay the hotel. Could you lend me {amount} until I'm home?",
            "I'm a doctor with the peacekeeping mission. My leave request needs a fee before they release me, can you help, sweetheart?",
            "You're the only person I trust. My daughter needs surgery and my funds are stuck in customs, please help us.",
            "Baby, the package with my savings is held at the airport and they want a clearance fee. I'll repay you double.",
            "I want to visit you next month but the flight is expensive with my accounts frozen. Could you help with the ticket?",
            "Since we met online my life has changed. I just need a small favour to get my inheritance released, then we can be together.",
            "My love, please receive a payment for me into your account and forward it on. My bank won't allow it from here.",
        ],
        "hinglish": [
            "Jaan, main yahan foreign mein phas gaya hoon, mera account freeze hai. Thode paise bhej do, wapas aake lauta dunga.",
        ],
        "manglish": [
            "Ente chakkare, njan ivide foreign il kudungi, account freeze aanu. Kurachu paisa ayachu tharamo? Thirichu tharaam.",
        ],
        "templates": [
            "{pet} {situation} {ask} {sweet}",
            "{pet} {sweet} {situation} {ask}",
        ],
        "slots": {
            "pet": ["My love,", "Darling,", "Sweetheart,", "Baby,"],
            "situation": ["I'm stuck overseas with my account frozen.", "My leave from the army needs a fee.", "Customs is holding my package.", "My hotel bill is overdue."],
            "ask": ["Could you send {amount}?", "Can you help me with the fee?", "Please lend me some money.", "Can you pay it for me?"],
            "sweet": ["I can't wait to meet you.", "You mean everything to me.", "Soon we'll be together.", "I trust only you."],
        },
    },
    "one-time code or password request": {
        "novelty": "seen",
        "seeds": [
            "Hi, I accidentally put your number in when signing up, can you forward the 6-digit code you just got?",
            "This is {bank}. To reverse the fraudulent charge, please read me the code we just sent by text.",
            "Your account verification is pending. Reply with the OTP sent to your phone to keep your account active.",
            "Hey, it's {name}. My phone's broken so the code went to you. Can you send it over quickly?",
            "To confirm the refund, I need the passcode that just arrived on your mobile.",
            "Security check: please tell the agent the verification code shown in your banking app.",
            "Your delivery is ready. Share the confirmation code we sent so the driver can release it.",
            "We're upgrading your SIM. Please reply with the code you receive in the next minute.",
        ],
        "hinglish": [
            "Sir aapke phone pe ek OTP aaya hoga, wo bata dijiye, refund process karna hai.",
            "Bhai galti se tera number daal diya, jo code aaya hai wo bhej de jaldi.",
        ],
        "manglish": [
            "Sir, ningalude phone il oru OTP vannittundu, athu onnu paranju tharamo? Refund process cheyyanam.",
        ],
        "templates": [
            "{who} {reason} {ask}",
            "{reason} {ask} {urgency}",
        ],
        "slots": {
            "who": ["Hi, it's {name}.", "This is {bank}.", "Customer care here.", "Hello from support."],
            "reason": ["I sent my code to your number by mistake.", "We need to verify your identity.", "To cancel the payment,", "Your account update is pending."],
            "ask": ["Can you forward me the code?", "please read out the 6-digit code we sent.", "reply with the OTP you just received.", "tell me the verification code."],
            "urgency": ["Quickly please.", "It expires soon.", "", "Thanks!"],
        },
    },
    "prize or lottery fee": {
        "novelty": "seen",
        "seeds": [
            "Congratulations! Your number was selected in our international draw. Claim your {amount} prize by paying the handling charge.",
            "You've won a brand-new smartphone! Just cover the delivery cost here: {link}",
            "Dear winner, your email won our annual sweepstakes. Contact our agent and pay the release fee to receive funds.",
            "Lucky customer! You've been chosen for a cash reward. Send your bank details and a small processing fee.",
            "An unclaimed inheritance of {amount} has been traced to you. Pay the legal fee to begin the transfer.",
            "You are today's winner of a shopping voucher worth {amount}. Pay a small fee to activate it: {link}",
            "Our records show you're entitled to a compensation payment. A one-time admin fee is required to release it.",
            "Spin the wheel result: you won a car! Confirm with a registration payment within 24 hours.",
        ],
        "hinglish": [
            "Badhai ho! Aapne {amount} ka lucky draw jeeta hai. Prize claim karne ke liye processing fee bharein: {link}",
        ],
        "manglish": [
            "Abhinandanangal! Ningal {amount} lucky draw jayichu. Prize kittan processing fee adakkuka: {link}",
        ],
        "templates": [
            "{congrats} {prize} {fee} {link}",
            "{congrats} {prize} {fee}",
        ],
        "slots": {
            "congrats": ["Congratulations!", "Dear winner,", "Lucky you!", "Good news!"],
            "prize": ["You won {amount} in our draw.", "You've been selected for a free phone.", "You're entitled to a cash prize.", "You won a holiday."],
            "fee": ["Pay the small release fee to claim.", "A delivery charge applies.", "Pay the processing fee today.", "Send the activation fee to receive it."],
        },
    },
    "job or advance-fee scam": {
        "novelty": "seen",
        "seeds": [
            "Hi! We found your profile and want to offer you a part-time role, 2 hours a day from home. Just pay for your starter pack to begin.",
            "Congratulations, you've been selected as a data entry assistant. A refundable onboarding fee of {amount} secures your place.",
            "Earn {amount} a week from home! Training materials cost a small amount upfront, refunded after your first payday.",
            "Your interview was successful. Before your first day, please pay the background verification charge.",
            "We need remote product reviewers. Buy the sample kit with your own money and we'll reimburse you with commission.",
            "Hello, our HR team has shortlisted you. To confirm the job offer, please transfer the security deposit.",
            "Work from home opportunity: receive payments into your account and forward them, keep 10% for yourself.",
            "You're hired! Equipment will be sent once you pay the delivery and setup charge.",
        ],
        "hinglish": [
            "Aapko work from home job mil gayi hai, roz {amount} kama sakte ho. Bas registration fee bharni hogi pehle.",
        ],
        "manglish": [
            "Ningalkku work from home job kitti, divasam {amount} undaakkaam. Aadyam registration fee adakkanam.",
        ],
        "templates": [
            "{offer} {pay} {refund}",
            "{offer} {pay}",
        ],
        "slots": {
            "offer": ["You've been selected for a remote job.", "Congratulations on your new position!", "We'd like to hire you as an online assistant.", "Earn {amount} weekly from home."],
            "pay": ["Please pay the onboarding fee to start.", "Transfer the security deposit to confirm.", "Pay for your training kit upfront.", "A verification charge is due before your first day."],
            "refund": ["It will be refunded with your first salary.", "Fully refundable.", "", "Reply to accept."],
        },
    },
    "blackmail or sextortion": {
        "novelty": "seen",
        "seeds": [
            "I know your password and I've been watching you through your camera. Pay me in bitcoin or the recording goes to your contacts.",
            "I have screenshots of the sites you visit. Send {amount} within 48 hours or your family and colleagues will see everything.",
            "Your device was infected weeks ago. I recorded you. If you don't pay, I'll share the video with all your friends.",
            "Do not ignore this. I have private photos of you. Transfer the money to the wallet below or I publish them.",
            "Hello pervert. I captured you on your webcam. You have two days to pay or I send the clip to your workplace.",
            "I got into your email and found your intimate pictures. Pay up or your boss gets a copy.",
            "This is your last warning. Send the bitcoin or the footage goes to everyone in your address book. Don't contact the police.",
            "I know what you did online. Pay {amount} in crypto and I will delete the evidence.",
        ],
        "hinglish": [
            "Mere paas tumhari private video hai. {amount} bhejo warna sabko bhej dunga, tumhare ghar walon ko bhi.",
        ],
        "manglish": [],
        "templates": [
            "{claim} {demand} {threat}",
            "{claim} {threat} {demand}",
        ],
        "slots": {
            "claim": ["I hacked your camera.", "I have your private photos.", "I recorded you.", "I know your password."],
            "demand": ["Pay {amount} in bitcoin.", "Send crypto to my wallet.", "Transfer the money within 48 hours.", "Pay me now."],
            "threat": ["Or I send the video to your contacts.", "Otherwise your family sees everything.", "Or I'll leak it to your colleagues.", "Don't contact the police."],
        },
    },

    # -------------------------------------------------------------- unseen
    "digital arrest": {
        "novelty": "unseen",
        "seeds": [
            "This is the cyber crime police. A parcel with illegal items was booked in your name. Stay on this video call, you are under digital arrest.",
            "Officer from the central investigation bureau speaking. Your ID is linked to money laundering. Do not disconnect the video call.",
            "Customs department: drugs were found in a courier under your name. Join the video call immediately for verification or face arrest.",
            "You are being monitored for a criminal case. Do not tell your family. Transfer your funds for verification and they will be returned.",
            "Narcotics bureau notice: your Aadhaar was used for a suspicious shipment. Remain on Skype with the officer until cleared.",
            "Court order issued against you. To avoid physical arrest, cooperate with the online interrogation and deposit the security amount.",
            "This call is from the police station. Your mobile number is involved in illegal activity. Keep your camera on and stay in the room.",
            "We are recording this verification. Move your savings to the government safety account so we can check they are legal.",
        ],
        "hinglish": [
            "Main CBI officer bol raha hoon, aapke naam pe illegal parcel mila hai. Video call band mat karna, aap digital arrest mein ho.",
            "Aapka Aadhaar money laundering case mein use hua hai. Kisi ko mat batana, verification ke liye paise transfer karo.",
        ],
        "manglish": [
            "Njan police officer aanu. Ningalude peril illegal parcel kittiyittundu. Video call cut cheyyaruthu, ningal digital arrest il aanu.",
        ],
        "templates": [
            "{agency}: {accusation} {order} {threat}",
            "{agency} speaking. {accusation} {order}",
        ],
        "slots": {
            "agency": ["Cyber crime police", "Central investigation bureau", "Customs enforcement", "Narcotics control bureau"],
            "accusation": ["A parcel with drugs was booked in your name.", "Your ID is linked to money laundering.", "Your number was used in a fraud case.", "A court warrant has been issued."],
            "order": ["Stay on the video call.", "Do not disconnect or tell anyone.", "Keep your camera on for verification.", "Transfer funds to the verification account."],
            "threat": ["Otherwise you will be arrested.", "Police will come to your home.", "Your accounts will be seized.", ""],
        },
    },
    "e-challan or traffic fine": {
        "novelty": "unseen",
        "seeds": [
            "Traffic police: an e-challan of {amount} is pending for your vehicle. Pay now to avoid court: {link}",
            "Your vehicle was caught speeding. Settle the fine within 24 hours or your licence will be suspended. {link}",
            "Parking penalty notice: pay {amount} today to avoid towing. {link}",
            "Unpaid traffic violation detected. Download the challan and pay online: {link}",
            "Dear vehicle owner, your challan is overdue. Late fee will apply after tonight. Pay via {link}",
            "Red light violation recorded at the junction. View photo and pay the penalty here {link}",
            "Final reminder: toll road fine unpaid. Clear it now or face legal action {link}",
            "Your number plate was flagged for a no-helmet violation. Pay the e-challan to avoid a warrant: {link}",
        ],
        "hinglish": [
            "Aapki gaadi ka {amount} ka challan pending hai. Abhi pay karein warna court case hoga: {link}",
        ],
        "manglish": [
            "Ningalude vandikku {amount} challan pending undu. Ippo thanne pay cheyyuka, illenkil court case aakum: {link}",
        ],
        "templates": [
            "{sender}: {violation} {fine} {link} {deadline}",
            "{violation} {fine} Pay at {link}",
        ],
        "slots": {
            "sender": ["Traffic police", "Road transport office", "Parking enforcement", "E-challan service"],
            "violation": ["Speeding recorded for your vehicle.", "Red light violation detected.", "Unpaid parking fine.", "No-helmet violation logged."],
            "fine": ["Fine: {amount}.", "Penalty of {amount} due.", "Pay {amount} to clear it."],
            "deadline": ["within 24 hours", "today", "to avoid licence suspension", ""],
        },
    },
    "QR code scam": {
        "novelty": "unseen",
        "seeds": [
            "Hi, I'm buying your sofa from the listing. I've sent a QR code, scan it to receive the {amount} payment.",
            "To get your refund, scan the attached QR and enter your PIN to accept the money.",
            "New parking payment system: scan the QR sticker on the meter to pay. Old method no longer works.",
            "EV charger notice: scan this code to start charging and save your card for future sessions.",
            "Congratulations, you've won cashback! Scan the QR code to claim {amount} instantly.",
            "I'm the buyer for your bike. Payment is ready, just scan my QR code and approve it on your app.",
            "Your electricity rebate is ready. Scan the QR in this message to receive it in your account.",
            "Restaurant review reward: scan this code and enter your UPI PIN to get your {amount} voucher.",
        ],
        "hinglish": [
            "Main aapka saman khareed raha hoon, maine QR bheja hai, scan karke PIN daalo, paisa aa jayega.",
        ],
        "manglish": [
            "Njan ningalude sofa vaangan ready aanu. QR ayachittundu, scan cheythu PIN adichaal paisa kittum.",
        ],
        "templates": [
            "{context} {scan} {receive}",
            "{context} {scan}",
        ],
        "slots": {
            "context": ["I'm buying your item from the listing.", "Your refund is approved.", "You won a cashback reward.", "New parking payment method:"],
            "scan": ["Scan the QR code I sent", "Scan this QR and enter your PIN", "Use the QR below and approve the request", "Scan the code to continue"],
            "receive": ["to receive {amount}.", "and the money comes to you.", "to claim it instantly.", ""],
        },
    },
    "task or like-and-earn scam": {
        "novelty": "unseen",
        "seeds": [
            "Hi! Want to earn {amount} a day? Just like YouTube videos and send screenshots. We pay instantly.",
            "Simple online tasks: rate hotels and get paid per review. Level up by topping up your task account.",
            "You completed today's tasks! To unlock the premium tier with higher commission, deposit {amount}.",
            "Part-time job: follow Instagram pages for us, 50 per follow. Join our Telegram to start.",
            "Your task account shows {amount} earnings. Pay the account upgrade fee to withdraw.",
            "Merchant tasks available: buy products in our app, get them refunded plus 20% commission.",
            "We need people to boost app ratings. Daily payment, no experience. Prepaid task bundles required for VIP level.",
            "Congratulations, you're a gold member! Complete 3 more combo tasks with a {amount} deposit to release your balance.",
        ],
        "hinglish": [
            "Ghar baithe kamao! Bas videos like karo aur screenshot bhejo, har task ke paise milenge. Telegram join karo.",
            "Aapke task account mein {amount} hai, withdraw karne ke liye pehle upgrade fee bharni hogi.",
        ],
        "manglish": [
            "Veetil irunnu paisa undaakkaam! Videos like cheythu screenshot ayachaal mathi, oro task inum paisa kittum.",
        ],
        "templates": [
            "{offer} {task} {catch}",
            "{offer} {task}",
        ],
        "slots": {
            "offer": ["Earn {amount} daily from home!", "Part-time online job available.", "Easy money, no experience needed.", "Join our task team."],
            "task": ["Just like videos and send screenshots.", "Rate hotels and get paid per review.", "Follow social media pages for us.", "Complete simple app tasks."],
            "catch": ["Top up {amount} to unlock higher tasks.", "Pay the upgrade fee to withdraw.", "Deposit to reach VIP level.", ""],
        },
    },
    "instant-loan app harassment": {
        "novelty": "unseen",
        "seeds": [
            "Your loan from QuickCash is overdue. Pay {amount} today or we will message everyone in your contacts that you are a fraud.",
            "Last warning: repay now or your morphed photos will be sent to your family and friends.",
            "We have your contact list and gallery. Clear the dues in 2 hours or we call your office.",
            "Pre-approved instant loan of {amount}! No documents. Install the app and allow contacts access: {link}",
            "You took a loan through our app. Interest has doubled. Pay the penalty now or face public shaming.",
            "Your relatives will be informed about your unpaid debt tonight. Pay immediately to stop this.",
            "Loan approved in 5 minutes! Just pay the processing charge of {amount} to receive the money.",
            "Recovery team here. If you don't pay today we will post your photo with 'defaulter' in all groups.",
        ],
        "hinglish": [
            "Aapka loan overdue hai. Aaj {amount} nahi bhara to aapke saare contacts ko message bhejenge ki aap fraud ho.",
            "Turant loan paayein, koi document nahi! App install karke contacts allow karein: {link}",
        ],
        "manglish": [
            "Ningalude loan overdue aanu. Innu {amount} adachillenkil ningalude contacts ellarkkum message ayakkum.",
        ],
        "templates": [
            "{who} {status} {threat}",
            "{offer} {catch}",
        ],
        "slots": {
            "who": ["Recovery team:", "Loan app notice:", "Final warning:", "Collections:"],
            "status": ["Your loan is overdue by 3 days.", "You owe {amount} with penalty.", "Repayment missed."],
            "threat": ["We will message all your contacts.", "Your photos will be shared with your family.", "We will call your office today.", "Pay now or face public shaming."],
            "offer": ["Instant loan of {amount} approved!", "Get cash in 5 minutes, no paperwork.", "Pre-approved personal loan for you."],
            "catch": ["Pay the processing fee first.", "Install the app and allow contact access: {link}", "Small verification charge required."],
        },
    },
    "UPI collect or accidental refund": {
        "novelty": "unseen",
        "seeds": [
            "Sorry, I sent {amount} to your UPI by mistake. Please accept the request I just sent to return it.",
            "Hi, I've sent you a collect request for your refund. Approve it with your PIN to receive the money.",
            "Wrong transfer! {amount} went to your account. Kindly send it back to this number, I'm a student.",
            "Your cashback of {amount} is pending. Accept the payment request in your app to credit it.",
            "Seller here, I'm paying for your listing via UPI. Just approve the request and enter your PIN.",
            "I accidentally paid you twice for the order. Please refund the extra by accepting the request.",
            "Bank notice: a reversal of {amount} is waiting. Approve the collect request within 10 minutes.",
            "Dear customer, to receive your insurance claim, approve the UPI request from our official handle.",
        ],
        "hinglish": [
            "Bhai galti se tumhare UPI pe {amount} chale gaye, maine request bheji hai, accept karke wapas kar do please.",
            "Aapka cashback pending hai, app mein request accept karo aur PIN daalo, paisa aa jayega.",
        ],
        "manglish": [
            "Sorry, njan abadhathil ningalude UPI ilekku {amount} ayachu. Request ayachittundu, accept cheythu thirichu tharaamo?",
        ],
        "templates": [
            "{mistake} {ask}",
            "{reason} {ask} {urgency}",
        ],
        "slots": {
            "mistake": ["I sent {amount} to you by mistake.", "Wrong UPI transfer, sorry!", "I paid you twice by accident."],
            "reason": ["Your cashback is ready.", "Your refund is approved.", "A reversal is pending."],
            "ask": ["Please accept the request I sent.", "Approve the collect request with your PIN.", "Kindly return it to this number.", "Enter your PIN to receive it."],
            "urgency": ["Within 10 minutes.", "Today please.", ""],
        },
    },
    "FASTag or toll balance": {
        "novelty": "unseen",
        "seeds": [
            "Your FASTag balance is low and will be blacklisted today. Recharge now: {link}",
            "FASTag KYC expired. Update details within 24 hours to avoid deactivation: {link}",
            "Toll payment failed for your vehicle. Pay the double penalty online to avoid a fine {link}",
            "Dear user, your tag has been suspended. Call {phone} to reactivate it.",
            "Annual toll pass offer: pay {amount} now and save 50%. Limited time: {link}",
            "Your vehicle crossed the toll without a valid tag. Clear dues of {amount} immediately: {link}",
            "FASTag alert: wallet blocked due to suspicious recharge. Verify your account here {link}",
            "Final notice: toll dues pending. Your number plate will be flagged at all plazas tomorrow.",
        ],
        "hinglish": [
            "Aapka FASTag block hone wala hai, KYC update karein abhi: {link}",
        ],
        "manglish": [
            "Ningalude FASTag block aakaan pokunnu, ippo KYC update cheyyuka: {link}",
        ],
        "templates": [
            "{alert} {issue} {action} {link}",
            "{issue} {action} {link}",
        ],
        "slots": {
            "alert": ["FASTag alert:", "Toll notice:", "Highway authority:"],
            "issue": ["Your tag balance is low.", "Your FASTag KYC has expired.", "Toll dues of {amount} are pending.", "Your tag is blacklisted."],
            "action": ["Recharge now", "Update details today", "Pay immediately", "Reactivate here"],
        },
    },
    "electricity disconnection": {
        "novelty": "unseen",
        "seeds": [
            "Dear consumer, your electricity will be disconnected tonight at 9:30 pm because last month's bill was not updated. Call {phone} immediately.",
            "Power supply notice: your connection will be cut today due to pending payment. Contact our officer now.",
            "Your electricity bill update is pending. Pay {amount} via {link} to avoid disconnection.",
            "URGENT: meter verification failed. Your power will be stopped in 2 hours. Call the electricity officer on {phone}.",
            "Last bill not received in our system. To avoid disconnection tonight, download the app and update your details.",
            "Electricity board: your account is flagged for overdue charges. Pay through the link {link} before 8pm.",
            "We tried to contact you about your energy account. Disconnection is scheduled this evening, respond now.",
            "Your smart meter subscription expired. Renew at {link} or supply will stop.",
        ],
        "hinglish": [
            "Priya upbhokta, aaj raat 9:30 baje aapki bijli kaat di jayegi kyunki pichla bill update nahi hua. Turant call karein {phone}.",
            "Bijli bill pending hai, {amount} abhi pay karo warna connection cut ho jayega: {link}",
        ],
        "manglish": [
            "Priya upabhokthave, innu raathri 9:30 nu ningalude current cut cheyyum, last bill update aayittilla. Udane vilikkuka {phone}.",
        ],
        "templates": [
            "{sender} {issue} {deadline} {action}",
            "{issue} {action} {deadline}",
        ],
        "slots": {
            "sender": ["Dear consumer,", "Electricity board:", "Power supply notice:", "Energy account alert:"],
            "issue": ["Your last bill is not updated.", "Payment of {amount} is overdue.", "Meter verification failed.", "Your account is flagged."],
            "deadline": ["Disconnection tonight at 9:30 pm.", "Supply stops in 2 hours.", "Power will be cut today.", ""],
            "action": ["Call {phone} immediately.", "Pay now: {link}", "Contact our officer.", "Update via {link}"],
        },
    },
    "KYC or ID update expiry": {
        "novelty": "unseen",
        "seeds": [
            "Dear customer, your KYC has expired. Your account will be blocked today. Update now: {link}",
            "Your PAN is not linked. Your account will be suspended within 24 hours. Complete verification {link}",
            "Aadhaar update required to continue banking services. Click {link} and enter your details.",
            "Your SIM will be deactivated in 24 hours due to incomplete KYC. Call {phone} to verify.",
            "Account frozen: KYC documents pending. Upload your ID and card details at {link}",
            "Wallet alert: complete re-KYC to avoid service interruption. Share the code you receive with our agent.",
            "Your bank account will be closed for non-compliance unless you verify your identity today {link}",
            "Final KYC reminder: update your details now or lose access to net banking.",
        ],
        "hinglish": [
            "Aapka KYC expire ho gaya hai, account aaj block ho jayega. Turant update karein: {link}",
            "PAN link nahi hai, 24 ghante mein account band ho jayega. Yahan verify karein {link}",
        ],
        "manglish": [
            "Ningalude KYC expire aayi, account innu block aakum. Udane update cheyyuka: {link}",
        ],
        "templates": [
            "{sender} {issue} {consequence} {action}",
            "{issue} {action} {consequence}",
        ],
        "slots": {
            "sender": ["Dear customer,", "Bank alert:", "Telecom notice:", "Wallet update:"],
            "issue": ["Your KYC has expired.", "Your PAN is not linked.", "Aadhaar verification pending.", "ID documents missing."],
            "consequence": ["Your account will be blocked today.", "Services stop in 24 hours.", "Your SIM will be deactivated.", ""],
            "action": ["Update now: {link}", "Verify at {link}", "Call {phone} to complete it.", "Upload details here {link}"],
        },
    },
    "fake customer-care helpline": {
        "novelty": "unseen",
        "seeds": [
            "Thanks for contacting support! For your refund, our executive will call you. Please keep your banking app open.",
            "Customer care: we saw your complaint online. Call our toll-free helpline {phone} to get your money back today.",
            "Hello, I'm from the official helpdesk. To process your return, download our support app and share the code.",
            "Your complaint is registered. Pay a {amount} service charge to escalate it to a senior team.",
            "This is the airline helpline regarding your cancelled flight. To issue the refund we need your card number and expiry.",
            "We found your review about the late delivery. Click {link} to claim compensation from our support team.",
            "Bank helpline: your card dispute needs verification. Please read me the code sent to your phone.",
            "Support ticket {code}: to receive the refund, approve the payment request we've sent to your app.",
        ],
        "hinglish": [
            "Customer care se bol raha hoon, aapka refund process karna hai, ek app install karke code bata dijiye.",
        ],
        "manglish": [
            "Customer care il ninnaanu. Ningalude refund process cheyyan oru app install cheythu code parayanam.",
        ],
        "templates": [
            "{who} {context} {ask}",
            "{context} {ask}",
        ],
        "slots": {
            "who": ["Customer care here.", "Official helpline:", "Support team:", "Refund desk:"],
            "context": ["We saw your complaint.", "Your refund is ready.", "Your ticket {code} is open.", "Your order was cancelled."],
            "ask": ["Call {phone} to claim it.", "Install our support app and share the code.", "Approve the payment request in your app.", "Share your card details to receive it."],
        },
    },
    "fake CAPTCHA or paste-command": {
        "novelty": "unseen",
        "seeds": [
            "Verify you are human: press Windows+R, paste the code we copied for you and press Enter.",
            "To view the shared document, complete the security check: open Run, press Ctrl+V and hit Enter.",
            "Browser update required. Copy the fix command below into PowerShell to continue.",
            "Your video can't play. Fix the error by pasting this line into your terminal: {link}",
            "Human verification step 2 of 3: paste the copied text into the Run box to confirm.",
            "Meeting link broken? Run the repair command we provide to join the call.",
            "Cloudflare-style check failed. Open the command window and paste the verification string.",
            "To download your invoice, prove you're not a robot by pasting the command into Windows Run.",
        ],
        "hinglish": [],
        "manglish": [],
        "templates": [
            "{why} {steps}",
            "{why} {steps} {urgency}",
        ],
        "slots": {
            "why": ["Verify you are human.", "Security check required.", "Document access blocked.", "Video error detected."],
            "steps": ["Press Windows+R, paste the code and press Enter.", "Open PowerShell and paste the fix command.", "Paste the copied text into the Run box.", "Run the repair command we provide."],
            "urgency": ["Then refresh the page.", "This takes 5 seconds.", ""],
        },
    },
    "deepfake CEO video call": {
        "novelty": "unseen",
        "seeds": [
            "Hi, it's the CEO. Join the video call in 5 minutes, the CFO and I need you to process a confidential transfer.",
            "Following our video meeting, please wire the acquisition payment today. Keep it strictly confidential.",
            "This is your director. The camera call was clear: send the funds to the new partner account before close of business.",
            "Urgent board decision on the call just now. Execute the payment of {amount} immediately, don't loop in finance.",
            "As discussed on video, I'm authorising an urgent transfer. Use the account I'm sending now.",
            "Hey, it's me from the call. Can you move {amount} to the vendor before the market opens? I'll sign off later.",
            "Our video meeting was recorded for compliance. Proceed with the secret transfer to the Hong Kong account.",
            "Confidential project: after today's call, transfer the deposit and tell no one until announced.",
        ],
        "hinglish": [
            "Main CEO bol raha hoon, abhi video call pe baat hui. Confidential payment turant transfer karo, finance ko mat batana.",
        ],
        "manglish": [],
        "templates": [
            "{who} {context} {ask} {secret}",
            "{context} {ask}",
        ],
        "slots": {
            "who": ["Hi, it's the CEO.", "This is your director.", "From the CFO:", "It's me from the call."],
            "context": ["As discussed on video,", "Following our camera meeting,", "The board agreed on the call just now:", "After today's video call,"],
            "ask": ["wire {amount} to the new partner account.", "process the confidential transfer today.", "send the acquisition payment now.", "move the funds before close of business."],
            "secret": ["Keep it confidential.", "Don't involve finance.", "Tell no one yet.", ""],
        },
    },
    "crypto airdrop or wallet drainer": {
        "novelty": "unseen",
        "seeds": [
            "You're eligible for the token airdrop! Connect your wallet at {link} to claim before it expires.",
            "Free NFT mint for early holders. Sign the transaction to receive yours: {link}",
            "Your wallet has unclaimed rewards worth {amount}. Approve the contract to collect them.",
            "Security alert: your wallet is compromised. Enter your recovery phrase here to secure your funds {link}",
            "Exclusive giveaway: send 0.1 ETH and get 1 ETH back, verified event.",
            "Claim your staking bonus now. Connect wallet and approve unlimited spending: {link}",
            "We're migrating to a new chain. Import your seed phrase in our app to keep your tokens.",
            "Congrats, you won the community lottery! Gas fee of {amount} required to release your prize.",
        ],
        "hinglish": [
            "Aapke wallet mein free tokens aaye hain, claim karne ke liye wallet connect karo: {link}",
        ],
        "manglish": [],
        "templates": [
            "{hook} {ask} {link}",
            "{hook} {ask}",
        ],
        "slots": {
            "hook": ["Airdrop live!", "You have unclaimed rewards.", "Free NFT for early holders.", "Wallet security alert:"],
            "ask": ["Connect your wallet to claim.", "Approve the contract to collect.", "Enter your recovery phrase to secure funds.", "Send a small gas fee to release it."],
        },
    },
    "student scholarship or exam scam": {
        "novelty": "unseen",
        "seeds": [
            "Congratulations! You've been selected for a national merit scholarship of {amount}. Pay the registration fee to receive it.",
            "Your exam result is withheld due to pending fees. Pay now at {link} to download your marksheet.",
            "Get the leaked question paper for tomorrow's exam. Pay {amount} via UPI and we'll send it.",
            "University admission confirmed! Secure your seat by paying the deposit today, limited seats.",
            "Your scholarship application is approved. Share your bank details and the OTP to credit funds.",
            "Exam re-evaluation service: guaranteed higher marks for a fee. Contact {phone}.",
            "Hostel allotment notice: pay {amount} within 24 hours or your room will be cancelled. {link}",
            "Foreign university scholarship: send the processing fee to start your visa application.",
        ],
        "hinglish": [
            "Badhai ho, aapko {amount} ki scholarship mili hai. Registration fee bharkar claim karein: {link}",
            "Kal ke exam ka paper chahiye? {amount} UPI karo, PDF bhej denge.",
        ],
        "manglish": [
            "Abhinandanangal, ningalkku {amount} scholarship kitti. Registration fee adachu claim cheyyuka: {link}",
        ],
        "templates": [
            "{hook} {ask} {link}",
            "{hook} {ask}",
        ],
        "slots": {
            "hook": ["You've won a merit scholarship!", "Your result is on hold.", "Admission confirmed!", "Scholarship approved."],
            "ask": ["Pay the registration fee to receive it.", "Pay pending fees to download your marksheet.", "Pay the seat deposit today.", "Send your bank details and OTP."],
        },
    },
    "rental or booking deposit": {
        "novelty": "unseen",
        "seeds": [
            "Hi, the flat is still available. I'm abroad so can't show it, but if you pay the deposit I'll courier the keys.",
            "Lots of interest in this room. Send a holding deposit of {amount} today to reserve it before viewings.",
            "Your holiday villa booking needs confirmation. Pay by bank transfer, not through the site, to get a discount.",
            "Hotel reservation issue: your card was declined. Re-enter payment details at {link} or lose the booking.",
            "I'm the landlord, I've moved for work. Transfer first month's rent and I'll send the contract.",
            "Your booking will be cancelled in 2 hours unless you verify payment through this link {link}",
            "Car rental confirmation: pay the security deposit via gift card to complete reservation.",
            "Cheap apartment, all bills included. Deposit secures it today, viewing not possible right now.",
        ],
        "hinglish": [
            "Flat available hai, main bahar hoon to dikha nahi sakta. Advance bhej do, chabi courier kar dunga.",
        ],
        "manglish": [
            "Flat available aanu, njan purathaanu, kaanikkan pattilla. Advance ayachaal key courier cheyyam.",
        ],
        "templates": [
            "{hook} {reason} {ask}",
            "{hook} {ask}",
        ],
        "slots": {
            "hook": ["The flat is still available.", "Your booking needs confirmation.", "Room available from next week.", "Holiday villa reserved for you."],
            "reason": ["I'm abroad so can't show it.", "There's high demand.", "Your card was declined.", "Viewing isn't possible right now."],
            "ask": ["Send the deposit to reserve it.", "Pay by bank transfer to confirm.", "Pay {amount} today to hold it.", "Verify payment at {link}"],
        },
    },
    "social-media verify or copyright strike": {
        "novelty": "unseen",
        "seeds": [
            "Your account has received a copyright strike and will be deleted in 24 hours. Appeal here: {link}",
            "Meta support: your page violates our policies. Verify your identity to avoid suspension {link}",
            "Congratulations, your account qualifies for the blue badge. Confirm your login at {link}",
            "We detected unusual login attempts. Confirm it's you by entering your password and code here {link}",
            "Your Instagram will be disabled for community violations. Fill the appeal form within 48 hours.",
            "Hi! A brand wants to collaborate with you. Log in through our partner portal to see the offer {link}",
            "Copyright notice: a video you posted infringes our rights. Download the evidence file and respond.",
            "Your account is under review. Send the 6-digit code we texted to keep your username.",
        ],
        "hinglish": [
            "Aapke Instagram account pe copyright strike aaya hai, 24 ghante mein delete ho jayega. Appeal karein: {link}",
        ],
        "manglish": [
            "Ningalude Instagram account il copyright strike vannu, 24 manikkoorinullil delete aakum. Appeal cheyyuka: {link}",
        ],
        "templates": [
            "{sender} {issue} {action} {link}",
            "{issue} {action} {link}",
        ],
        "slots": {
            "sender": ["Meta support:", "Copyright team:", "Account safety:", "Creator support:"],
            "issue": ["Your account got a copyright strike.", "Your page violates our policies.", "Unusual login detected.", "You qualify for verification."],
            "action": ["Appeal within 24 hours", "Verify your identity", "Confirm your login", "Submit the form"],
        },
    },
}
