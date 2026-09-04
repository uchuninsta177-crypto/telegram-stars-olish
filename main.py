user_id = context.user_data["target_user"]
    add_balance(user_id, amount)
    balance = get_balance(user_id)
    
    await update.message.reply_text(
        f"✅ Balans qo'shildi!\n\n"
        f"👤 User ID: {user_id}\n"
        f"➕ Qo'shildi: {amount:,} so'm\n"
        f"💳 Yangi balans: {balance:,} so'm"
    )

    return ConversationHandler.END

async def remove_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END

    await query.message.reply_text("👤 User ID yuboring:")
    return WAIT_REMOVE_USER

async def receive_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["target_user"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat User ID (son) yuboring.")
        return WAIT_REMOVE_USER

    await update.message.reply_text("💰 Ayiriladigan summani yuboring:")
    return WAIT_REMOVE_AMOUNT

async def receive_remove_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat son kiriting.")
        return WAIT_REMOVE_AMOUNT

    user_id = context.user_data["target_user"]

    add_balance(user_id, -amount)
    balance = get_balance(user_id)

    await update.message.reply_text(
        f"✅ Balans ayirildi!\n\n"
        f"👤 User ID: {user_id}\n"
        f"➖ Ayirildi: {amount:,} so'm\n"
        f"💳 Yangi balans: {balance:,} so'm"
    )

    return ConversationHandler.END

if name == "main":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))

    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(add_balance_start, pattern="^add_balance$")],
            states={
                WAIT_ADD_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add_user)],
                WAIT_ADD_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add_amount)],
            },
            fallbacks=[],
        )
    )

    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(remove_balance_start, pattern="^remove_balance$")],
            states={
                WAIT_REMOVE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_user)],
                WAIT_REMOVE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_amount)],
            },
            fallbacks=[],
        )
    )

    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()
