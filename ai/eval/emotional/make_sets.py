"""Write the two emotional-manipulation check sets (synthetic data, hand-written).

    python eval/emotional/make_sets.py

design.jsonl   used while designing rules (its misses are looked at).
holdout.jsonl  scored only before and after a change; never looked at while designing.

Neither file is ever used to train or to set cut-offs. Links use the reserved
.test domain and there are no real phone numbers or accounts.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (label, group, text). group = scam subtype or honest group.
DESIGN = [
    ("scam", "family emergency", "Mum it's Zoe, I crashed the car and the other driver wants £900 cash or he calls the police. Please send it to his account, I'll explain later, don't tell Dad."),
    ("scam", "family emergency", "Papa main hospital me hu, accident ho gaya. Doctor ko abhi 30,000 chahiye, unke UPI pe bhejo. Phone ki battery khatam ho rahi hai, call mat karna."),
    ("scam", "family emergency", "Grandma it's Liam, I'm in trouble, got arrested at a party. The lawyer says $1,800 for bail tonight. Please send it to him, and please don't tell Mom."),
    ("scam", "family emergency", "Dad, I'm stuck at the border, they took my wallet. I need $600 for the fine or they won't let me through. Send to my friend's Zelle, my bank app is locked."),
    ("scam", "family emergency", "Aunty, Rahul here. I had a fall at college and need stitches. The clinic wants 12,000 before treating me, please transfer to the receptionist's GPay quickly."),
    ("scam", "family emergency", "Mom please help, I hit a pedestrian and the police say if we pay the family 2 lakh now there will be no case. Send to the inspector's number, hurry."),
    ("scam", "new number money", "Hi Mum, new number, old phone smashed. Can you transfer £640 for my rent today? My banking app won't let me log in on this phone. Pay you back Friday x"),
    ("scam", "new number money", "Hey Dad it's me, this is my new number. I need to pay an urgent bill of $950 but my card is blocked. Can you send it to this account? Will explain tonight."),
    ("scam", "new number money", "Mummy ye mera naya number hai. Ek urgent payment karni hai 22,000 ki, account number bhej rahi hu, aaj hi kar do please, kal wapas."),
    ("scam", "new number money", "Hi it's your son, I'm texting from a friend's phone. Mine broke. Could you pay this invoice for me, £480? It's due today. Don't call, I'm at work."),
    ("scam", "romance money", "Darling, I've never felt this way. My card is frozen in Lagos and I can't pay the hotel. Please send $700 by gift card tonight, I'll repay when I land."),
    ("scam", "romance money", "Baby I'm so ashamed to ask, but the customs office is holding my bags with your gifts inside. They need $480 to release them. Please, I want to see you smile."),
    ("scam", "romance money", "My love, the ticket to come see you costs $1,350 and my salary comes next month. If you buy it now we can finally be together. Please don't break my heart."),
    ("scam", "romance money", "Jaan, mera account block ho gaya hai. 15,000 bhej do is account pe, kisi ko mat batana, hum milke sab theek kar denge."),
    ("scam", "bereavement", "Sorry for your loss. Your late father borrowed Rs 80,000 from me. I didn't want to disturb the family, but please clear it this week to my account so his soul rests in peace."),
    ("scam", "bereavement", "Our condolences. Your mother's insurance payout is ready but a release fee of $350 must be paid today or the claim closes. Reply to get the payment link."),
    ("scam", "sympathy donation", "Please help, my daughter needs urgent heart surgery tomorrow and we're short $2,000. I'm a single mother. Send anything to my CashApp, God bless you."),
    ("scam", "sympathy donation", "Mera beta ICU me hai, hospital 1.5 lakh maang raha hai. Insaniyat ke naate jitna ho sake is account pe bhej dijiye."),
    ("scam", "extortion threat", "I have your private chats and photos. Pay 25,000 by tonight or I send them to your family and your office group."),
    ("scam", "extortion threat", "I know where you live. Pay $1,500 or your children will pay for it. Don't involve the police, I'll know."),
    ("scam", "guilt pressure", "After everything I've done for you, you can't lend me 10,000? I'm in serious trouble. Send it to this UPI right now if you ever cared about me."),
    ("scam", "guilt pressure", "I'm going through hell and you're the only one I can turn to. Please send $250 to my cousin's account today, I'll never forget it."),
    ("scam", "kidnapping", "We have your son. Don't hang up, don't call anyone. Send 3 lakh to the account I'll text or you won't see him again."),
    ("scam", "loyalty test", "If you really love me you'll send me the code that just came to your phone. I need to know I can trust you."),
    ("scam", "religious pressure", "Guruji says your family has a curse that will harm your children. Pay Rs 9,100 for the special puja today to remove it."),
    ("honest", "family emergency", "Mum, small accident on the way home, the car's dented but I'm totally fine. Waiting for the insurance people. Call you in an hour."),
    ("honest", "family emergency", "Papa hospital me checkup ke liye aaye hain, sab normal hai. Reports shaam tak milenge."),
    ("honest", "family emergency", "Grandma, I'm home safe from the party. Thanks for worrying about me ❤️"),
    ("honest", "family emergency", "Dad, I lost my wallet at the station. Already blocked my cards and reported it. Can you bring my spare ID card tonight?"),
    ("honest", "family emergency", "Fell during football practice, got 3 stitches at the college clinic. All covered by the student insurance. I'm fine!"),
    ("honest", "family emergency", "Mom, the police stopped me for a broken tail light, just a warning. Getting it fixed tomorrow."),
    ("honest", "new number", "Hi Mum, new number, old phone smashed. Save this one. Coming home Saturday x"),
    ("honest", "new number", "Hey Dad, it's me on my work phone, mine's charging. Running late, home by 8."),
    ("honest", "new number", "Mummy ye mera naya number hai, save kar lo. Purana wala band ho gaya."),
    ("honest", "lending", "Can you lend me 2,000 till Friday? Salary's late. No worries if not!"),
    ("honest", "lending", "Thanks for covering lunch, I've sent you the 450 on GPay."),
    ("honest", "lending", "Dad, could you transfer my semester fees to the college account? The fee notice is on the student portal."),
    ("honest", "romance", "I miss you so much. Counting down the days till your flight lands ❤️"),
    ("honest", "romance", "Booked our tickets for the trip! I paid for the hotel, you get dinners 😄"),
    ("honest", "grief", "So sorry about your dad. He was a lovely man. The funeral is Friday at 11, family asked for donations to the hospice instead of flowers."),
    ("honest", "grief", "Mum's insurance paperwork is done, the agent said the claim takes about 4 weeks. No fees, it's all in the policy."),
    ("honest", "illness", "My daughter's surgery went well! Thank you everyone for your prayers and messages."),
    ("honest", "illness", "Beta ICU se general ward me shift ho gaya hai. Doctor ne kaha 3 din me discharge."),
    ("honest", "venting", "I'm going through a really tough time and you're the only one I can talk to. Can we call tonight?"),
    ("honest", "venting", "I feel like everyone is disappointed in me. Not in danger, just sad. Could use a hug."),
    ("honest", "worry", "Our son isn't answering his phone, have you heard from him? Probably just at practice."),
    ("honest", "love", "If you really love me you'll watch the last episode with me tonight 😂"),
    ("honest", "religious", "Guruji said the puja for Dadi's recovery is on Sunday at 9am, please come."),
    ("honest", "secrecy", "Don't tell Mom, but I'm planning a surprise party for her 50th! Can you help?"),
    ("honest", "work", "Sorry, I'm going through a hard week. Could I have till Monday for the report?"),
]

HOLDOUT = [
    ("scam", "family emergency", "Nana it's me, I'm at the police station, I was in a fight. I need $1,200 for a lawyer right now. Send it to his account, please don't tell my parents."),
    ("scam", "family emergency", "Mom I'm okay but I'm in the hospital after a crash. They won't treat me until $900 is paid. Send to the nurse's Venmo, I can't use my card."),
    ("scam", "family emergency", "Bhaiya, accident ho gaya highway pe. Doosri gaadi wala 40,000 maang raha hai warna police bulayega. Uske number pe GPay karo jaldi."),
    ("scam", "family emergency", "Uncle it's Priya, I'm stranded at the airport abroad, they lost my bag with my passport and money. Please send £400 to my friend's account so I can get a hotel."),
    ("scam", "family emergency", "Dad, I got into trouble at uni and there's a fine of $750 today or I'm expelled. Please pay to the office account I'll send, and don't tell Mum."),
    ("scam", "family emergency", "Grandpa, I'm in jail, please don't hang up. The officer says $2,000 bail by tonight. I'll put my lawyer on to explain how to pay."),
    ("scam", "family emergency", "Amma, en friend accident aayi, hospital il 25,000 adakkanam. Ee number il GPay cheyyu, vegam."),
    ("scam", "new number money", "Mum this is my new number, I dropped my phone. Can you pay a parcel fee for me, £3.50? Link: royal-parcels.example.test. Also need £500 for rent later x"),
    ("scam", "new number money", "Hey Mom, new phone who dis 😄 jk it's me. Can you send $820 for my car repair? Garage won't release it and my bank's locked on this phone."),
    ("scam", "new number money", "Papa ye naya number hai mera. Mujhe 35,000 ek friend ke account me bhejne hain urgent, mere account me problem hai. Abhi bhej do please."),
    ("scam", "new number money", "Hi Dad, using a mate's phone, mine got stolen. Could you transfer £600 to my flatmate? I owe him rent and he's threatening to kick me out."),
    ("scam", "romance money", "Sweetheart, I'm stuck at the airport in Dubai, immigration wants $900 or they'll deport me. You're the only one I trust. Please send it now."),
    ("scam", "romance money", "Honey I've sent you a parcel with jewellery and cash for our future. The courier needs $600 clearance fee, please pay it so it isn't returned."),
    ("scam", "romance money", "Baby, my mother is sick and the hospital won't wait. I hate asking, but could you send $1,100 tonight? I'll pay it back when my contract ends."),
    ("scam", "romance money", "Mere pyaar, mera visa reject ho jayega agar aaj 18,000 fee nahi bhari. Tum hi meri ummeed ho, please bhej do."),
    ("scam", "bereavement", "Condolences on your husband's death. He had a loan with us of $2,600. To stop it going to collections and affecting your family, pay today by card over the phone."),
    ("scam", "bereavement", "Sorry for your loss. I'm collecting for the funeral of our old classmate Arjun, his family can't afford it. Please send to my personal UPI, keep it quiet on the group."),
    ("scam", "sympathy donation", "My little boy needs a kidney transplant in 3 days. We've sold everything. Please donate to my PayPal, every dollar is a chance at life. Don't scroll past."),
    ("scam", "sympathy donation", "Ek gareeb maa ki madad kijiye, beti ka operation kal hai, 80,000 kam pad rahe hain. Is UPI pe jo ho sake bhejiye."),
    ("scam", "extortion threat", "I have screenshots of your messages to her. Pay $900 by tomorrow or your wife and your boss get everything."),
    ("scam", "extortion threat", "Your private video is with me. Send 40,000 or I share it with all your Instagram followers and your college."),
    ("scam", "extortion threat", "We are watching your house. Pay 2 lakh by Sunday or your family will suffer. Tell no one."),
    ("scam", "guilt pressure", "I always helped you when you needed it. Now I need 15,000 urgently and you're ignoring me? Send it to this account today, you owe me that much."),
    ("scam", "guilt pressure", "Please, I'm begging you, they will cut my electricity and my kids are cold. Send $200 to my neighbour's CashApp, I'll pay you back next week."),
    ("scam", "kidnapping", "Your daughter is with us. You heard her crying. Wire $5,000 in the next hour. If you call police, you'll regret it."),
    ("scam", "kidnapping", "Tumhara beta humare paas hai. 4 lakh tayyar rakho, kisi ko bataya toh achha nahi hoga. Account number bhej rahe hain."),
    ("scam", "loyalty test", "Babe, prove you trust me, tell me your bank PIN. Couples shouldn't have secrets."),
    ("scam", "religious pressure", "Your stars show a deadly danger to your husband this month. Pay Rs 11,000 for the protective havan today or the dosh will grow."),
    ("scam", "elder befriending", "Hello Auntie, I'm the boy from the temple. My mother is in hospital, I need 6,000 urgently. Please send to my number, you are like family to me."),
    ("scam", "self-harm pressure", "If you don't send me 5,000 tonight I don't know what I'll do to myself. You'll have to live with it."),
    ("honest", "family emergency", "Nana, I'm home from the station, the police just took my statement about the stolen bike. All okay."),
    ("honest", "family emergency", "Mom, I'm at the hospital with Sam, he twisted his ankle. Insurance card worked, we're waiting for the X-ray."),
    ("honest", "family emergency", "Bhaiya, gaadi ka chhota accident hua, bumper toota bas. Insurance claim kar diya hai."),
    ("honest", "family emergency", "Uncle, landed safely! Bag got delayed but the airline will deliver it to the hotel tomorrow."),
    ("honest", "family emergency", "Dad, got a parking fine on campus, $40. I'll pay it on the university website, sorry!"),
    ("honest", "family emergency", "Amma, friend nu cheriya accident, but okay aanu. Njan hospital il und, vaikunneram varam."),
    ("honest", "new number", "Mum this is my new number, I dropped my phone. Getting it fixed on Monday. Love you x"),
    ("honest", "new number", "Hey Mom, new phone! Same number though, just restored everything."),
    ("honest", "new number", "Papa ye naya number hai mera, office wala. Personal wala bhi chalu hai."),
    ("honest", "lending", "Hi Dad, could you send me some money for books this month? Happy to show you the receipts."),
    ("honest", "lending", "Sent you the 600 I owed for the concert, check your account."),
    ("honest", "lending", "Can I borrow 500 for the cab? Left my wallet at home, will pay back tonight."),
    ("honest", "romance", "Landed in Dubai! Hotel is amazing. Call you after dinner ❤️"),
    ("honest", "romance", "I sent you a little parcel, should arrive Thursday. Don't open it before your birthday!"),
    ("honest", "romance", "My mum's in hospital for a small procedure. I'll be with her today, talk tonight?"),
    ("honest", "grief", "Condolences on Raj's passing. The bank asked for the death certificate to close his account, I can come with you."),
    ("honest", "grief", "We're collecting for flowers for Arjun's funeral at the office, I'll take cash at my desk."),
    ("honest", "illness", "Little Aarav's transplant was a success! The hospital's charity page has updates, thank you for all the support."),
    ("honest", "illness", "Beti ka operation kal hai, dua kijiye. Insurance se sab cover ho gaya hai."),
    ("honest", "worry", "Haven't heard from your daughter since this morning, is she with you? Just checking."),
    ("honest", "venting", "I've been feeling so low lately. Don't worry, I've booked a therapist. Just wanted you to know."),
    ("honest", "venting", "I'm begging you, please stop sending me memes during work 😂"),
    ("honest", "religious", "The havan for Papa's health is on Sunday, 8am at home. Please come."),
    ("honest", "elder", "Auntie, I'll pick you up for the temple on Sunday. Mum says hi!"),
    ("honest", "secrecy", "Don't tell anyone yet, but we're pregnant!! 🥹"),
    ("honest", "secrecy", "Keep this between us, I'm applying for a new job. Wish me luck!"),
    ("honest", "work", "Client meeting moved to 4pm. Can you send me the deck before then?"),
    ("honest", "work", "Payroll will be a day late this month because of the bank holiday. Sorry everyone."),
    ("honest", "bank alert", "Rs 15,000 debited from your account to UPI/rentpay. If not done by you, call your bank's helpline on the back of your card."),
    ("honest", "otp", "Your OTP for the transfer is 482193. Never share it with anyone, including bank staff."),
]


def write(name, rows):
    path = HERE / name
    with open(path, "w", encoding="utf-8") as f:
        for i, (label, group, text) in enumerate(rows):
            f.write(json.dumps({"id": f"{name[:3]}{i:03d}", "text": text, "label": "scam" if label == "scam" else "legit",
                                "group": group, "synthetic": True}, ensure_ascii=False) + "\n")
    print(f"{path.name}: {sum(r[0] == 'scam' for r in rows)} scam, {sum(r[0] == 'honest' for r in rows)} honest")


if __name__ == "__main__":
    write("design.jsonl", DESIGN)
    write("holdout.jsonl", HOLDOUT)
