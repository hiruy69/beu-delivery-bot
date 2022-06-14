import logging
from typing import Dict
from decouple import config
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,InlineKeyboardMarkup, InlineKeyboardButton,KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from order import Order, Vendor, Food,User,Status, foods ,vendors as Vendors,orders as Orders

orders = []

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)




async def done(update: Update, context: ContextTypes.DEFAULT_TYPE,message=".") -> ReplyKeyboardMarkup:
    vendor = [ vendor for vendor in Vendors if vendor.chat_id  == update.effective_message.chat_id ]
    start_reply_keyboard = [
        ["View Foods", "Manage Orders" if vendor else KeyboardButton("Register As Vendor", request_contact=True,request_location=True )],
        ["Add Food"] if vendor else ["Done"], 
    ]
    start_markup = ReplyKeyboardMarkup(start_reply_keyboard, one_time_keyboard=True,request_contact=True)

    await update.message.reply_text(message,reply_markup=start_markup,)

    return start_markup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   
    start_markup = await done(update,context)
    await update.message.reply_text(
        f"Hi! {update.effective_user.full_name}. Welcome to Beu delivery bot. "
        ,
        reply_markup=start_markup,
    )


async def send_orders(update: Update,orders) -> None:
    for order in orders:
        food_detail = f"""
Order Id: {order.id}
Food Name: {order.food.name}
Quantity: {order.quantity}
User Name: {order.user.username}
User Phone: {order.user.phone}
Status: {order.status.name}
        """
        if order.status == Status.PENDING:
            button = [
                    [InlineKeyboardButton(f"Mark as Complete ✅", callback_data=f'complete_{order.id}'),InlineKeyboardButton("Cancel ❌", callback_data=f'cancel_{order.id}') ] 
                ]
            await update.message.reply_text(food_detail, reply_markup=InlineKeyboardMarkup(button))
        elif order.status == Status.INCOMING:
            button = [
                [InlineKeyboardButton(f"Accept", callback_data=f'order_{order.id}'),InlineKeyboardButton("Cancel", callback_data=f'cancel_{order.id}') ] 
            ]
            await update.message.reply_text(food_detail, reply_markup=InlineKeyboardMarkup(button))

        else:
            await update.message.reply_text(food_detail)


async def manage_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = update.message.text
    button = [
                ["View Incoming Orders", "View Pending Orders"],["View Completed Orders","View Cancelled Orders"] ,["Back"]
            ]
    if (action == "View Pending Orders"):
        orders = [ order for order in Orders if order.status == Status.PENDING and order.food.vendor.chat_id == update.effective_message.chat_id ]
        if orders :
            await send_orders(update,orders)
        else:
            await update.message.reply_text("No pending orders")
    elif (action == "View Incoming Orders"):
        orders = [ order for order in Orders if order.status == Status.INCOMING and order.food.vendor.chat_id == update.effective_message.chat_id ]
        if orders:
            await send_orders(update,orders)
        else :
            await update.message.reply_text("No incoming orders")
    elif (action == "View Completed Orders"):
        orders = [ order for order in Orders if order.status == Status.COMPLETED and order.food.vendor.chat_id == update.effective_message.chat_id ]
        if orders:
            await send_orders(update,orders)
        else :
            await update.message.reply_text("No completed orders")
    elif (action == "View Cancelled Orders"):
        orders = [ order for order in Orders if order.status == Status.CANCELLED  and order.food.vendor.chat_id == update.effective_message.chat_id ]
        if orders:
            await send_orders(update,orders)
        else :
            await update.message.reply_text("No cancelled orders")
    elif (action == "Manage Orders"):
        await update.message.reply_text(reply_markup= ReplyKeyboardMarkup(button, one_time_keyboard=True), text="Select an option")

    # return CHOOSING

async def view_foods(update: Update, context: ContextTypes.DEFAULT_TYPE,Foods) -> None:
    page_number = context.user_data["page_number"]
    for food in Foods:
        button = [
            [InlineKeyboardButton("Order", callback_data=f'food_id_{food.id}')]
            ]
        food_detail = f"""
Name: {food.name}
Price: {food.price}
Description: {food.description}
Vendor: {food.vendor.name}
        """
        await update.effective_message.reply_text(food_detail, reply_markup=InlineKeyboardMarkup(button))
    button = [
                [InlineKeyboardButton(f"<< Previous", callback_data=f'previous_'),InlineKeyboardButton("Next >>", callback_data=f'next_') ] 
            ]
    if Foods:
        await update.effective_message.reply_text(reply_markup= InlineKeyboardMarkup(button), text=f"Page {page_number}")


async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    context.user_data["choice"] = text
    if text == "View Foods":
        context.user_data["page"] = 3
        context.user_data["page_number"] = 1
    await view_foods(update,context,foods[:3])
    

