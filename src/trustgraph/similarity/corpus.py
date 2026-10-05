"""Reference messages the similarity signal compares against.

SCAM_SCRIPTS are paraphrases of widely reported scam patterns (UK Action
Fraud / US FTC style). LEGIT_MESSAGES are ordinary messages, deliberately
including ones that share scam vocabulary (invoices, bank notices, a family
emergency with no money ask, a new number with no ask), so that sounding
like "business" or "family" isn't enough to score high.

Everything here is hand-written stand-in data: a real deployment would load
reported scam messages and its own legit traffic instead.
"""

SCAM_SCRIPTS = {
    "bank safe-account scam": [
        "This is the fraud department at your bank. Your account has been compromised and you need to move your money to a safe account we have set up for you today.",
        "We have detected suspicious activity on your account. To protect your savings please transfer the full balance to the secure holding account I will give you now.",
        "Hello, calling from your bank's security team. Criminals have access to your account, so move your funds into this new protected account before they empty it.",
        "Your card has been cloned. For your protection we need you to transfer your savings to a temporary safe account while we investigate.",
        "This is the police working with your bank. A staff member there is corrupt, so do not speak to the branch; withdraw the cash and move it to the account we give you.",
    ],
    "gift-card request from a boss or colleague": [
        "Are you available? I need you to buy some gift cards for a client quickly. I'm in a meeting and can't talk, just send me the codes by email.",
        "I need a favour, please pick up six Apple gift cards of 100 each, scratch off the back and send me photos of the codes. I'll reimburse you later.",
        "Can you get Google Play cards for the staff reward today? Keep it confidential, it's a surprise. Send the card numbers to me directly.",
        "Quick task: purchase Amazon gift cards worth 500 and text me the redemption codes. Don't mention it to anyone else in the office.",
        "I'm stuck in a conference and need iTunes cards for a vendor, please buy them at the nearest shop and send me the numbers asap.",
    ],
    "invoice or bank-details change": [
        "Please note our bank details have changed. Kindly make this and all future payments to the new account below.",
        "Due to an audit our old account is on hold, please remit the outstanding invoice to our updated bank account instead.",
        "We have switched banks. Use the new sort code and account number attached for the payment due today, not the one on file.",
        "Our finance team has updated our payment details. Please update your records and pay invoice 4471 to the account in this email.",
        "Important: do not pay to the previous account. Our banking details have changed, the correct account details are below.",
    ],
    "family emergency or new-number scam": [
        "Hi Mum, this is my new number, I dropped my phone in the toilet. Can you help me pay a bill urgently, I can't log into my banking app.",
        "Grandma it's me, I'm in trouble. I was arrested and need money for bail, please don't tell Mum and Dad, send it to my lawyer's account.",
        "Hey Dad, lost my phone so using a friend's. I need to pay rent today or I'll be evicted, can you transfer it to this account and I'll pay you back.",
        "Mum it's me on a new number, save this one. I've got an urgent payment to make and my card isn't working, could you send it for me?",
        "I've had an accident abroad and the hospital won't treat me until I pay. Please send money to this account, and please don't tell anyone yet.",
    ],
    "tech support remote-access scam": [
        "This is Microsoft support. Your computer is sending us error messages and is infected. Please install AnyDesk so our technician can fix it.",
        "We detected a virus on your device. Download TeamViewer and give me the access code so I can remove it before your data is stolen.",
        "Your internet will be disconnected today because your router has been hacked. Let me connect remotely to your computer to secure it.",
        "Warning: your PC is blocked. Call this number immediately and allow our engineer screen sharing access to restore your files.",
        "To process your refund I need remote access to your computer. Log in to your online banking while I am connected so I can check it.",
    ],
    "tax or government threat": [
        "This is HMRC. You owe unpaid tax and a warrant has been issued for your arrest. Pay today to avoid legal action.",
        "Final notice from the IRS: a lawsuit has been filed against you. Call back immediately or the police will come to your address.",
        "Your National Insurance number has been suspended due to suspicious activity. Press 1 to speak to an officer and avoid arrest.",
        "The tax office has found an error in your return. You must pay the penalty now by bank transfer or face court proceedings.",
        "This is the immigration department. Your visa has an issue and you will be deported unless you pay the processing fee today.",
    ],
    "parcel or delivery fee": [
        "Your parcel is on hold due to an unpaid shipping fee of 1.99. Pay now via this link to reschedule delivery.",
        "Royal Mail: we missed you. A redelivery fee is required, please confirm your card details at the link below.",
        "Your package could not be delivered because of incomplete address information. Update your details and pay the customs charge here.",
        "DHL: customs duty is owed on your item. Pay within 24 hours or the parcel will be returned to sender.",
        "Your order is waiting at the depot. A small handling fee must be paid before we can release it, follow the link.",
    ],
    "investment or crypto scam": [
        "I made thousands with this crypto trading platform, my mentor guarantees 20 percent returns a week. Send bitcoin to this wallet to start.",
        "Exclusive investment opportunity with guaranteed returns. Deposit today and double your money within a month, limited places left.",
        "Your trading account has profits waiting but you must pay a withdrawal tax first before we can release your funds.",
        "Join our investment group, we use AI trading bots with no risk. Transfer USDT to the wallet address below to open your account.",
        "The coin is about to launch, get in now before the price explodes. Send your crypto to my wallet and I will buy it for you.",
    ],
    "romance scam money request": [
        "My love, I want to come and see you but I cannot afford the flight. Could you send me the money for the ticket and I will pay you back when I arrive.",
        "I am stuck overseas on the oil rig and my bank account is frozen. Please help me with some money, you are the only one I trust.",
        "Darling, customs are holding my package with the gold inside and I need to pay the release fee. Can you send it and we can finally be together.",
        "I have never felt this way about anyone. My daughter is in hospital and I need help with the bill, please send what you can by transfer.",
        "We will be married soon so what is mine is yours. I just need you to receive a payment into your account and send it on for me.",
    ],
    "one-time code or password request": [
        "We've sent a verification code to your phone, please read it back to me to confirm your identity.",
        "Hi, I accidentally sent my WhatsApp code to your number, could you forward me the six digit code please?",
        "To stop the fraudulent transaction I need the one-time passcode your bank just texted you.",
        "Please confirm your PIN and the code from your card reader so I can cancel the payment.",
        "Your account will be locked. Reply with the security code we sent and your password to keep it active.",
    ],
    "prize or lottery fee": [
        "Congratulations, you have won 50,000 in our international lottery. To claim your prize, pay the processing fee today.",
        "You have been selected for a cash prize. Send a small clearance fee and your bank details to receive the funds.",
        "Your email address won our annual draw. Contact our claims agent and pay the release fee to get your winnings.",
        "You're our lucky winner of a new iPhone, just pay the delivery charge at the link to claim it.",
        "Good news, an inheritance of 2 million is waiting for you. We need an administration fee to transfer the money.",
    ],
    "job or advance-fee scam": [
        "You've been hired for our remote job, but you need to pay for your training materials and equipment upfront, which we'll refund.",
        "Earn 300 a day working from home liking videos. Just pay a small deposit to unlock higher paying tasks.",
        "We'll send you a cheque to buy office equipment. Deposit it and transfer the leftover amount to our supplier.",
        "Congratulations on your new position. Please pay the background check fee before your start date.",
        "Our company needs a payment agent. Receive transfers into your account and send them on, keeping 10 percent commission.",
    ],
}

