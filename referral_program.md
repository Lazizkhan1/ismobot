I need you to create implementation plan referral system and discount system in this project.
Business logic:
1. The uesr use's /start command, then menu buttons opens with 3 buttons: 1-button) Order photo, 2-button) Invite Friends, 3-button) Contact to admin.
2. User presses the order photo button then the current order flow continues but at the payment part after verification video received add one more button with title "Invite friends" alongside "%N so'm". Update the payment text accordingly.
3. User presses the invite friends button then the menu buttons needs to be updated with 3 buttons:
    1) My Discounts,
    2) Invite Friends
    3) Back to main menu

Technical logic:

use aiogram deep link to send the referral link to the user.

1. The users table needs to be updated with a new column called "referrer_id" which is a foreign key to the users table.
2. Create a promotion table with the following columns:
    1) id bigint (primary key)
    2) title varchar(255)
    3) description text
    4) discount_amount decimal(10, 2)
    5) discrete boolean
    6) amount
    7) created_at timestamp

3. Create a new table called "referrals" with the following columns:
    1) id bigint (primary key)
    2) referrer_id bigint (foreign key to users table)
    3) new_customer_id bigint (foreign key to users table)
    4) discount_amount decimal(10, 2)

CREATE OR UPDATE OTHER REQUIRED TABLES TO COMPLETE THE FUNCTIONALITY OF THE REFERRAL AND DISCOUNT SYSTEM
UPDATE ALL TEXT, ADD EMOJIS, USE TEXT STYLING, REDUCE LONG TEXT INTO SHORTER VERSION BY KEEPING THE MEANING OF THE TEXT, AND MAKE IT MORE ENGAGING AND FUN.
CREATE PROJECT.md file to explain the project architecture, etc.

Answer for Q1: 
The initial referral reward is 20% of for 1 person, 50% of for 2 people, 100% of for 3 people. create that kind of discount if you cant adjust the flexibility of referral reward logic.

Answer for Q2: Discounts will be applied manually by the customer. Like this in below
default referrall reward needs to connected to promotions table. Update the promotion table name to "discounts". update the FAST_DELIVERY env variable to ORDER_PRICE and add discounts, total_amount, (total_amount=ORDER_PRICE-discounts) columns, 
update all orders' discount=0 , total_amount=ORDER_PRICE for all orders. 
Create order_discount table to store the referral discount amount.
Create discount_history table to store addition or removal of discount amount.
After OrderState.video_note_id received, before sending next message, check if user have discounts, if yes then add a use discount button to the message.
then next message will be "which discount do you want to use?" 2 buttons: "N so'm" and "-N% off".
then send the send the total amount after subracting the discount amount add button "Pay now: "total_amount so'm"".
after pay now button pressed: ask for the payment confirmation I mean update theOrderState to cheque_id. 
So user will have 2 variants of referral discount: 1-percentage discount and 2-discrete discount.
When the user referred customer bought a images, then the referrer will get a message like "Congratulations! 🎉 You've earned a discount of %N so'm or $N percenatge off on your next order!" with use discount button,
When that button is pressed, the fsm context will be checked that user hasn't uncompleted order, the user will be redirected to the main menu.
when user have uncompleted order(category_id not none, ceremony_date not none, video_note_id not none), the user will be redirected to pay now or use discount stage. 

lets say user referred 3 customers:
   The new UX flow:
   "Please choose a discount to use"
   | -- 1-button) "100% off"          |
   | -- 2-button) "20,000 so'm"          | 
ps: dont show the ether button if the user hasn't discount type percent or discrete yet.

if user get 4 people referred,
    100% off + 10,000 so'm for each person exeeded 3 customers.



