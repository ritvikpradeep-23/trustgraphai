"""Reproducible TrustGraph-authored synthetic examples, NOT ScamShield data.

25 scam families x 7 social-engineering contexts x 4 concrete asks = 700
distinct message variants. Templates recur; this is not 700 independent fraud
mechanisms, real incidents or model-training/accuracy evidence. Emits JSON only.
"""
import argparse
import hashlib
import json
from collections import Counter

CONTEXTS = [
    "Please keep this conversation private; your family must not know.",
    "The standard support desk cannot help, so follow these instructions here.",
    "I am contacting you from a replacement number because the official channel is unavailable.",
    "Do not delay this request while you verify my identity.",
    "The app will not show this exception, so use the manual procedure I am providing.",
    "A colleague has authorized me to collect this from you directly.",
    "Treat this as a priority request and do not discuss it with anyone else.",
]

FAMILIES = [
    ("Bank safe-account transfer", "Your bank balance is exposed to a security breach and our emergency fraud team can protect it.", [
        "Move your savings to the safe account that I supply instead of contacting your branch.",
        "Transfer your full balance to my protected holding account for the investigation.",
        "Withdraw your money and deposit it into our temporary secure account before the hackers take it.",
        "Send the bank transfer to this new safe account and tell me the transaction verification code."]),
    ("OTP account takeover", "I am restoring access to your messaging account after a synchronization problem.", [
        "Forward the WhatsApp verification code that just arrived on your phone to me.",
        "Read me the six-digit login code so that I can finish the recovery on my computer.",
        "Reply with your OTP and password; this will prevent your account from being locked.",
        "Send a screenshot of the security code from your authenticator so I can sign in for you."]),
    ("Boss gift-card impersonation", "I am your manager and need a confidential purchase while I am away from the office.", [
        "Buy Apple gift cards and send me photos of the scratched redemption codes.",
        "Pick up Amazon gift cards and email the card numbers to my personal address.",
        "Purchase Google Play cards and forward the codes before contacting the finance team.",
        "Get Steam gift cards for our client and text me every redemption code immediately."]),
    ("Supplier invoice diversion", "We are the supplier handling your outstanding invoice and our payment account has changed.", [
        "Pay the invoice to my new bank account, not the account your company has on file.",
        "Remit today's balance to the updated account I sent in this chat without calling your usual contact.",
        "Cancel the scheduled transfer and send the funds to our replacement banking details.",
        "Use this alternate personal account for the invoice payment while our finance account is being audited."]),
    ("Family new-number emergency", "Mum, this is my replacement number. My phone broke and I cannot access my banking app.", [
        "Transfer the emergency bill money to my friend's account now and do not tell Dad.",
        "Send cash for my urgent rent to the account I provide without calling my old number.",
        "Pay my hospital deposit through this wallet because the doctor will not wait for verification.",
        "Move the money to my temporary account and keep it secret from the rest of the family."]),
    ("Remote tech-support theft", "This is the device security team. We detected malicious software and must repair your computer remotely.", [
        "Install AnyDesk, give me the access code and open your online banking while I am connected.",
        "Launch TeamViewer and share the session code so I can control your screen.",
        "Allow remote desktop access and tell me the password that unlocks your banking browser.",
        "Download our remote-access application and approve the screen-sharing request before calling official support."]),
    ("Tax arrest threat", "I am an investigator from the tax department and there is an arrest warrant linked to your unpaid tax.", [
        "Buy gift cards and send the redemption codes to settle the penalty before the officers arrive.",
        "Transfer the tax settlement to my personal bank account immediately to avoid arrest.",
        "Pay the penalty in bitcoin to the wallet address I provide; do not contact the police.",
        "Send the clearance payment through this private wallet instead of the official tax portal."]),
    ("Courier redelivery phishing", "Your parcel is held at our delivery depot because the address and delivery payment could not be verified.", [
        "Enter your card number, CVV and OTP at https://courier-fee.invalid to release the shipment.",
        "Pay the redelivery charge at https://parcel-release.invalid and type your bank password to confirm.",
        "Install the delivery update APK from https://courier-app.invalid and grant SMS access.",
        "Forward your bank verification code to our delivery agent so the shipping fee can be authorized."]),
    ("Crypto withdrawal fee", "Your investment account has earned a large profit, but the withdrawal is blocked until you complete our clearance.", [
        "Send USDT to my wallet address to pay the release fee before your profits can be withdrawn.",
        "Transfer bitcoin for the withdrawal tax; it must be paid outside the investment platform.",
        "Deposit an additional processing fee into this personal account to unlock your balance.",
        "Pay another security deposit through my crypto wallet before we release the original funds."]),
    ("Guaranteed trading investment", "Our private trading group guarantees profits without any chance of losing your capital.", [
        "Send bitcoin to my wallet address to activate your guaranteed-return trading account.",
        "Transfer your savings into this investment account today and we promise to double the balance.",
        "Buy USDT and forward it to our private wallet to join the risk-free trading scheme.",
        "Pay the membership fee directly to me rather than through a regulated investment platform."]),
    ("Romance emergency payment", "My love, I cannot leave my overseas work site and my bank account is frozen. Only you can help me come home.", [
        "Send the travel permit payment to my agent's personal account before calling anyone to check.",
        "Transfer the customs release fee for my valuable package so we can finally meet.",
        "Buy gift cards and send me their codes because my local bank cannot receive money.",
        "Pay my emergency hospital deposit through this crypto wallet and keep our relationship private."]),
    ("Lottery advance fee", "Your phone number has won a major cash prize in our international lottery draw.", [
        "Pay a processing fee to my account first and then we will release your winnings.",
        "Send the prize clearance charge in gift-card codes before claiming the reward.",
        "Transfer the insurance fee through this private wallet to receive the lottery payout.",
        "Provide your card PIN and OTP at https://prize-claim.invalid to activate the prize transfer."]),
    ("Job registration fee", "You have been selected for our remote position without an interview and your offer expires today.", [
        "Pay the mandatory joining fee to my personal account before receiving the offer letter.",
        "Buy the training kit through our private payment link; employment starts only after this deposit.",
        "Send a refundable background-check fee in crypto to secure your job slot.",
        "Transfer the registration charge now and do not contact the company's published recruitment address."]),
    ("Paid task withdrawal trap", "You earned commission from liking videos, but your task balance is frozen at the next level.", [
        "Deposit more money into our wallet to unlock the commission you already earned.",
        "Pay a VIP upgrade fee before you are allowed to withdraw your task earnings.",
        "Transfer a recovery deposit to finish the group task and release your frozen balance.",
        "Send another payment for the mistaken order; the earlier deposit cannot be refunded until then."]),
    ("Private-video extortion", "I hacked your webcam and have a private recording that I can send to your contacts.", [
        "Transfer bitcoin to my wallet address or I will publish the video to your family.",
        "Buy gift cards and send their codes before I email the recording to your colleagues.",
        "Pay my silence fee through this crypto wallet and do not contact the police.",
        "Send money to my account today or your intimate pictures will be posted publicly."]),
    ("Electricity disconnection fraud", "Your power connection will be disconnected tonight because our billing system says your payment is missing.", [
        "Install our bill-correction APK from https://power-update.invalid and grant SMS permissions.",
        "Send the payment to my personal UPI account, not the electricity company's payment portal.",
        "Give our officer your card PIN and OTP so he can reverse the disconnection order.",
        "Allow AnyDesk access to your phone while we update your bank payment record."]),
    ("Digital arrest impersonation", "This is the cyber police. A parcel in your name contains illegal items and you are under digital arrest.", [
        "Transfer your savings into our verification account while remaining on this private video call.",
        "Pay the investigation clearance fee in bitcoin and do not contact your local police station.",
        "Send a refundable custody bond to my personal account to prevent your immediate arrest.",
        "Tell me your banking password and OTP so we can prove that your funds are lawful."]),
    ("Traffic fine malware", "A traffic penalty has been issued against your vehicle and a court summons will follow if it remains unpaid.", [
        "Install the challan APK from https://traffic-notice.invalid and allow it to read all text messages.",
        "Pay the court settlement to the officer's private UPI account instead of the official portal.",
        "Enter your card PIN and OTP at https://fine-clearance.invalid to cancel the warrant.",
        "Send a bail deposit in gift-card codes to stop the vehicle seizure today."]),
    ("Fake bank KYC", "Your bank account will be suspended because the identity verification file has expired.", [
        "Send your bank password and OTP to our verification officer to keep the account active.",
        "Enter your card PIN at https://bank-kyc.invalid to confirm your identity immediately.",
        "Install our KYC-update APK and grant accessibility permissions so we can activate your account.",
        "Share your screen through TeamViewer and sign in to your banking app for the KYC check."]),
    ("UPI refund collection", "A refund is ready for you, but you must complete our special UPI verification before receiving it.", [
        "Approve my collect payment request and enter your UPI PIN to receive the refund.",
        "Scan the payment QR code and send a transfer first so the refund can be credited.",
        "Tell me your UPI PIN and banking OTP so I can manually release the money.",
        "Pay a refundable activation charge to my wallet before we send your cashback."]),
    ("Rental deposit impersonation", "The apartment is available at a special rate, but I cannot arrange a viewing before collecting a deposit.", [
        "Transfer the reservation deposit to my personal account before you verify ownership or see the property.",
        "Pay the key-release fee in gift cards and email me the redemption codes.",
        "Send a second insurance deposit through this crypto wallet to unlock the property viewing.",
        "Wire the holding payment to my overseas agent today; no signed rental agreement is needed."]),
    ("Marketplace buyer payment trick", "I am buying your item and my courier requires a payment-verification step before collecting it.", [
        "Enter your card PIN and OTP at https://buyer-courier.invalid to receive the sale proceeds.",
        "Approve my UPI collect request as the refund step; you must enter your PIN to get paid.",
        "Pay the courier insurance fee into my wallet first and I will reimburse it after pickup.",
        "Give me remote access to your phone so I can verify your seller payment account."]),
    ("Recovery agent advance fee", "I can recover the money you lost to a scam because I have special access to the fraudster's frozen wallet.", [
        "Send a recovery deposit in bitcoin to my wallet before I release your original money.",
        "Pay my clearance fee in gift-card codes and do not contact your bank about this recovery.",
        "Transfer the legal processing charge to my personal account before receiving any proof of recovery.",
        "Give me your wallet seed phrase and account password so I can recover the funds for you."]),
    ("Charity impersonation", "I represent an emergency relief charity and we must collect your contribution through an unofficial channel today.", [
        "Send the donation to my personal crypto wallet and do not ask the registered charity to verify me.",
        "Buy gift cards for relief supplies and send their redemption codes directly to my phone.",
        "Give me your card PIN and OTP so I can deduct the donation immediately.",
        "Install my remote-access app and open your banking screen so I can arrange the charitable transfer."]),
    ("Government subsidy phishing", "Your government subsidy has been approved, but it will expire unless you complete our private release procedure.", [
        "Pay the benefit release fee to my personal UPI account before receiving your subsidy.",
        "Enter your bank password and OTP at https://subsidy-release.invalid to activate the payment.",
        "Install the subsidy APK and allow it to read your SMS messages and control your phone.",
        "Transfer a refundable verification deposit in gift-card codes to unlock the benefit."]),
]


def build():
    rows = []
    for family_index, (title, premise, asks) in enumerate(FAMILIES, 1):
        for context_index, context in enumerate(CONTEXTS, 1):
            for ask_index, ask in enumerate(asks, 1):
                rows.append({"id": f"authored_v1_{family_index:02}_{context_index}_{ask_index}",
                             "title": title, "text": f"{premise} {context} {ask}",
                             "language": "English", "source_kind": "TrustGraph_authored_synthetic",
                             "family": family_index, "context_variant": context_index,
                             "ask_variant": ask_index})
    return rows


def provenance(rows):
    return {"source": "TrustGraph-authored synthetic demonstration variants",
            "count": len(rows), "families": len(FAMILIES),
            "contexts_per_family": len(CONTEXTS), "asks_per_family": 4,
            "categories": dict(Counter(row["title"] for row in rows)),
            "selection_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "limitations": "Template variants, not verified incidents or independent scam mechanisms. Not ScamShield-origin data, not model training and not an accuracy benchmark."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    rows = build()
    print(json.dumps(provenance(rows) if args.summary else rows, ensure_ascii=False))