LEGIT_MESSAGES = [
    "Hi, just a reminder that invoice 4471 is due on Friday. Payment to the usual account as before, thanks.",
    "Please find attached our invoice for March. Let me know if you have any questions about the line items.",
    "Thanks for the payment, we've received it and your account is up to date.",
    "Our office will be closed on Monday for the bank holiday, we'll be back on Tuesday.",
    "Can we move our meeting to 3pm tomorrow? Something came up in the morning.",
    "The quote for the kitchen work is attached, it includes materials and labour.",
    "Your monthly statement is now available to view in online banking. We will never ask you for your PIN or passwords.",
    "We noticed a login from a new device. If this was you, no action is needed. If not, call the number on the back of your card.",
    "Your direct debit to the council has been set up successfully.",
    "Your parcel will be delivered tomorrow between 10am and 2pm. No action needed.",
    "Your order has been dispatched and should arrive within 3 working days.",
    "We tried to deliver your parcel today and left it with your neighbour at number 12.",
    "Hi Mum, I'm at the hospital with a sprained ankle, nothing serious. Can you pick me up at 6?",
    "Dad, can you call me when you're free? Nothing urgent, just want to talk about the weekend.",
    "Hey, it's Sam, this is my new number. Save it! See you at football on Saturday.",
    "Happy birthday! Hope you have a lovely day, we'll celebrate at the weekend.",
    "Don't forget the school trip money is due on Wednesday, it's paid through the parent app.",
    "Running 10 minutes late, stuck in traffic. Start without me.",
    "Can you send me the report by end of day? The client wants to review it tomorrow.",
    "I've shared the spreadsheet with you, please add your numbers in column C.",
    "Reminder: your dentist appointment is on Thursday at 9:30am. Reply C to confirm.",
    "Your prescription is ready to collect from the pharmacy.",
    "The plumber is coming at 8am, can you leave the side gate unlocked?",
    "Thanks for dinner last night, it was lovely to catch up.",
    "I bought a gift card for Sarah's leaving present, can you chip in 10 when you see me?",
    "Don't tell Jess about the surprise party on Saturday, she has no idea!",
    "The IT team will be updating laptops this weekend, please save your work and log off on Friday.",
    "Your tax return has been received and is being processed. You can check progress in your online account.",
    "Your energy bill for this quarter is ready. It will be collected by direct debit on the 15th.",
    "Hi, we've updated our privacy policy. No action is needed from you.",
    "Can you cover my shift on Sunday? I'll swap you for next week.",
    "The car is booked in for its MOT on Tuesday morning.",
    "Our team lunch is on Friday at 1pm, let me know if you have any dietary requirements.",
    "We're pleased to confirm your interview for Thursday at 11am at our office.",
    "Your subscription renews next month at the same price. You can manage it in your account settings.",
    "Payment of 250 to Northwind Supplies for invoice 882 has been sent from our usual account.",
    "Can you check whether the supplier sent the updated purchase order? I can't find it.",
    "Heads up, I'm working from home tomorrow, reach me on Teams.",
    "Grandad, thanks for the card and the money for my birthday, I'm going to spend it on football boots!",
    "Our annual audit starts next week, please make sure your expense receipts are uploaded.",
    "Your verification code is 604219. It expires in 10 minutes. Do not share it with anyone.",
    "Use code 3391 to sign in. If you didn't request this, ignore this message.",
    "Your bank will never ask you to move money to a safe account or share a one-time passcode.",
    "New phone, same me! This is Olu's new number, the old one is dead.",
]
