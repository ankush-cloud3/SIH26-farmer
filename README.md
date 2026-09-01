# SIH26-Farmer PS (project title)
# Farmer End - WhatsApp Bot

## Farmer Onboarding and Document Verification

1. **Document Submission:** The farmer sends identity and land documents (Aadhaar, land patta/ownership proof) directly via the WhatsApp bot.
2. **Database Registration:** The backend registers the submission, saves files to cloud storage, and assigns the status `PENDING_APPROVAL`.
3. **Immediate Acknowledgment:** The bot responds: *"Your documents are under review. You will receive a notification once verified."*
4. **Admin Alert:** The backend forwards the documents and details to the designated Admin WhatsApp group or number using Meta's interactive message templates.
5. **Admin Action:** The admin reviews the documents inside WhatsApp and clicks either `[Approve Listing]` or `[Reject / Re-upload]`.
6. **Status Update, Verified Badge & Notification:**
   * If **Approved**, status changes to `APPROVED`, assigns him a verified badge, and the bot notifies the farmer: *"Your account is verified! You can now list your produce."*
   * If **Rejected**, status changes to `REJECTED`, and the bot asks for corrections: *"Your document was blurry. Please re-upload your ID."*

---

## AI-Assisted Produce Listing

1. **Initial Trigger:** The verified farmer sends a photo of their crop or type the name along with a text snippet and quantity (e.g., photo of carrots + `"carat 50kg"`).
2. **Multilingual & Typo-Tolerant AI Parsing:**
   * The backend sends the image and text to the Gemini API.
   * Gemini detects the language, corrects typos (mapping `"carat"` to `"Carat"`), extracts the quantity (`50kg`), and returns structured JSON data. If ambiguous, the bot prompts with numbered suggestions (e.g., *"Did you mean Carrot or Garlic?"*).
3. **Conversational Completion:** The bot bypasses identification and asks only for missing details sequentially:
   * *"When will this be available for pickup?"*
   * *"Please share your exact pickup location or pin code."*
   * *"What is your expected price per kg?"*
4. **MSP & Mandi Price Check:**
   * When the price is entered, the backend cross-references it against the government Minimum Support Price (MSP) and nearby Mandi modal rates.
   * If the price is below MSP, the bot warns: *"Note: This is below the government MSP of ₹X/kg. Do you want to adjust or proceed?"*
5. **Confirmation Summary:** The bot presents a final summary (*"Product: Carrot, Qty: 50kg, Price: ₹30/kg, Location: [Area]"*) and asks the farmer to confirm.
6. **Auto-Publish:** Once confirmed, the listing status updates to live and automatically appears on the customer website sorted by proximity.

---

## Notable Features

1. **Interactive Listing Management (Get Status, Edit, Delete):** Farmers can manage their active listings directly through the bot using interactive options:
   * **Get Status:** Displays active listing specs (e.g., *Crop name: Ragi | Price: ₹40/kg | Quantity: 90kg*).
   * **Edit Listing:** Allows updating parameters like price, quantity, or availability.
   * **Delete Listing:** Instantly removes the listing from the live catalog.
2. **Unsold Produce Alert (Scheduled Backend Job):**
   * If a listing age exceeds $X$ days with no orders, an automated alert triggers.
   * Gemini suggests remedial actions: *Reduce price, expand buyer radius, or find a bulk buyer.*
3. **Digital Receipt Generation:** Generates a complete digital receipt containing all details including order ID, customer name, purchased quantity, final price, and itemized fees.
4. **On-Demand Money Flow Breakdown:** The detailed financial split (e.g., Buyer pays ₹1,500 $\rightarrow$ Farmer gets ₹1,370, Logistics gets ₹100, Platform gets ₹30) is hidden by default and shown only if explicitly asked or when a specific info button is pressed.
5. **Farmer Performance Dashboard:** AI aggregates orders, sales, and pricing data to generate performance insights: *"Your average realization increased by ₹3.20/kg."*
6. **Perishability Alert & Fair Pricing Check:**
   * To solve a major problem with perishable agricultural produce: farmers can lose money if crops remain unsold for too long. For example, a farmer harvests 100 kg of tomatoes. Tomatoes have a limited shelf life. If only 20 kg are sold and the remaining 80 kg sit unsold for several days, their quality starts declining. Eventually, the farmer may have to sell them at a very low price or throw them away. The system detects this before the produce becomes a serious loss and alerts the farmer.
   * The price is cross-referenced against the government MSP and local Mandi prices to ensure it complies with fair local rates and helps farmers **Know Your Real Market Price**.

---

# Customer End - Web Application

1. **Proximity-Based Discovery:** Customers log into the web application, enter their location or allow geolocation, and browse farm produce listed via the WhatsApp bot, dynamically sorted by distance using PostGIS coordinate calculations.
2. **Real-Time Inventory Validation & Checkout:** Customers select items and proceed to checkout; the system verifies live stock levels before directing them to complete payments via the Razorpay Sandbox gateway (triggering an "Out of Stock" notice if inventory is depleted).
3. **Automated Farmer Notification:** Upon successful payment verification (payment.captured webhook), the backend instantly dispatches an interactive WhatsApp notification to the respective farmer with order specs, buyer distance, and total payout.