async def register_vendor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id =  update.message.contact.user_id
    phone_number = update.message.contact.phone_number
    location = update.message.location
    full_name = update.message.from_user.full_name

    vendor = Vendor(name=full_name,phone=phone_number,address= location,chat_id=user_id)
    Vendors.append(vendor)

    await done(update,context,f"🎉🎉 {full_name} successfully registered 🎉🎉")
    


async def custom_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    context.user_data['food_id'] = update.callback_query.data.replace('food_id_', '')
    context.user_data['order_id'] = update.callback_query.data.replace('order_', '')

    food = [ food for food in foods if food.id == context.user_data['food_id'] ][0]
    user = User(username=update.effective_user.full_name, phone="09123456789",chat_id=update.effective_user.id)            
    order = Order(quantity=1, food=food, user=user)
    button = [
                [InlineKeyboardButton(f"Accept", callback_data=f'order_{order.id}'),InlineKeyboardButton("Cancel", callback_data=f'cancel_{order.id}') ] 
            ]
    order_detail = f"""
<< Incoming Order >>
Order Id: {order.id}
Food Name: {order.food.name}
Quantity: {order.quantity}
User Name: {order.user.username}
User Phone: {order.user.phone}
Status: {order.status.name}
        """
    await context.bot.send_message(chat_id=food.vendor.chat_id, text=order_detail , reply_markup=InlineKeyboardMarkup(button))
    Orders.insert(0,order)
    
    await update.effective_message.reply_text(f'🎉 Order Placed Successfully! 🎉')



async def update_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    order = update.callback_query.data.split('_')
    order_id = order[1]
    order_status = order[0]
    order_ =  [ order for order in Orders if order.id == str(order_id) ][0]
    if order_status == "order" and order_.status == Status.INCOMING:
        order_.status = Status.PENDING
        text = f"Order id: {order_.id} Accepted ✅"
        await context.bot.send_message(chat_id=order_.user.chat_id, text=f"{order_.user.username} your Order has been Accepted ✅" )
    elif order_status == "cancel" and order_.status != Status.COMPLETED:
        order_.status = Status.CANCELLED
        text = f"Order id: {order_.id}  Cancelled ❌"
        await context.bot.send_message(chat_id=order_.user.chat_id, text=f"Sorry {order_.user.username} your Order has been Cancelled ❌" )
    elif order_status == "complete" and order_.status != Status.CANCELLED:
        order_.status = Status.COMPLETED
        text = f"Order id: {order_.id} Completed ✅"
    else:
        text = f"Can't change this Order Status"
    await update.callback_query.answer()
    await update.effective_message.reply_text(f"{text}")


async def food_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    page = context.user_data.get("page") or 3
    page_number = context.user_data.get("page_number") or 1
    previous_page = update.callback_query.data.split('_')[0]
    context.user_data["page_number"] = page_number
    foods_ = foods[:3]

    if previous_page == "previous" and page_number > 1:
        foods_ = foods[page-6:page-3]
        context.user_data["page"] = page-3
        context.user_data["page_number"] = page_number-1
    elif previous_page == "next" :
        foods_ = foods[page:page+3]
        context.user_data["page"] = page+3
        context.user_data["page_number"] = page_number+1
    
    await view_foods(update,context,foods_)

async def add_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.reply_text("Enter Food Name")

    return CHOOSING

async def food_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.reply_text("Enter Food Price")
    context.user_data["food_name"] = update.message.text

    return TYPING_CHOICE

async def add_food_for_vendor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price = int(update.message.text)
    food_name = context.user_data.get("food_name")
    vendor = [ vendor for vendor in Vendors if vendor.chat_id == update.effective_user.id ][0]
    food = Food(name=food_name,price=price,vendor=vendor,stock=10,description="description")
    foods.insert(0,food)

    await update.effective_message.reply_text(f"Food {food_name} added successfully!!!")
    return ConversationHandler.END





def main() -> None:
    
    application = Application.builder().token(config("SERVER_BOT_TOKEN")).build()
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(Add Food|)$"), add_food)],
        states={
            CHOOSING: [
                MessageHandler( filters.TEXT & ~(filters.COMMAND | filters.Regex("^order_$")), food_price),
            ],
            TYPING_CHOICE: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^order_$")), add_food_for_vendor)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Back$"), done)],
    )


    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^(View Foods|Register As Vendor)$"), regular_choice))
    application.add_handler(MessageHandler(filters.Regex("^(Manage Orders|View Pending Orders|View Incoming Orders|View Completed Orders|View Cancelled Orders)$"), manage_orders))
    application.add_handler(MessageHandler( filters.CONTACT, register_vendor))
    application.add_handler(CallbackQueryHandler(custom_choice,pattern="^food_id_.*$"))
    application.add_handler(CallbackQueryHandler(update_orders,pattern="^complete_.*$|^cancel_.*$|^order_.*$"))
    application.add_handler(MessageHandler(filters.Regex("^(Back)$"), done))
    application.add_handler(CallbackQueryHandler(food_page,pattern="^previous_.*$|^next_.*$"))


    application.run_polling()


if __name__ == "__main__":
    main()
